from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import func, select

import ckan.plugins.toolkit as tk
from ckan import model

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


class OrganizationCountMetric(MetricBase):
    """Total number of active organizations with a monthly creation trend."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CARD
    icon: ClassVar[str] = "fa-solid fa-sitemap"

    def __init__(self) -> None:
        super().__init__(
            name="organization_count",
            title=tk._("Organizations"),
            description=tk._("Total number of organizations and their creation trend"),
            order=9,
        )

    def get_data(self) -> int:
        return (
            model.Session.query(model.Group)
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
            )
            .count()
        )

    def get_card_data(self) -> dict[str, Any]:
        return {"value": self.get_data(), "label": tk._("Organizations")}

    def get_chart_data(self) -> dict[str, Any]:
        rows = (
            model.Session.query(
                func.date_trunc("month", model.Group.created).label("month"),
                func.count(model.Group.id).label("count"),
            )
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
            )
            .group_by("month")
            .order_by("month")
            .all()
        )
        return {
            "type": "line",
            "labels": [row.month.strftime("%Y-%m") for row in rows],
            "data": [row.count for row in rows],
            "options": {
                "plugins": {"legend": {"display": False}},
                "scales": {"y": {"beginAtZero": True, "ticks": {"stepSize": 1}}},
            },
        }

    def get_table_data(self) -> dict[str, Any]:
        rows = (
            model.Session.query(model.Group.title, model.Group.created)
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
            )
            .order_by(model.Group.created.desc())
            .all()
        )
        return {
            "headers": [tk._("Organization"), tk._("Created")],
            "rows": [
                [
                    row.title or row[0],
                    row.created.strftime("%Y-%m-%d") if row.created else "—",
                ]
                for row in rows
            ],
        }


class OrganizationMembershipMetric(MetricBase):
    """Number of members per organization, revealing engagement and staffing levels."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-user-group"

    def __init__(self) -> None:
        super().__init__(
            name="organization_membership",
            title=tk._("Organization Membership"),
            description=tk._("Number of members per organization"),
            order=10,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rows = (
            model.Session.query(
                model.Group.title,
                func.count(model.Member.id).label("members"),
            )
            .join(model.Member, model.Group.id == model.Member.group_id)
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
                model.Member.table_name == "user",
                model.Member.state == model.State.ACTIVE,
            )
            .group_by(model.Group.id, model.Group.title)
            .order_by(func.count(model.Member.id).desc())
            .limit(15)
            .all()
        )
        return [{"organization": row.title, "members": row.members} for row in rows]

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "type": "bar",
            "labels": [item["organization"] for item in data],
            "data": [item["members"] for item in data],
            "options": {
                "indexAxis": "y",
                "plugins": {"legend": {"display": False}},
                "scales": {
                    "x": {
                        "beginAtZero": True,
                        "ticks": {"stepSize": 1},
                        "title": {"display": True, "text": tk._("Members")},
                    },
                },
            },
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Organization"), tk._("Members")],
            "rows": [[item["organization"], item["members"]] for item in data],
        }


class OrganizationOverviewMetric(MetricBase):
    """Leaderboard showing datasets, resources and members for every organization."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.TABLE
    icon: ClassVar[str] = "fa-solid fa-table-list"

    def __init__(self) -> None:
        super().__init__(
            name="organization_overview",
            title=tk._("Organization Overview"),
            description=tk._("Datasets, resources and members per organization"),
            order=11,
            grid_size="full",
        )

    def get_data(self) -> list[dict[str, Any]]:
        dataset_counts = (
            model.Session.query(
                model.Member.group_id.label("org_id"),
                func.count(func.distinct(model.Package.id)).label("datasets"),
            )
            .join(model.Package, model.Member.table_id == model.Package.id)
            .filter(
                model.Member.table_name == "package",
                model.Member.state == model.State.ACTIVE,
                model.Package.state == model.State.ACTIVE,
                model.Package.type == "dataset",
            )
            .group_by(model.Member.group_id)
            .subquery()
        )

        resource_counts = (
            model.Session.query(
                model.Member.group_id.label("org_id"),
                func.count(func.distinct(model.Resource.id)).label("resources"),
            )
            .join(model.Package, model.Member.table_id == model.Package.id)
            .join(model.Resource, model.Package.id == model.Resource.package_id)
            .filter(
                model.Member.table_name == "package",
                model.Member.state == model.State.ACTIVE,
                model.Package.state == model.State.ACTIVE,
                model.Resource.state == model.State.ACTIVE,
            )
            .group_by(model.Member.group_id)
            .subquery()
        )

        member_counts = (
            model.Session.query(
                model.Member.group_id.label("org_id"),
                func.count(model.Member.id).label("members"),
            )
            .filter(
                model.Member.table_name == "user",
                model.Member.state == model.State.ACTIVE,
            )
            .group_by(model.Member.group_id)
            .subquery()
        )

        rows = (
            model.Session.query(
                model.Group.title,
                func.coalesce(dataset_counts.c.datasets, 0).label("datasets"),
                func.coalesce(resource_counts.c.resources, 0).label("resources"),
                func.coalesce(member_counts.c.members, 0).label("members"),
            )
            .outerjoin(dataset_counts, model.Group.id == dataset_counts.c.org_id)
            .outerjoin(resource_counts, model.Group.id == resource_counts.c.org_id)
            .outerjoin(member_counts, model.Group.id == member_counts.c.org_id)
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
            )
            .order_by(func.coalesce(dataset_counts.c.datasets, 0).desc())
            .all()
        )
        return [
            {
                "organization": row.title,
                "datasets": row.datasets,
                "resources": row.resources,
                "members": row.members,
            }
            for row in rows
        ]

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [
                tk._("Organization"),
                tk._("Datasets"),
                tk._("Resources"),
                tk._("Members"),
            ],
            "rows": [
                [
                    item["organization"],
                    item["datasets"],
                    item["resources"],
                    item["members"],
                ]
                for item in data
            ],
        }


class InactiveOrganizationsMetric(MetricBase):
    """Organizations that have no active datasets — useful for spotting unused entries."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CARD,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.TABLE
    icon: ClassVar[str] = "fa-solid fa-building-circle-xmark"

    def __init__(self) -> None:
        super().__init__(
            name="inactive_organizations",
            title=tk._("Inactive Organizations"),
            description=tk._("Organizations with no active datasets"),
            order=12,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        orgs_with_datasets = (
            model.Session.query(model.Member.group_id)
            .join(model.Package, model.Member.table_id == model.Package.id)
            .filter(
                model.Member.table_name == "package",
                model.Member.state == model.State.ACTIVE,
                model.Package.state == model.State.ACTIVE,
                model.Package.type == "dataset",
            )
            .distinct()
            .subquery()
        )
        rows = (
            model.Session.query(model.Group.title, model.Group.created)
            .filter(
                model.Group.type == "organization",
                model.Group.state == model.State.ACTIVE,
                ~model.Group.id.in_(select(orgs_with_datasets.c.group_id)),
            )
            .order_by(model.Group.title)
            .all()
        )

        return [
            {
                "organization": row.title,
                "created": row.created.strftime("%Y-%m-%d") if row.created else "—",
            }
            for row in rows
        ]

    def get_card_data(self) -> dict[str, Any]:
        return {"value": len(self.get_data()), "label": tk._("Inactive Organizations")}

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [tk._("Organization"), tk._("Created")],
            "rows": [[item["organization"], item["created"]] for item in data],
        }
