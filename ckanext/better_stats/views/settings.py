import logging

from flask import Blueprint, Response, jsonify, make_response
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan import model

from ckanext.better_stats.metrics.base import MetricRegistry
from ckanext.better_stats.model import MetricConfig

log = logging.getLogger(__name__)
bp = Blueprint("better_stats_settings", __name__, url_prefix="/better_stats")


@bp.before_request
def before_request() -> None:
    try:
        tk.check_access("better_stats_view_settings", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Only sysadmins are allowed to manage settings"))


class BetterStatsSettingsView(MethodView):
    def get(self) -> str | Response:
        rows = []

        for metric in MetricRegistry.get_all_metrics():
            cfg = MetricConfig.for_metric(metric.name)
            rows.append(
                {
                    "name": metric.name,
                    "title": metric.title,
                    "icon": metric.icon,
                    "enabled": cfg.enabled if cfg else True,
                    "order": cfg.order if cfg else metric.order,
                    "col_span": cfg.col_span if cfg else metric.col_span,
                    "row_span": cfg.row_span if cfg else metric.row_span,
                    "access_level": (cfg.access_level or metric.access_level) if cfg else metric.access_level,
                    "cache_timeout": cfg.cache_timeout if cfg else metric.cache_timeout,
                }
            )

        rows.sort(key=lambda r: r["order"])

        return tk.render(
            "better_stats/settings.html",
            extra_vars={"rows": rows},
        )


def update_metric_config(metric_name: str) -> Response:
    """AJAX: update persisted config for one metric."""
    payload = tk.request.get_json(silent=True) or {}
    payload["metric_name"] = metric_name

    try:
        result = tk.get_action("better_stats_update_metric")({"user": tk.current_user.name}, payload)
    except tk.ObjectNotFound as e:
        return make_response(jsonify({"error": str(e)}), 404)
    except tk.ValidationError as e:
        return make_response(jsonify({"error": e.error_dict}), 400)

    return jsonify(result)


def batch_update_order() -> Response:
    """AJAX: update order for multiple metrics in one transaction."""
    MetricRegistry._ensure_loaded()
    payload = tk.request.get_json(silent=True) or []

    if not isinstance(payload, list):
        return make_response(jsonify({"error": "Expected a list"}), 400)

    errors = []
    for item in payload:
        name = item.get("metric_name")
        order = item.get("order")
        if name not in MetricRegistry.METRICS:
            errors.append(f"Unknown metric: {name}")
            continue
        if not isinstance(order, int):
            errors.append(f"Invalid order for {name}")
            continue
        cfg = MetricConfig.for_metric(name)
        if not cfg:
            cfg = MetricConfig(metric_name=name, order=order)
            model.Session.add(cfg)
        else:
            cfg.order = order

    if errors:
        model.Session.rollback()
        return make_response(jsonify({"error": errors}), 400)

    model.Session.commit()
    return jsonify({"updated": len(payload)})


def clear_all_caches() -> Response:
    """Clear cached data for every registered metric."""
    cleared: list[str] = []
    errors: list[str] = []

    for metric in MetricRegistry.get_all_metrics():
        metric.refresh_cache()
        cleared.append(metric.name)

    return jsonify({"cleared": cleared, "failed": errors})


def clear_metric_cache(metric_name: str) -> Response:
    """Clear cached data for a single metric."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric:
        return make_response(jsonify({"error": tk._("Metric not found")}), 404)

    metric.refresh_cache()

    return jsonify({"cleared": metric_name})


def reset_all_configs() -> Response:
    """Delete all persisted MetricConfig rows, reverting every metric to its defaults."""
    MetricConfig.clear_all()
    return jsonify({"reset": True})


bp.add_url_rule("/settings", view_func=BetterStatsSettingsView.as_view("settings"))
bp.add_url_rule("/settings/metric/<metric_name>", methods=["POST"], view_func=update_metric_config)
bp.add_url_rule("/settings/cache/clear", methods=["POST"], view_func=clear_all_caches)
bp.add_url_rule(
    "/settings/cache/clear/<metric_name>",
    methods=["POST"],
    view_func=clear_metric_cache,
)
bp.add_url_rule("/settings/batch-order", methods=["POST"], view_func=batch_update_order)
bp.add_url_rule("/settings/reset", methods=["POST"], view_func=reset_all_configs)
