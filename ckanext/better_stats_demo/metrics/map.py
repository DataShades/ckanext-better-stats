"""DEMO map metrics shipped by the ``better_stats_demo`` plugin.

A *single*, data-driven ``map`` visualization type (registered here, with its
client-side renderer in ``assets/ts/bstats-maps.ts``) backs three metrics that
all render with that one viz yet *look* different, because each ships its own
``tiles`` preset and marker ``style`` in the data payload:

  - :class:`UserOriginMetric`       — OSM tiles, blue circle markers
  - :class:`DatasetsByRegionMetric` — terrain tiles, green value pins
  - :class:`DownloadActivityMetric` — satellite tiles, a heatmap layer

All three use entirely fake, fixed-seed data, so the demo never touches the DB.
"""

from __future__ import annotations

import random
from typing import Any, ClassVar

import ckan.plugins.toolkit as tk

from ckanext.better_stats_demo.metrics.const import GROUP

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase, MetricRegistry
from ckanext.better_stats.visualization import Visualization, VisualizationRegistry

MAP_VIZ = "map"


class _DemoMapMetric(MetricBase):
    """Shared base for the demo map metrics.

    Subclasses produce ``[{name, lat, lng, count}]`` from :meth:`get_data` and
    pick a ``_tiles`` preset / marker ``_style`` / accent ``_color``. The common
    ``get_map_data`` packs those into the payload the ``map`` renderer reads
    (convention dispatch: ``get_<viz>_data``).
    """

    supported_visualizations: ClassVar[list[const.VisualizationType | str]] = [
        MAP_VIZ,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType | str] = MAP_VIZ
    icon: ClassVar[str] = "fa-solid fa-map-location-dot"
    supported_export_formats: ClassVar[list[str]] = ["csv", "json", "xlsx"]
    scope: ClassVar[const.MetricScope] = const.MetricScope.GLOBAL
    group = GROUP

    # Look of the map — overridden per metric.
    _tiles: ClassVar[str] = "osm"
    _style: ClassVar[str] = "circles"
    _color: ClassVar[str] = "#3b82f6"

    def get_data(self) -> list[dict[str, Any]]:  # pragma: no cover - overridden
        raise NotImplementedError

    def get_map_data(self) -> dict[str, Any]:
        """Payload consumed by the data-driven ``map`` client renderer."""
        return {
            "points": self.get_data(),
            "tiles": self._tiles,
            "style": self._style,
            "color": self._color,
        }


