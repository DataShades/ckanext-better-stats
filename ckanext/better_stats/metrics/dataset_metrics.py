from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase
from ckanext.better_stats.search import make_connection, solr_search

log = logging.getLogger(__name__)


class DatasetCountMetric(MetricBase):
    """Total number of active datasets in the system.

    A single numeric value — only card and table visualizations are meaningful.
    """

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.TABLE
    icon: ClassVar[str] = "fa-solid fa-database"
    supported_export_formats = ["csv", "xlsx"]
    scope: ClassVar[const.MetricScope] = const.MetricScope.USER

    def __init__(self) -> None:
        super().__init__(
            name="dataset_count",
            title=tk._("Total Datasets"),
            description=tk._("Total number of datasets in the system"),
            order=30,
        )

    def get_data(self) -> int:
        result = tk.get_action("package_search")(
            {"user": tk.current_user.name},
            {"rows": 0, "include_private": True},
        )
        return result["count"]

    def get_table_data(self) -> dict[str, Any]:
        return {
            "headers": [tk._("Metric"), tk._("Value")],
            "rows": [[tk._("Total Datasets"), self.get_data()]],
        }


class DatasetsByOrganizationMetric(MetricBase):
    """Distribution of datasets across organisations."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-building"
    scope: ClassVar[const.MetricScope] = const.MetricScope.USER

    def __init__(self) -> None:
        super().__init__(
            name="datasets_by_org",
            title=tk._("Datasets by Organization"),
            description=tk._("Distribution of datasets across organizations"),
            order=10,
            col_span=6,
        )

    def get_data(self) -> list[dict[str, Any]]:
        result = tk.get_action("package_search")(
            {"user": tk.current_user.name},
            {
                "rows": 0,
                "include_private": True,
                "facet.field": ["organization"],
                "facet.limit": -1,
            },
        )
        items = result.get("search_facets", {}).get("organization", {}).get("items", [])
        return sorted(
            [{"organization": item["display_name"], "count": item["count"]} for item in items],
            key=lambda x: x["count"],
            reverse=True,
        )

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [
                {
                    "type": "pie",
                    "radius": "60%",
                    "data": [{"name": item["organization"], "value": item["count"]} for item in data],
                }
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Organization"), tk._("Dataset Count")],
            "rows": [[item["organization"], item["count"]] for item in data],
        }


class DatasetCreationHistoryMetric(MetricBase):
    """Number of datasets created per day, in chronological order."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-calendar-days"
    scope: ClassVar[const.MetricScope] = const.MetricScope.USER

    def __init__(self) -> None:
        super().__init__(
            name="dataset_creation_history",
            title=tk._("Dataset Creation History"),
            description=tk._("Number of datasets created over time"),
            order=60,
            col_span=6,
        )

    def get_data(self) -> list[dict[str, Any]]:
        client = make_connection()

        oldest = solr_search(
            fq=["state:active", "type:dataset"],
            client=client,
            rows=1,
            sort="metadata_created asc",
            fl="metadata_created",
        )
        if not oldest.docs:
            return []

        raw = oldest.docs[0]["metadata_created"]
        earliest = raw.strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(raw, datetime) else str(raw)

        resp = solr_search(
            fq=["state:active", "type:dataset"],
            client=client,
            rows=0,
            facet="on",
            **{
                "facet.range": "metadata_created",
                "facet.range.start": earliest,
                "facet.range.end": "NOW+1DAY/DAY",
                "facet.range.gap": "+1DAY",
                "facet.range.other": "none",
            },
        )

        # SOLR returns counts as a flat list: [date, count, date, count, ...]
        counts = resp.facets["facet_ranges"]["metadata_created"]["counts"]
        return [
            {
                "day": datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d %B %Y"),
                "count": c,
            }
            for d, c in zip(counts[::2], counts[1::2], strict=True)
            if c > 0
        ]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [item["day"] for item in data]},
            "yAxis": {"type": "value", "minInterval": 1},
            "series": [
                {
                    "type": "line",
                    "data": [item["count"] for item in data],
                    "smooth": True,
                }
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Day"), tk._("Datasets Created")],
            "rows": [[item["day"], item["count"]] for item in data],
        }


