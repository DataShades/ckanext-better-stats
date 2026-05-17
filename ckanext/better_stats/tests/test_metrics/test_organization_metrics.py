from __future__ import annotations

from typing import Any

import pytest

from ckanext.better_stats.metrics import (
    InactiveOrganizationsMetric,
    OrganizationCountMetric,
    OrganizationMembershipMetric,
    OrganizationOverviewMetric,
    OrganizationSizesMetric,
)


@pytest.mark.usefixtures("with_request_context", "with_plugins", "clean_db")
class TestOrganizationMetrics:
    def test_organization_count(self, organization_factory: Any) -> None:
        organization_factory()
        organization_factory()
        metric = OrganizationCountMetric()

        assert metric.get_data() == 2
        assert metric.get_card_data()["value"] == 2
        assert metric.get_chart_data()["series"][0]["type"] == "line"
        assert metric.get_table_data()["headers"]

    def test_organization_membership(self, organization_factory: Any, user_factory: Any) -> None:
        org = organization_factory(users=[user_factory()])
        metric = OrganizationMembershipMetric()

        assert metric.get_data() == [{"organization": org["title"], "members": 2}]
        assert metric.get_chart_data()["series"][0]["type"] == "bar"
        assert metric.get_table_data()["headers"]

    def test_organization_overview(self, organization_factory: Any, dataset_factory: Any) -> None:
        org = organization_factory()
        dataset_factory(owner_org=org["id"])
        metric = OrganizationOverviewMetric()

        data = metric.get_data()[0]

        assert data["datasets"] == 1
        assert data["members"] == 1
        assert data["resources"] == 0
        assert data["organization"] == {"text": org["title"], "url": f"/organization/{org['name']}"}

        assert isinstance(metric.get_data(), list)
        assert metric.get_table_data()["headers"]

    def test_organization_sizes(self, dataset_factory: Any, organization_factory: Any) -> None:
        org = organization_factory()
        dataset_factory(owner_org=org["id"])
        metric = OrganizationSizesMetric()
        data = metric.get_data()

        assert isinstance(metric.get_data(), list)
        assert data[0] == {"count": 1, "organization": org["title"], "url": f"/organization/{org['name']}"}
        assert metric.get_chart_data()["series"][0]["type"] == "treemap"
        assert metric.get_table_data()["headers"]

    def test_inactive_organizations(self, organization_factory: Any) -> None:
        org = organization_factory()
        metric = InactiveOrganizationsMetric()
        data = metric.get_data()[0]

        assert data["organization"] == org["title"]
        assert data["created"]
        assert metric.get_card_data()["value"] == 1
        assert metric.get_table_data()["headers"]