class UserOriginMetric(_DemoMapMetric):
    """DEMO: simulated users scattered across the world on an OSM map.

    Blue circle markers on OpenStreetMap tiles. Data is a fixed-seed spread of
    random markers, so the map and table always agree and never hit the DB.
    """

    _tiles: ClassVar[str] = "osm"
    _style: ClassVar[str] = "circles"
    _color: ClassVar[str] = "#3b82f6"

    _MARKER_COUNT: ClassVar[int] = 20
    _SEED: ClassVar[int] = 42

    def __init__(self) -> None:
        super().__init__(
            name="user_origin",
            title=tk._("Users by Origin"),
            description=tk._("Demo: simulated users scattered across the world"),
            order=10,
            col_span=3,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        """Return ``[{name, lat, lng, count}]`` — random markers."""
        rng = random.Random(self._SEED)  # noqa: S311
        # Keep latitudes within roughly habitable bounds so markers don't land
        # in the polar caps; longitudes span the whole globe.
        return [
            {
                "name": tk._("Origin {n}").format(n=i + 1),
                "lat": round(rng.uniform(-55.0, 70.0), 4),
                "lng": round(rng.uniform(-180.0, 180.0), 4),
                "count": rng.randint(1, 500),
            }
            for i in range(self._MARKER_COUNT)
        ]

    def get_table_data(self) -> dict[str, Any]:
        return {
            "headers": [
                tk._("Origin"),
                tk._("Latitude"),
                tk._("Longitude"),
                tk._("Users"),
            ],
            "rows": [[p["name"], p["lat"], p["lng"], p["count"]] for p in self.get_data()],
        }


class DatasetsByRegionMetric(_DemoMapMetric):
    """DEMO: simulated dataset counts pinned to world regions.

    Green value-pin markers on OpenTopoMap terrain tiles — a deliberately
    different look from :class:`UserOriginMetric` while reusing the ``map`` viz.
    """

    _tiles: ClassVar[str] = "topo"
    _style: ClassVar[str] = "pins"
    _color: ClassVar[str] = "#16a34a"

    _REGIONS: ClassVar[list[tuple[str, float, float]]] = [
        ("North America", 40.0, -100.0),
        ("South America", -15.0, -60.0),
        ("Western Europe", 48.0, 8.0),
        ("Eastern Europe", 52.0, 30.0),
        ("Sub-Saharan Africa", -2.0, 25.0),
        ("Middle East", 29.0, 45.0),
        ("South Asia", 22.0, 78.0),
        ("East Asia", 35.0, 110.0),
        ("Southeast Asia", 5.0, 110.0),
        ("Oceania", -25.0, 135.0),
    ]
    _SEED: ClassVar[int] = 7

    def __init__(self) -> None:
        super().__init__(
            name="datasets_by_region",
            title=tk._("Datasets by Region"),
            description=tk._("Demo: simulated dataset counts pinned to world regions"),
            order=20,
            col_span=3,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        rng = random.Random(self._SEED)  # noqa: S311
        return [
            {
                "name": tk._(name),
                "lat": lat,
                "lng": lng,
                "count": rng.randint(5, 240),
            }
            for name, lat, lng in self._REGIONS
        ]

    def get_table_data(self) -> dict[str, Any]:
        return {
            "headers": [
                tk._("Region"),
                tk._("Latitude"),
                tk._("Longitude"),
                tk._("Datasets"),
            ],
            "rows": [[p["name"], p["lat"], p["lng"], p["count"]] for p in self.get_data()],
        }


class DownloadActivityMetric(_DemoMapMetric):
    """DEMO: simulated download hotspots rendered as a heatmap.

    A ``leaflet.heat`` layer over Esri satellite imagery. Points are scattered
    in clusters around a few busy hubs so the heatmap shows recognisable
    hotspots rather than uniform noise.
    """

    _tiles: ClassVar[str] = "satellite"
    _style: ClassVar[str] = "heat"
    _color: ClassVar[str] = "#f97316"

    _HUBS: ClassVar[list[tuple[str, float, float]]] = [
        ("New York", 40.7, -74.0),
        ("London", 51.5, -0.1),
        ("Berlin", 52.5, 13.4),
        ("Nairobi", -1.3, 36.8),
        ("Mumbai", 19.1, 72.9),
        ("Singapore", 1.3, 103.8),
        ("Sydney", -33.9, 151.2),
        ("São Paulo", -23.5, -46.6),
    ]
    _POINTS_PER_HUB: ClassVar[int] = 8
    _SEED: ClassVar[int] = 13

    def get_data(self) -> list[dict[str, Any]]:
        rng = random.Random(self._SEED)  # noqa: S311

        return [
            {
                "name": name,
                # Jitter around the hub so the heatmap forms a blob.
                "lat": round(lat + rng.uniform(-3.0, 3.0), 4),
                "lng": round(lng + rng.uniform(-3.0, 3.0), 4),
                "count": rng.randint(1, 100),
            }
            for name, lat, lng in self._HUBS
            for _ in range(self._POINTS_PER_HUB)
        ]

    def __init__(self) -> None:
        super().__init__(
            name="download_activity",
            title=tk._("Download Activity"),
            description=tk._("Demo: simulated download hotspots as a heatmap"),
            order=30,
            col_span=6,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_table_data(self) -> dict[str, Any]:
        return {
            "headers": [
                tk._("Hub"),
                tk._("Latitude"),
                tk._("Longitude"),
                tk._("Downloads"),
            ],
            "rows": [[p["name"], p["lat"], p["lng"], p["count"]] for p in self.get_data()],
        }


def register_visualizations() -> None:
    """Register the single, data-driven ``map`` visualization type."""
    VisualizationRegistry.register(
        Visualization(MAP_VIZ, tk._("Map"), "fa fa-map-location-dot"),
    )


def register_metrics() -> None:
    """Register the demo map metrics."""
    MetricRegistry.register("user_origin", UserOriginMetric)
    MetricRegistry.register("datasets_by_region", DatasetsByRegionMetric)
    MetricRegistry.register("download_activity", DownloadActivityMetric)
