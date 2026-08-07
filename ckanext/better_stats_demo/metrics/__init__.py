"""DEMO metrics package for the ``better_stats_demo`` plugin.

Each submodule owns one visualization type plus the metrics that use it:

* :mod:`.map`       — the data-driven ``map`` viz (3 metrics)
* :mod:`.tag_cloud` — the ``tag_cloud`` word-cloud viz (1 metric)

``register_metrics`` / ``register_visualizations`` fan out to every submodule;
the plugin wires them to the ``better_stats:register_*`` signals. Add a new demo
viz by dropping in a module and listing it here.
"""

from __future__ import annotations

from ckanext.better_stats_demo.metrics import map as map_metrics
from ckanext.better_stats_demo.metrics import tag_cloud as tag_cloud_metrics

_MODULES = (map_metrics, tag_cloud_metrics)


def register_metrics() -> None:
    """Register every demo metric."""
    for module in _MODULES:
        module.register_metrics()


def register_visualizations() -> None:
    """Register every demo visualization type."""
    for module in _MODULES:
        module.register_visualizations()
