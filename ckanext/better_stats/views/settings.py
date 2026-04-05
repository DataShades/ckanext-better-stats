import logging

from flask import Blueprint, Response, jsonify, make_response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import (
    MetricRegistry,
)
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
                    "grid_size": cfg.grid_size if cfg else metric.grid_size,
                    "access_level": cfg.access_level if cfg else metric.access_level,
                    "cache_timeout": cfg.cache_timeout if cfg else metric.cache_timeout,
                }
            )

        rows.sort(key=lambda r: r["order"])

        return tk.render(
            "better_stats/settings.html",
            extra_vars={"rows": rows},
        )


def update_metric_config(metric_name: str) -> Response:  # noqa: PLR0912, C901
    """AJAX: update persisted config for one metric."""
    metric = MetricRegistry.get_metric(metric_name)

    if not metric:
        return make_response(jsonify({"error": tk._("Metric not found")}), 404)

    payload = tk.request.get_json(silent=True) or {}

    updates: dict = {}
    errors: list[str] = []

    if "enabled" in payload:
        val = payload["enabled"]
        if not isinstance(val, bool):
            errors.append("'enabled' must be a boolean")
        else:
            updates["enabled"] = val

    if "order" in payload:
        val = payload["order"]
        if not isinstance(val, int):
            errors.append("'order' must be an integer")
        else:
            updates["order"] = val

    if "grid_size" in payload:
        val = payload["grid_size"]
        if val not in [e.value for e in const.GridSize]:
            errors.append(f"'grid_size' must be one of {sorted([e.value for e in const.GridSize])}")
        else:
            updates["grid_size"] = val

    if "access_level" in payload:
        val = payload["access_level"]
        if val not in [e.value for e in const.AccessLevel]:
            errors.append(f"'access_level' must be one of {sorted([e.value for e in const.AccessLevel])}")
        else:
            updates["access_level"] = val

    if "cache_timeout" in payload:
        val = payload["cache_timeout"]
        if not isinstance(val, int) or val < 0:
            errors.append("'cache_timeout' must be a non-negative integer")
        else:
            updates["cache_timeout"] = val

    if errors:
        return make_response(jsonify({"error": errors}), 400)

    if not updates:
        return make_response(jsonify({"error": tk._("No valid fields provided")}), 400)

    cfg = MetricConfig.upsert(metric_name, **updates)

    return jsonify(
        {
            "metric": metric_name,
            "enabled": cfg.enabled,
            "order": cfg.order,
            "grid_size": cfg.grid_size,
            "access_level": cfg.access_level,
            "cache_timeout": cfg.cache_timeout,
        }
    )


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
bp.add_url_rule("/settings/reset", methods=["POST"], view_func=reset_all_configs)
