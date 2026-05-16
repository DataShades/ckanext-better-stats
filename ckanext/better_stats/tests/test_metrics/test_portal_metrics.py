from __future__ import annotations

from typing import Any

import pytest

from ckanext.better_stats.metrics.portal_metrics import (
    DatasetCompletenessMetric,
    UserCountMetric,
)


@pytest.mark.usefixtures("with_request_context", "with_plugins", "clean_db")
class TestPortalMetrics:
    def test_user_count(self, user_factory: Any) -> None:
        user_factory()
        metric = UserCountMetric()

        assert metric.get_data() >= 1
        assert metric.get_card_data()["value"] >= 1
        assert metric.get_chart_data()["series"][0]["type"] == "line"
        assert metric.get_table_data()["headers"]

    def test_dataset_completeness_empty(self) -> None:
        metric = DatasetCompletenessMetric()
        assert metric.get_data()["total"] == 0

        # Progress and table data have headers even if there are no datasets
        assert len(metric.get_progress_data()["items"]) == 3
        assert len(metric.get_table_data()["rows"]) == 4

    def test_dataset_completeness_with_data(self, dataset_factory: Any, organization_factory: Any) -> None:
        org = organization_factory()
        dataset_factory(owner_org=org["id"], notes="A description", tags=[{"name": "tag1"}])

        metric = DatasetCompletenessMetric()
        data = metric.get_data()

        assert data["total"] == 1
        assert data["with_description"] == 1
        assert data["with_tags"] == 1
        assert metric.get_progress_data()["items"][0]["value"] == 100.0
