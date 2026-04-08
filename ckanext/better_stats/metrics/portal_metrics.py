from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import func, select

import ckan.plugins.toolkit as tk
from ckan import model

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


class UserCountMetric(MetricBase):
    """Total registered users with a month-by-month registration trend."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CARD
    icon: ClassVar[str] = "fa-solid fa-users"

    def __init__(self) -> None:
        super().__init__(
            name="user_count",
            title=tk._("Registered Users"),
            description=tk._("Total number of registered users and registration trend"),
            order=7,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> int:
        return model.Session.query(model.User).filter(model.User.state == model.State.ACTIVE).count()

    def get_card_data(self) -> dict[str, Any]:
        return {"value": self.get_data(), "label": tk._("Registered Users")}

    def get_chart_data(self) -> dict[str, Any]:
        rows = (
            model.Session.query(
                func.date_trunc("month", model.User.created).label("month"),
                func.count(model.User.id).label("count"),
            )
            .filter(model.User.state == model.State.ACTIVE)
            .group_by("month")
            .order_by("month")
            .all()
        )
        return {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [row.month.strftime("%Y-%m") for row in rows]},
            "yAxis": {"type": "value", "minInterval": 1},
            "series": [{"type": "line", "data": [row.count for row in rows], "smooth": True}],
        }

    def get_table_data(self) -> dict[str, Any]:
        rows = (
            model.Session.query(
                func.date_trunc("month", model.User.created).label("month"),
                func.count(model.User.id).label("count"),
            )
            .filter(model.User.state == model.State.ACTIVE)
            .group_by("month")
            .order_by("month")
            .all()
        )
        return {
            "headers": [tk._("Month"), tk._("New Users")],
            "rows": [[row.month.strftime("%Y-%m"), row.count] for row in rows],
        }


class DatasetCompletenessMetric(MetricBase):
    """Percentage of datasets that have a description, at least one tag, and at least one resource."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.PROGRESS,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.PROGRESS
    icon: ClassVar[str] = "fa-solid fa-circle-check"

    def __init__(self) -> None:
        super().__init__(
            name="dataset_completeness",
            title=tk._("Dataset Completeness"),
            description=tk._("Percentage of datasets with description, tags, and resources"),
            order=8,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> dict[str, Any]:
        base = model.Session.query(model.Package).filter(
            model.Package.state == model.State.ACTIVE, model.Package.type == "dataset"
        )
        total = base.count()

        if total == 0:
            return {
                "total": 0,
                "with_description": 0,
                "with_tags": 0,
                "with_resources": 0,
            }

        with_description = base.filter(
            model.Package.notes.isnot(None),
            func.length(func.trim(model.Package.notes)) > 0,
        ).count()

        with_tags = base.filter(
            model.Package.id.in_(
                select(
                    model.Session.query(model.PackageTag.package_id)
                    .filter(model.PackageTag.state == model.State.ACTIVE)
                    .distinct()
                    .subquery()
                )
            )
        ).count()

        with_resources = base.filter(
            model.Package.id.in_(
                select(
                    model.Session.query(model.Resource.package_id)
                    .filter(model.Resource.state == model.State.ACTIVE)
                    .distinct()
                    .subquery()
                )
            )
        ).count()

        return {
            "total": total,
            "with_description": with_description,
            "with_tags": with_tags,
            "with_resources": with_resources,
        }

    def get_progress_data(self) -> dict[str, Any]:
        data = self.get_data()
        total = data["total"] or 1  # avoid division by zero
        return {
            "items": [
                {
                    "label": tk._("Have description"),
                    "value": round(data["with_description"] / total * 100, 1),
                    "max": 100,
                    "unit": "%",
                },
                {
                    "label": tk._("Have tags"),
                    "value": round(data["with_tags"] / total * 100, 1),
                    "max": 100,
                    "unit": "%",
                },
                {
                    "label": tk._("Have resources"),
                    "value": round(data["with_resources"] / total * 100, 1),
                    "max": 100,
                    "unit": "%",
                },
            ]
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        total = data["total"] or 1

        def pct(n: int) -> str:
            return f"{round(n / total * 100, 1)}%"

        return {
            "headers": [tk._("Criterion"), tk._("Datasets"), tk._("Coverage")],
            "rows": [
                [
                    tk._("Have description"),
                    data["with_description"],
                    pct(data["with_description"]),
                ],
                [tk._("Have tags"), data["with_tags"], pct(data["with_tags"])],
                [
                    tk._("Have resources"),
                    data["with_resources"],
                    pct(data["with_resources"]),
                ],
                [tk._("Total"), data["total"], "100%"],
            ],
        }
