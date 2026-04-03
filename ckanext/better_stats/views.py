import logging
import json
import csv
import io

from flask import Blueprint, Response, jsonify, make_response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricRegistry, before_metric_render_signal


log = logging.getLogger(__name__)
bp = Blueprint("better_stats", __name__, url_prefix="/better_stats")


class BetterStatsDashboardView(MethodView):
    def get(self) -> str | Response:
        tk.check_access("better_stats_view_dashboard", {"user": tk.current_user.name})

        metrics = MetricRegistry.get_enabled_metrics()

        accessible_metrics = []

        for metric in metrics:
            if tk.h.check_user_can_access_metric(metric):
                accessible_metrics.append(metric)

        return tk.render(
            "better_stats/dashboard.html",
            extra_vars={"accessible_metrics": accessible_metrics},
        )


class BetterStatsSettingsView(MethodView):
    def get(self) -> str | Response:
        tk.check_access("better_stats_view_settings", {})
        return tk.render("better_stats/settings.html", extra_vars={})


@bp.route("/metric/<metric_name>")
def get_metric_data(metric_name: str) -> Response:
    """Return visualization data for a single metric."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric or not tk.h.check_user_can_access_metric(metric):
        return make_response(
            jsonify({"error": "Metric not found or not accessible"}), 404
        )

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

    for _, result in before_metric_render_signal.send(None, context={"metric": metric, "viz_type": viz_type.value, "data": data}):
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
            "supported_visualizations": [
                v.value for v in metric.supported_visualizations
            ],
            "default_visualization": metric.default_visualization.value,
        }
    )


@bp.route("/embed/<metric_name>")
def embed_metric(metric_name: str) -> Response:
    """Return a self-contained HTML page for embedding in an iframe."""
    metric = MetricRegistry.get_metric(metric_name)

    print(metric)

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
    """Export metric data"""

    metric = MetricRegistry.get_metric(metric_name)

    if not metric:
        return make_response(jsonify({"error": tk._("Metric not found")}), 404)

    if not tk.h.check_user_can_access_metric(metric) or not metric.can_export():
        return make_response(jsonify({"error": tk._("Export not available")}), 403)

    format_type = tk.request.args.get("format", "csv")
    data = metric.get_export_data()

    if format_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(data["headers"])
        writer.writerows(data["rows"])

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = (
            f"attachment; filename={metric_name}.csv"
        )
    elif format_type == "json":
        response = make_response(json.dumps(data, indent=2))
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = (
            f"attachment; filename={metric_name}.json"
        )
    else:
        return make_response(
            jsonify({"error": tk._("Unsupported format")}), 400
        )

    return response


bp.add_url_rule("/dashboard", view_func=BetterStatsDashboardView.as_view("dashboard"))
bp.add_url_rule("/settings", view_func=BetterStatsSettingsView.as_view("settings"))
bp.add_url_rule("/embed/<metric_name>", view_func=embed_metric)
bp.add_url_rule("/export/<metric_name>", view_func=export_metric)
