from __future__ import annotations

from typing import Any, cast
from unittest import mock

import pytest

from ckan.tests.helpers import call_action

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase, MetricRegistry
from ckanext.better_stats.model import MetricConfig


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestMetricRegistry:
    def test_register_and_get(self, metric_factory: Any) -> None:
        metric_factory(name="dummy")
        metric_factory(name="another")

        metric1 = MetricRegistry.get_metric("dummy")
        assert metric1 is not None
        assert metric1.name == "dummy"

        metric2 = MetricRegistry.get_metric("another")
        assert metric2 is not None
        assert metric2.name == "another"

    def test_get_metric_not_found(self) -> None:
        assert MetricRegistry.get_metric("missing") is None

    def test_get_metric_disabled(self, metric_factory: Any) -> None:
        metric = metric_factory(name="dummy")

        assert MetricRegistry.get_metric("dummy") is not None

        call_action("better_stats_update_metric", metric_name=metric.name, enabled=False)
        assert MetricRegistry.get_metric("dummy") is None

    def test_get_enabled_metrics(self, metric_factory: Any, fresh_registry) -> None:
        assert len(MetricRegistry.get_enabled_metrics()) == 21

        metric_factory(name="another")
        assert len(MetricRegistry.get_enabled_metrics()) == 22

    def test_get_enabled_metrics_excludes_disabled(self, metric_factory: Any) -> None:
        metric = metric_factory(name="dummy")

        call_action("better_stats_update_metric", metric_name=metric.name, enabled=False)

        names = [m.name for m in MetricRegistry.get_enabled_metrics()]
        assert metric.name not in names

    def test_get_all_metrics_sorted_by_order(self) -> None:
        metrics = MetricRegistry.get_all_metrics()
        prev_order = None

        for metric in metrics:
            if prev_order is not None:
                assert metric.order >= prev_order

            prev_order = metric.order

    def test_metric_config_overrides(self, metric_factory: Any) -> None:
        metric = metric_factory()
        MetricConfig.upsert(
            metric.name,
            col_span=6,
            order=999,
            row_span=2,
            cache_timeout=120,
            access_level="admin",
        )

        metric = cast(MetricBase, MetricRegistry.get_metric(metric.name))
        assert metric.col_span == 6
        assert metric.order == 999
        assert metric.row_span == 2
        assert metric.cache_timeout == 120
        assert metric.access_level == "admin"

    def test_reset_clears_state(self, metric_factory: Any) -> None:
        metric_factory()

        MetricRegistry._loaded = True
        MetricRegistry.reset()

        assert MetricRegistry.METRICS == {}
        assert MetricRegistry._loaded is False


