from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import func

import ckan.model as model
import ckan.plugins.toolkit as tk

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
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.TABLE
    )
    icon: ClassVar[str] = "bi-database"
    color: ClassVar[str] = "#0d6efd"

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
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.CHART
    )
    icon: ClassVar[str] = "bi-building"
    color: ClassVar[str] = "#0d6efd"

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
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.CHART
    )
    icon: ClassVar[str] = "bi-calendar-range"
    color: ClassVar[str] = "#0d6efd"

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
        return [
            {"day": row.day.strftime("%Y-%m-%d"), "count": row.count}
            for row in rows
        ]

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
