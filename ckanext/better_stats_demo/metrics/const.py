from __future__ import annotations

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const

GROUP = const.MetricGroup(
    name="demo",
    label=tk._("Demo"),
    icon="fa-solid fa-chart-bar",
)