class TestMetricBase:
    def test_supports_visualization(self, metric_factory: Any) -> None:
        metric = metric_factory()
        assert metric.supports_visualization(const.VisualizationType.CHART) is True
        assert metric.supports_visualization(const.VisualizationType.TABLE) is False

    def test_to_dict(self, metric_factory: Any) -> None:
        metric = metric_factory()
        data = metric.to_dict()
        assert data["name"] == metric.name
        assert data["title"] == metric.title
        assert data["default_visualization"] == const.VisualizationType.CHART.value
        assert "supported_export_formats" in data
        assert "group" in data

    def test_get_card_data_default_for_int(self, metric_factory: Any) -> None:
        metric = metric_factory()
        card = metric.get_card_data()
        assert card == {"value": metric.get_data(), "label": metric.title}

    def test_default_viz_methods_return(self, metric_factory: Any) -> None:
        metric = metric_factory(title="Metric")

        assert metric.get_card_data()
        assert metric.get_chart_data() is None
        assert metric.get_table_data() is None
        assert metric.get_progress_data() is None

    def test_compute_viz_data_unknown_type(self, metric_factory: Any) -> None:
        metric = metric_factory()
        result = metric._compute_viz_data(const.VisualizationType.PROGRESS)
        assert result is None

    def test_can_export_default_true(self, metric_factory: Any) -> None:
        metric = metric_factory()
        assert metric.can_export() is True

    def test_get_export_data_falls_back_to_table(self) -> None:
        class TableMetric(MetricBase):
            supported_visualizations = [const.VisualizationType.TABLE]
            default_visualization = const.VisualizationType.TABLE

            def __init__(self) -> None:
                super().__init__(name="table_metric")

            def get_data(self) -> int:
                return 1

            def get_table_data(self) -> dict[str, Any]:
                return {"headers": ["x"], "rows": [[1]]}

        assert TableMetric().get_export_data() == {"headers": ["x"], "rows": [[1]]}

    def test_get_export_data_empty_for_no_table(self, metric_factory: Any) -> None:
        metric = metric_factory()
        assert metric.get_export_data() == {}

    def test_cache_key_global(self, metric_factory: Any) -> None:
        metric = metric_factory()
        assert metric.cache_key == f"better_stats:global:metric:{metric.name}"

    def test_cache_key_user_scoped(self, metric_factory: Any) -> None:
        metric = metric_factory(class_attrs={"scope": const.MetricScope.USER})

        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.id = "user-123"
            assert metric.cache_key == f"better_stats:user:{mock_user.id}:metric:{metric.name}"

    def test_get_viz_data_caches_result(self, metric_factory: Any) -> None:
        metric = metric_factory()

        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            mock_cache.cache_get.return_value = None

            metric.get_viz_data(const.VisualizationType.CARD)

            mock_cache.cache_set.assert_called_once()

    def test_get_viz_data_returns_cached(self, metric_factory: Any) -> None:
        metric = metric_factory()
        cached = {"value": 99, "label": "cached"}
        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            mock_cache.cache_get.return_value = cached
            result = metric.get_viz_data(const.VisualizationType.CHART)
            assert result == cached
            mock_cache.cache_set.assert_not_called()

    def test_refresh_cache_global(self, metric_factory: Any) -> None:
        metric = metric_factory()
        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            metric.refresh_cache()
            # Global metrics clear one cache key per supported visualization.
            assert mock_cache.cache_delete.call_count == len(metric.supported_visualizations)

    def test_refresh_cache_user_scoped(self, metric_factory: Any) -> None:
        metric = metric_factory(class_attrs={"scope": const.MetricScope.USER})

        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            metric.refresh_cache()
            mock_cache.cache_delete_pattern.assert_called_once_with(f"better_stats:user:*:metric:{metric.name}:*")

    def test_get_cached_data_with_refresh(self, metric_factory: Any) -> None:
        metric = metric_factory()

        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            mock_cache.cache_get.return_value = None
            metric.get_cached_data(const.VisualizationType.CHART, refresh=True)
            mock_cache.cache_delete.assert_called_once()


class _CustomVizMetric(MetricBase):
    """Metric exercising a custom, extension-style visualization id."""

    supported_visualizations = ["user_map", const.VisualizationType.TABLE]
    default_visualization = "user_map"

    def __init__(self) -> None:
        super().__init__(name="custom_viz_metric", title="Custom")

    def get_data(self) -> int:
        return 1

    def get_user_map_data(self) -> dict[str, Any]:
        return {"points": [{"lat": 0, "lng": 0, "count": 1}]}

    def get_table_data(self) -> dict[str, Any]:
        return {"headers": ["x"], "rows": [[1]]}


class TestCustomVisualization:
    def test_compute_viz_data_dispatches_by_convention(self) -> None:
        metric = _CustomVizMetric()
        assert metric._compute_viz_data("user_map") == {"points": [{"lat": 0, "lng": 0, "count": 1}]}

    def test_default_visualization_id_for_string(self) -> None:
        assert _CustomVizMetric().default_visualization_id == "user_map"

    def test_supports_visualization_accepts_string_and_enum(self) -> None:
        metric = _CustomVizMetric()
        assert metric.supports_visualization("user_map") is True
        assert metric.supports_visualization(const.VisualizationType.TABLE) is True
        assert metric.supports_visualization("card") is False

    def test_get_viz_data_for_custom_type(self) -> None:
        metric = _CustomVizMetric()
        with mock.patch("ckanext.better_stats.metrics.base.cache") as mock_cache:
            mock_cache.cache_get.return_value = None
            data = metric.get_viz_data("user_map")
            assert data == {"points": [{"lat": 0, "lng": 0, "count": 1}]}
            # Cache key is suffixed with the custom viz id.
            key = mock_cache.cache_set.call_args.args[0]
            assert key.endswith(":user_map")

    def test_to_dict_serialises_custom_viz_descriptor(self) -> None:
        data = _CustomVizMetric().to_dict()
        names = [v["name"] for v in data["supported_visualizations"]]
        assert names == ["user_map", "table"]
        # Each entry carries the resolved label/icon (fallback for unregistered).
        assert all({"name", "label", "icon"} <= v.keys() for v in data["supported_visualizations"])
        assert data["default_visualization"] == "user_map"
