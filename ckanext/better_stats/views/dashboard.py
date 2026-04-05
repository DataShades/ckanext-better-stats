import csv
import io
import json
import logging
from datetime import UTC, datetime

from flask import Blueprint, Response, jsonify, make_response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import (
    MetricBase,
    MetricRegistry,
    before_metric_render_signal,
)

log = logging.getLogger(__name__)
bp = Blueprint("better_stats", __name__, url_prefix="/better_stats")


class BetterStatsDashboardView(MethodView):
    def get(self) -> str | Response:
        try:
            tk.check_access("better_stats_view_dashboard", {"user": tk.current_user.name})
        except tk.NotAuthorized:
            tk.abort(403, tk._("You must be logged in to visit this page"))

        metrics = MetricRegistry.get_enabled_metrics()

        accessible_metrics = [metric for metric in metrics if tk.h.check_user_can_access_metric(metric)]

        return tk.render(
            "better_stats/dashboard.html",
            extra_vars={"accessible_metrics": accessible_metrics},
        )


@bp.route("/metric/<metric_name>")
def get_metric_data(metric_name: str) -> Response:
    """Return visualization data for a single metric."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric or not tk.h.check_user_can_access_metric(metric):
        return make_response(jsonify({"error": "Metric not found or not accessible"}), 404)

    requested = tk.request.args.get("type", metric.default_visualization.value)
    refresh = tk.asbool(tk.request.args.get("refresh", False))

    try:
        viz_type = const.VisualizationType(requested)
    except ValueError:
        viz_type = metric.default_visualization

    # Fall back to the metric's default when the requested type is unsupported.
    if not metric.supports_visualization(viz_type):
        viz_type = metric.default_visualization

    if refresh:
        metric.refresh_cache()

    try:
        data = metric.get_viz_data(viz_type)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    for _, result in before_metric_render_signal.send(
        None, context={"metric": metric, "viz_type": viz_type.value, "data": data}
    ):
        if result is not None:
            data = result
            break

    return jsonify(
        {
            "name": metric.name,
            "title": metric.title,
            "description": metric.description,
            "data": data,
            "type": viz_type.value,
            "supported_visualizations": [v.value for v in metric.supported_visualizations],
            "default_visualization": metric.default_visualization.value,
            "supported_export_formats": list(metric.supported_export_formats),
        }
    )


@bp.route("/embed/<metric_name>")
def embed_metric(metric_name: str) -> Response:
    """Return a self-contained HTML page for embedding in an iframe."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric or not tk.h.check_user_can_access_metric(metric):
        tk.abort(404)

    viz_type = tk.request.args.get("viz", metric.default_visualization.value)

    resp = make_response(
        tk.render(
            "better_stats/embed.html",
            {
                "metric": metric,
                "viz_type": viz_type,
                "metric_api_url": tk.url_for(
                    "better_stats.get_metric_data",
                    metric_name=metric_name,
                    _external=True,
                ),
            },
        )
    )

    # Allow the page to be framed from any origin (operators can restrict
    # this via a reverse-proxy CSP header if needed).
    resp.headers["X-Frame-Options"] = "ALLOWALL"
    resp.headers["Content-Security-Policy"] = "frame-ancestors *"

    return resp


@bp.route("/export/<metric_name>")
def export_metric(metric_name: str) -> Response:
    """Export metric data."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric:
        return make_response(jsonify({"error": tk._("Metric not found")}), 404)

    try:
        tk.check_access(
            "better_stats_export_metric",
            {"user": tk.current_user.name},
            {"metric": metric},
        )
    except tk.NotAuthorized:
        return make_response(jsonify({"error": tk._("Export not available")}), 403)

    if not metric.can_export():
        return make_response(jsonify({"error": tk._("Export not available")}), 403)

    format_type = tk.request.args.get("format", const.ExportFormat.CSV.value)

    if format_type not in metric.supported_export_formats:
        return make_response(jsonify({"error": tk._("Unsupported format")}), 400)

    return MetricExporter(metric, f"{metric_name}_{datetime.now(UTC).isoformat()}", format_type).export_metric()


class MetricExporter:
    def __init__(self, metric: MetricBase, filename: str, format_type: str) -> None:
        self.metric = metric
        self.filename = filename
        self.format_type = format_type
        self.data = metric.get_export_data()

    def export_metric(self) -> Response:
        if self.format_type == const.ExportFormat.CSV.value:
            return self._export_as_csv()
        if self.format_type == const.ExportFormat.JSON.value:
            return self._export_as_json()
        return make_response(jsonify({"error": tk._("Unsupported format")}), 400)

    def _export_as_csv(self) -> Response:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.data.get("headers", []))
        writer.writerows(self.data.get("rows", []))

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = f"attachment; filename={self.filename}.csv"

        return response

    def _export_as_json(self) -> Response:
        envelope = {
            "metric": self.metric.name,
            "title": self.metric.title,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "site_url": tk.config.get("ckan.site_url", ""),
            "data": self.data,
        }
        response = make_response(json.dumps(envelope, indent=2))
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = f"attachment; filename={self.filename}.json"

        return response


bp.add_url_rule("/dashboard", view_func=BetterStatsDashboardView.as_view("dashboard"))
bp.add_url_rule("/embed/<metric_name>", view_func=embed_metric)
bp.add_url_rule("/export/<metric_name>", view_func=export_metric)
