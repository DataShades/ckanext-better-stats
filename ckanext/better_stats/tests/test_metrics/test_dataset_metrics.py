from __future__ import annotations

from typing import Any
from unittest import mock

import pytest

from ckanext.better_stats.metrics import (
    DatasetCountMetric,
    DatasetCreationHistoryMetric,
    DatasetsByOrganizationMetric,
    DatasetsWithoutResourcesMetric,
    ResourcesByFormatMetric,
    StaleDatasetsMetric,
    TopTagsMetric,
)


@pytest.mark.usefixtures("with_request_context", "with_plugins", "clean_db", "clean_index")
class TestDatasetCountMetric:
    def test_dataset_count_metric(self, dataset_factory: Any) -> None:
        dataset_factory()
        dataset_factory()

        metric = DatasetCountMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            count = metric.get_data()
            assert count == 2

    def test_dataset_count_table_data(self, dataset_factory: Any) -> None:
        dataset_factory()

        metric = DatasetCountMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            table_data = metric.get_table_data()

            assert "headers" in table_data
            assert table_data["rows"][0][1] == 1


@pytest.mark.usefixtures("with_request_context", "with_plugins", "clean_db", "clean_index")
class TestDatasetMetricsBranches:
    def test_datasets_by_organization_get_data(self, dataset_factory: Any, organization_factory: Any) -> None:
        org = organization_factory()
        dataset_factory(owner_org=org["id"])

        metric = DatasetsByOrganizationMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            data = metric.get_data()

        assert isinstance(data, list)
        chart = metric.get_chart_data()
        assert chart["series"][0]["type"] == "pie"
        table = metric.get_table_data()
        assert "headers" in table

    def test_dataset_creation_history_returns_empty_when_no_data(self) -> None:
        metric = DatasetCreationHistoryMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            assert metric.get_data() == []
            assert metric.get_chart_data()["series"][0]["type"] == "line"
            assert metric.get_table_data()["headers"]

    def test_resources_by_format_aggregates(self) -> None:
        metric = ResourcesByFormatMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            data = metric.get_data()
            chart = metric.get_chart_data()
            table = metric.get_table_data()
        assert isinstance(data, list)
        assert chart["series"][0]["type"] == "pie"
        assert table["headers"]

    def test_top_tags(self) -> None:
        metric = TopTagsMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            data = metric.get_data()
            chart = metric.get_chart_data()
            table = metric.get_table_data()
        assert isinstance(data, list)
        assert chart["series"][0]["type"] == "bar"
        assert table["headers"]

    def test_datasets_without_resources_card_and_table(self) -> None:
        metric = DatasetsWithoutResourcesMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            data = metric.get_data()
            card = metric.get_card_data()
            table = metric.get_table_data()
            export = metric.get_export_data()
        assert isinstance(data, list)
        assert card["value"] == len(data)
        assert table["headers"]
        assert export["headers"]

    def test_stale_datasets_card_and_table(self) -> None:
        metric = StaleDatasetsMetric()
        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.name = "sysadmin"
            data = metric.get_data()
            card = metric.get_card_data()
            table = metric.get_table_data()
            export = metric.get_export_data()
        assert isinstance(data, list)
        assert card["value"] == len(data)
        assert table["headers"]
        assert export == table
