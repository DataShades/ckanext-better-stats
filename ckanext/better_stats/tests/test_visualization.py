from __future__ import annotations

from ckanext.better_stats import const
from ckanext.better_stats.visualization import (
    Visualization,
    VisualizationRegistry,
    viz_id,
)


class TestVizId:
    def test_enum_member(self) -> None:
        assert viz_id(const.VisualizationType.CHART) == "chart"

    def test_descriptor(self) -> None:
        assert viz_id(Visualization("foo", "Foo")) == "foo"

    def test_plain_string(self) -> None:
        assert viz_id("user_map") == "user_map"


class TestVisualizationRegistry:
    def test_builtins_registered(self) -> None:
        for viz in const.VisualizationType:
            descriptor = VisualizationRegistry.get(viz.value)
            assert descriptor is not None
            assert descriptor.name == viz.value

    def test_get_unknown_returns_none(self) -> None:
        assert VisualizationRegistry.get("does-not-exist") is None
        assert VisualizationRegistry.get(None) is None

    def test_register_and_get(self) -> None:
        VisualizationRegistry.register(Visualization("temp_viz", "Temp", "fa fa-flask"))
        try:
            descriptor = VisualizationRegistry.get("temp_viz")
            assert descriptor is not None
            assert descriptor.label == "Temp"
            assert descriptor.icon == "fa fa-flask"
        finally:
            VisualizationRegistry._registry.pop("temp_viz", None)

    def test_resolve_fallback_for_unregistered(self) -> None:
        resolved = VisualizationRegistry.resolve("ghost_viz")
        assert resolved.name == "ghost_viz"
        assert resolved.label == "ghost_viz"
        assert resolved.icon == "fa fa-question"

    def test_resolve_known(self) -> None:
        resolved = VisualizationRegistry.resolve(const.VisualizationType.TABLE)
        assert resolved.name == "table"
        assert resolved.label == "Table"
