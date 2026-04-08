from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from sqlalchemy import func, select

import ckan.plugins.toolkit as tk
from ckan import model

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


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
    supported_export_formats = ["csv"]

    def __init__(self) -> None:
        super().__init__(
            name="dataset_count",
            title=tk._("Total Datasets"),
            description=tk._("Total number of datasets in the system"),
            order=1,
        )

    def get_data(self) -> int:
        return (
            model.Session.query(model.Package)
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
            )
            .count()
        )

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

    def __init__(self) -> None:
        super().__init__(
            name="datasets_by_org",
            title=tk._("Datasets by Organization"),
            description=tk._("Distribution of datasets across organizations"),
            order=2,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                model.Group.title,
                func.count(model.Package.id).label("count"),
            )
            .join(model.Member, model.Group.id == model.Member.group_id)
            .join(model.Package, model.Member.table_id == model.Package.id)
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
                model.Group.type == "organization",
                model.Member.table_name == "package",
            )
            .group_by(model.Group.title)
            .all()
        )
        return [{"organization": row.title, "count": row.count} for row in rows]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "type": "pie",
            "labels": [item["organization"] for item in data],
            "data": [item["count"] for item in data],
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

    def __init__(self) -> None:
        super().__init__(
            name="dataset_creation_history",
            title=tk._("Dataset Creation History"),
            description=tk._("Number of datasets created over time"),
            order=3,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                func.date_trunc("day", model.Package.metadata_created).label("day"),
                func.count(model.Package.id).label("count"),
            )
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
            )
            .group_by("day")
            .order_by("day")
            .all()
        )
        return [{"day": row.day.strftime("%Y-%m-%d"), "count": row.count} for row in rows]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "type": "line",
            "labels": [item["day"] for item in data],
            "data": [item["count"] for item in data],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Day"), tk._("Datasets Created")],
            "rows": [[item["day"], item["count"]] for item in data],
        }


class ResourcesByFormatMetric(MetricBase):
    """Distribution of resources across file formats (top 10)."""

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
            order=4,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                func.coalesce(func.nullif(func.upper(model.Resource.format), ""), "Unknown").label("format"),
                func.count(model.Resource.id).label("count"),
            )
            .filter(model.Resource.state == "active")
            .group_by("format")
            .order_by(func.count(model.Resource.id).desc())
            .limit(10)
            .all()
        )
        return [{"format": row.format, "count": row.count} for row in rows]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "type": "pie",
            "labels": [item["format"] for item in data],
            "data": [item["count"] for item in data],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Format"), tk._("Resources")],
            "rows": [[item["format"], item["count"]] for item in data],
        }


class TopTagsMetric(MetricBase):
    """Most frequently used tags across all active datasets (top 15)."""

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
            order=5,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                model.Tag.name,
                func.count(model.PackageTag.package_id).label("count"),
            )
            .join(model.PackageTag, model.Tag.id == model.PackageTag.tag_id)
            .join(model.Package, model.PackageTag.package_id == model.Package.id)
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
                model.PackageTag.state == "active",
            )
            .group_by(model.Tag.name)
            .order_by(func.count(model.PackageTag.package_id).desc())
            .limit(15)
            .all()
        )
        return [{"tag": row.name, "count": row.count} for row in rows]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "type": "bar",
            "labels": [item["tag"] for item in data],
            "data": [item["count"] for item in data],
            "options": {
                "indexAxis": "y",
                "plugins": {"legend": {"display": False}},
                "scales": {
                    "x": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": tk._("Datasets")},
                    },
                },
            },
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
            order=6,
            grid_size="full",
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(model.Package.name, model.Package.title)
            .filter(
                model.Package.state == model.State.ACTIVE,
                model.Package.type == "dataset",
                ~model.Package.id.in_(
                    select(
                        model.Session.query(model.Resource.package_id)
                        .filter(model.Resource.state == model.State.ACTIVE)
                        .subquery()
                    )
                ),
            )
            .order_by(model.Package.title)
            .all()
        )

        return [
            {
                "name": row.name,
                "title": row.title or row.name,
                "url": tk.url_for("dataset.read", id=row.name, _external=False),
            }
            for row in rows
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
                    {"text": item["url"], "url": item["url"]},
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
            order=7,
            grid_size="full",
        )

    def _cutoff(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                model.Package.name,
                model.Package.title,
                model.Package.metadata_modified,
            )
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
                model.Package.metadata_modified < self._cutoff(),
            )
            .order_by(model.Package.metadata_modified.asc())
            .all()
        )
        return [
            {
                "name": row.name,
                "title": row.title or row.name,
                "last_updated": row.metadata_modified.strftime("%Y-%m-%d"),
            }
            for row in rows
        ]

    def get_card_data(self) -> dict[str, Any]:
        return {"value": len(self.get_data()), "label": tk._("Stale Datasets")}

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Dataset"), tk._("Last Updated")],
            "rows": [[item["title"], item["last_updated"]] for item in data],
        }

    def get_export_data(self) -> dict[str, Any]:
        return self.get_table_data()
