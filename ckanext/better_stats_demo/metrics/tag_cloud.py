"""DEMO ``tag_cloud`` metric + visualization for the ``better_stats_demo`` plugin.

A second brand-new visualization type (after ``map``): a word cloud where each
tag's size scales with its count — the bigger the number, the bigger the word.
The client renderer lives in ``assets/ts/bstats-tag-cloud.ts``; the backend just
ships ``{tags: [{text, count}], palette}`` via the conventional
``get_tag_cloud_data`` method.

Data is a fixed list of plausible tags with seeded counts, so the demo never
touches the database.
"""

from __future__ import annotations

import random
from typing import Any, ClassVar

import ckan.plugins.toolkit as tk

from ckanext.better_stats_demo.metrics.const import GROUP

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase, MetricRegistry
from ckanext.better_stats.visualization import Visualization, VisualizationRegistry

TAG_CLOUD_VIZ = "tag_cloud"


class TagCloudMetric(MetricBase):
    """DEMO: most-used tags drawn as a word cloud, sized by frequency."""

    supported_visualizations: ClassVar[list[const.VisualizationType | str]] = [
        TAG_CLOUD_VIZ,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType | str] = TAG_CLOUD_VIZ
    icon: ClassVar[str] = "fa-solid fa-tags"
    supported_export_formats: ClassVar[list[str]] = ["csv", "json", "xlsx"]
    scope: ClassVar[const.MetricScope] = const.MetricScope.GLOBAL
    group = GROUP

    # Accent colours cycled through by the renderer. Chosen to read on both the
    # light and dark dashboard themes.
    _PALETTE: ClassVar[list[str]] = [
        "#2563eb",
        "#16a34a",
        "#f97316",
        "#db2777",
        "#7c3aed",
        "#0891b2",
        "#ca8a04",
    ]

    # Plausible CKAN-ish tags; counts are seeded so the cloud is stable across
    # renders and agrees with the table.
    _TAGS: ClassVar[list[str]] = [
        "open-data",
        "geospatial",
        "transport",
        "environment",
        "health",
        "education",
        "economy",
        "energy",
        "agriculture",
        "population",
        "climate",
        "budget",
        "elections",
        "tourism",
        "housing",
        "water",
        "biodiversity",
        "employment",
        "crime",
        "weather",
        "census",
        "infrastructure",
        "research",
        "statistics",
    ]
    _SEED: ClassVar[int] = 21

    def __init__(self) -> None:
        super().__init__(
            name="popular_tags",
            title=tk._("Popular Tags"),
            description=tk._("Demo: most-used tags drawn as a word cloud"),
            order=40,
            col_span=6,
            row_span=2,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        """Return ``[{text, count, url}]`` sorted most-used first.

        ``url`` points at CKAN's dataset search filtered by the tag (e.g.
        ``/dataset/?tags=open-data``), so the cloud behaves like real tag links.
        """
        rng = random.Random(self._SEED)  # noqa: S311
        tags = [
            {
                "text": text,
                "count": rng.randint(3, 240),
                "url": tk.url_for("dataset.search", tags=text),
            }
            for text in self._TAGS
        ]
        tags.sort(key=lambda t: t["count"], reverse=True)
        return tags

    def get_tag_cloud_data(self) -> dict[str, Any]:
        """Payload consumed by the ``tag_cloud`` client renderer."""
        return {"tags": self.get_data(), "palette": self._PALETTE}

    def get_table_data(self) -> dict[str, Any]:
        return {
            "headers": [tk._("Tag"), tk._("Datasets")],
            "rows": [[t["text"], t["count"]] for t in self.get_data()],
        }


def register_visualizations() -> None:
    """Register the demo ``tag_cloud`` visualization type."""
    VisualizationRegistry.register(
        Visualization(TAG_CLOUD_VIZ, tk._("Tag Cloud"), "fa fa-tags"),
    )


def register_metrics() -> None:
    """Register the demo tag-cloud metric."""
    MetricRegistry.register("popular_tags", TagCloudMetric)
