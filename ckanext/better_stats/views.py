import logging
import json
import csv
import io

from flask import Blueprint, Response, jsonify, make_response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.better_stats.metrics.base import MetricRegistry


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
def get_metric_data(metric_name) -> Response:
    """Get data for specific metric"""
    registry = MetricRegistry()
    metric = registry.get_metric(metric_name)

    if not metric or not tk.h.check_user_can_access_metric(metric):
        return make_response(
            jsonify({"error": "Metric not found or not accessible"}), 404
        )

    viz_type = tk.request.args.get("type", "chart")
    refresh = tk.request.args.get("refresh", False)

    if refresh:
        metric.refresh_cache()

    try:
        if viz_type == "chart":
            data = metric.get_chart_data()
        elif viz_type == "table":
            data = metric.get_table_data()
        elif viz_type == "card":
            data = metric.get_card_data()
        else:
            data = metric.get_data()
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    return jsonify(
        {
            "name": metric.name,
            "title": metric.title,
            "description": metric.description,
            "data": data,
            "type": viz_type,
        }
    )


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

    try:
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

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

    return response


bp.add_url_rule("/dashboard", view_func=BetterStatsDashboardView.as_view("dashboard"))
bp.add_url_rule("/settings", view_func=BetterStatsSettingsView.as_view("settings"))
bp.add_url_rule("/export/<metric_name>", view_func=export_metric)