class ResourcesByFormatMetric(MetricBase):
    """Distribution of resources across file formats."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-file-code"

    def __init__(self) -> None:
        super().__init__(
            name="resources_by_format",
            title=tk._("Resources by Format"),
            description=tk._("Distribution of resources across file formats"),
            order=50,
        )

    def get_data(self) -> list[dict[str, Any]]:
        result = tk.get_action("package_search")(
            {"ignore_auth": False},
            {
                "rows": 0,
                "facet.field": ["res_format"],
                "facet.limit": -1,
                "include_private": True,
            },
        )
        items = result.get("search_facets", {}).get("res_format", {}).get("items", [])

        aggregated: dict[str, int] = {}

        for item in items:
            key = item["name"].upper() if item["name"] else tk._("Unknown")
            aggregated[key] = aggregated.get(key, 0) + item["count"]

        return [
            {"format": fmt, "count": count}
            for fmt, count in sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
        ]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [
                {
                    "type": "pie",
                    "radius": "60%",
                    "data": [{"name": item["format"], "value": item["count"]} for item in data],
                }
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Format"), tk._("Resources")],
            "rows": [[item["format"], item["count"]] for item in data],
        }


class TopTagsMetric(MetricBase):
    """Most frequently used tags across all active datasets."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-tags"

    def __init__(self) -> None:
        super().__init__(
            name="top_tags",
            title=tk._("Top Tags"),
            description=tk._("Most frequently used tags across datasets"),
            order=40,
        )

    def get_data(self) -> list[dict[str, Any]]:
        result = tk.get_action("package_search")(
            {"ignore_auth": False},
            {
                "rows": 0,
                "facet.field": ["tags"],
                "facet.limit": 15,
                "include_private": True,
            },
        )
        items = result.get("search_facets", {}).get("tags", {}).get("items", [])
        return [{"tag": item["name"], "count": item["count"]} for item in items]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": 100, "right": 20, "top": 20, "bottom": 40},
            "xAxis": {"type": "value", "minInterval": 1, "name": tk._("Datasets")},
            "yAxis": {
                "type": "category",
                "data": [item["tag"] for item in data],
                "axisLabel": {"width": 100, "overflow": "truncate", "ellipsis": "..."},
            },
            "series": [
                {
                    "type": "bar",
                    "data": [item["count"] for item in data],
                    "colorBy": "data",
                }
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Tag"), tk._("Datasets")],
            "rows": [[item["tag"], item["count"]] for item in data],
        }


class DatasetsWithoutResourcesMetric(MetricBase):
    """Datasets that have no attached resources."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.TABLE
    icon: ClassVar[str] = "fa-solid fa-file-circle-xmark"

    def __init__(self) -> None:
        super().__init__(
            name="datasets_without_resources",
            title=tk._("Datasets Without Resources"),
            description=tk._("Datasets that have no attached resources"),
            order=110,
            access_level=const.AccessLevel.AUTHENTICATED.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        packages = []
        page_size = 1000
        start = 0

        while True:
            result = tk.get_action("package_search")(
                {"user": tk.current_user.name},
                {
                    "fq": "num_resources:0",
                    "fl": "name,title,dataset_type",
                    "rows": page_size,
                    "start": start,
                    "include_private": True,
                },
            )

            batch = result["results"]
            packages.extend(batch)

            if start + len(batch) >= result["count"]:
                break

            start += page_size

        return [
            {
                "name": pkg["name"],
                "title": pkg["title"] or pkg["name"],
                "url": f"/{pkg['dataset_type']}/{pkg['name']}",
            }
            for pkg in packages
        ]

    def get_card_data(self) -> dict[str, Any]:
        return {
            "value": len(self.get_data()),
            "label": tk._("Datasets Without Resources"),
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Dataset"), tk._("URL")],
            "rows": [
                [
                    item["title"],
                    {"text": item["title"], "url": item["url"]},
                ]
                for item in data
            ],
        }

    def get_export_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Dataset"), tk._("URL")],
            "rows": [[item["title"], item["url"]] for item in data],
        }


class StaleDatasetsMetric(MetricBase):
    """Datasets that have not been updated in over a year."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.TABLE
    icon: ClassVar[str] = "fa-solid fa-hourglass-end"

    def __init__(self) -> None:
        super().__init__(
            name="stale_datasets",
            title=tk._("Stale Datasets"),
            description=tk._("Datasets not updated in over a year"),
            order=120,
            access_level=const.AccessLevel.AUTHENTICATED.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        year_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)
        packages = []
        page_size = 1000
        start = 0

        while True:
            result = tk.get_action("package_search")(
                {"user": tk.current_user.name},
                {
                    "fq": f"metadata_modified:[* TO {year_ago.strftime('%Y-%m-%dT%H:%M:%SZ')}]",
                    "fl": "name,title,dataset_type,metadata_modified",
                    "rows": page_size,
                    "start": start,
                    "sort": "metadata_modified asc",
                    "include_private": True,
                },
            )

            batch = result["results"]
            packages.extend(batch)

            if start + len(batch) >= result["count"]:
                break

            start += page_size

        return [
            {
                "name": pkg["name"],
                "title": pkg["title"] or pkg["name"],
                "last_updated": datetime.fromisoformat(pkg["metadata_modified"]).strftime("%d %B %Y"),
                "url": f"/{pkg['dataset_type']}/{pkg['name']}",
            }
            for pkg in packages
        ]

    def get_card_data(self) -> dict[str, Any]:
        return {"value": len(self.get_data()), "label": tk._("Stale Datasets")}

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Dataset"), tk._("Last Updated")],
            "rows": [[{"text": item["title"], "url": item["url"]}, item["last_updated"]] for item in data],
        }

    def get_export_data(self) -> dict[str, Any]:
        return self.get_table_data()
