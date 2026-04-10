from __future__ import annotations

import logging
from typing import Any

from ckan import types
from ckan.logic import validate
from ckan.plugins import toolkit as tk

from ckanext.better_stats.logic import schema
from ckanext.better_stats.metrics.base import MetricRegistry
from ckanext.better_stats.model import MetricConfig

log = logging.getLogger(__name__)

_UPDATABLE_FIELDS = ("enabled", "order", "grid_size", "access_level", "cache_timeout")


@validate(schema.better_stats_update_metric)
def better_stats_update_metric(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("better_stats_update_metric", context, data_dict)

    metric_name = data_dict["metric_name"]

    if metric_name not in MetricRegistry.METRICS:
        raise tk.ObjectNotFound(tk._("Metric not found: {}").format(metric_name))

    updates = {k: data_dict[k] for k in _UPDATABLE_FIELDS if k in data_dict}

    if not updates:
        raise tk.ValidationError({"": [tk._("No valid fields provided")]})

    cfg = MetricConfig.upsert(metric_name, **updates)

    return {
        "metric": metric_name,
        "enabled": cfg.enabled,
        "order": cfg.order,
        "grid_size": cfg.grid_size,
        "access_level": cfg.access_level,
        "cache_timeout": cfg.cache_timeout,
    }
