from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, cast

import ckan.plugins.toolkit as tk

from ckanext.better_stats import cache, const
from ckanext.better_stats.model import MetricConfig


class MetricBase(ABC):
    """Base class for all metrics.

    Subclasses must implement :meth:`get_data` and should declare
    :attr:`supported_visualizations` and :attr:`default_visualization` as
    class attributes alongside any visualization methods they support.

    Visualization methods (:meth:`get_chart_data`, :meth:`get_table_data`,
    :meth:`get_card_data`) return ``None`` by default, signalling that the
    metric does not support that particular view.  Override only the ones
    listed in :attr:`supported_visualizations`.

    The :attr:`scope` class variable controls cache isolation:

    * ``MetricScope.GLOBAL`` (default) — one shared cache entry for the whole
      site.  Use this for metrics whose results are identical for every user
      (e.g. system metrics or aggregate counts that bypass SOLR and always
      reflect the full dataset catalogue).

    * ``MetricScope.USER`` — a separate cache entry per authenticated user,
      keyed by ``tk.current_user.id``.  Use this for metrics whose results
      must respect CKAN's SOLR ``permission_labels``, i.e. when the data
      shown should differ depending on which datasets the requesting user is
      allowed to see.
    """

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [const.VisualizationType.CHART]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.CHART
    icon: ClassVar[str] = "fa-solid fa-chart-bar"
    supported_export_formats: ClassVar[list[str]] = ["csv", "json", "xlsx", "image"]
    scope: ClassVar[const.MetricScope] = const.MetricScope.GLOBAL

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        title: str = "",
        description: str = "",
        col_span: int = 3,
        row_span: int = 1,
        order: int = 100,
        cache_timeout: int = 600,
        access_level: str = const.AccessLevel.PUBLIC.value,
    ) -> None:
        self.name = name
        self.title = title
        self.description = description
        self.col_span = col_span
        self.row_span = row_span
        self.order = order
        self.cache_timeout = cache_timeout
        self.access_level = access_level

    @property
    def cache_key(self) -> str:
        """Return the base cache key for this metric (without viz-type suffix).

        Global metrics share one key across all users::

            better_stats:global:metric:<name>

        User-scoped metrics are keyed by the current user's ID::

            better_stats:user:<user_id>:metric:<name>
        """
        if self.scope is const.MetricScope.USER:
            user_id = tk.current_user.id or "anonymous"
            return f"better_stats:user:{user_id}:metric:{self.name}"

        return f"better_stats:global:metric:{self.name}"

    @abstractmethod
    def get_data(self) -> dict[str, Any] | list[Any] | int | float:
        """Fetch raw data for the metric.

        This is the only method subclasses are required to implement.
        All visualization methods call this (directly or indirectly).
        """

    def get_chart_data(self) -> dict[str, Any] | None:
        """Return a Chart.js-compatible config dict, or ``None`` if unsupported."""
        return None

    def get_table_data(self) -> dict[str, Any] | None:
        """Return ``{"headers": [...], "rows": [[...], ...]}`` or ``None`` if unsupported."""
        return None

    def get_card_data(self) -> dict[str, Any] | None:
        """Return card data.

        Return ``{"value": ..., "label": ...}`` or ``None`` if unsupported.

        The default implementation works for any metric whose :meth:`get_data`
        returns a plain ``int`` or ``float``.
        """
        data = self.get_data()
        if isinstance(data, (int, float)):
            return {"value": data, "label": self.title}
        return None

    def get_progress_data(self) -> dict[str, Any] | None:
        """Return progress data.

        Return ``{"items": [{"label": str, "value": num, "max": num, "unit": str}]}``
        or ``None`` if unsupported.

        Each item renders as a labelled horizontal progress bar.
        """
        return None

    def _compute_viz_data(self, viz_type: const.VisualizationType) -> dict[str, Any] | None:
        """Dispatch to the appropriate visualization method without caching.

        Returns ``None`` for unknown or unsupported visualization types.
        """
        dispatch: dict[const.VisualizationType, Callable[[], dict[str, Any] | None]] = {
            const.VisualizationType.CHART: self.get_chart_data,
            const.VisualizationType.TABLE: self.get_table_data,
            const.VisualizationType.CARD: self.get_card_data,
            const.VisualizationType.PROGRESS: self.get_progress_data,
        }
        handler = dispatch.get(viz_type)
        return handler() if handler else None

    def get_viz_data(self, viz_type: const.VisualizationType) -> dict[str, Any] | None:
        """Return visualization data for *viz_type*, reading from cache when available.

        On a cache miss the result of :meth:`_compute_viz_data` is stored
        before being returned.  Returns ``None`` for unsupported types.
        """
        key = f"{self.cache_key}:{viz_type.value}"

        if cached := cache.cache_get(key):
            return cached

        if data := self._compute_viz_data(viz_type):
            cache.cache_set(key, data, self.cache_timeout)

        return data

    def supports_visualization(self, viz_type: const.VisualizationType) -> bool:
        """Return ``True`` if this metric supports *viz_type*."""
        return viz_type in self.supported_visualizations

    def get_cached_data(self, viz_type: const.VisualizationType, refresh: bool = False) -> dict[str, Any] | None:
        """Return visualization data for *viz_type*, with optional forced refresh.

        When *refresh* is ``True`` the cached entry for *viz_type* is deleted
        before fetching, guaranteeing fresh data is returned and re-cached.
        For invalidating all visualization types at once use
        :meth:`refresh_cache`.
        """
        if refresh:
            cache.cache_delete(f"{self.cache_key}:{viz_type.value}")

        return self.get_viz_data(viz_type)

    def refresh_cache(self) -> None:
        """Invalidate all cached visualization entries for this metric.

        For **global** metrics the four per-viz-type keys are deleted directly.

        For **user-scoped** metrics a Redis ``SCAN`` is used to delete every
        entry matching ``better_stats:user:*:metric:<name>:*``, covering all
        users at once.  This is the correct behaviour for admin-initiated cache
        clears — it ensures no stale per-user entries linger after a forced
        refresh.
        """
        if self.scope is const.MetricScope.USER:
            cache.cache_delete_pattern(f"better_stats:user:*:metric:{self.name}:*")
        else:
            for viz in const.VisualizationType:
                cache.cache_delete(f"{self.cache_key}:{viz.value}")

    @classmethod
    def can_export(cls) -> bool:
        """Return ``True`` if metric data may be exported."""
        return True

    def get_export_data(self) -> dict[str, Any]:
        """Return data in export format (defaults to table data)."""
        return self.get_table_data() or {}

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict of metric metadata."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "col_span": self.col_span,
            "row_span": self.row_span,
            "order": self.order,
            "supported_visualizations": [v.value for v in self.supported_visualizations],
            "default_visualization": self.default_visualization.value,
            "supported_export_formats": list(self.supported_export_formats),
            "access_level": self.access_level,
        }


register_metrics_signal = tk.signals.ckanext.signal(
    "better_stats:register_metrics",
    "Register metrics for the better_stats extension",
)

before_metric_render_signal = tk.signals.ckanext.signal(
    "better_stats:before_metric_render",
    "Fired after metric visualization data is fetched, before it is returned"
    " to the client. Receivers accept (sender, context) where context is a"
    " dict with keys 'metric', 'viz_type' (str), and 'data' (dict|None)."
    " Return a replacement data dict to override the value, or None to leave"
    " it unchanged. The first non-None return wins.",
)


class MetricRegistry:
    """Registry for all available metrics.

    Metric factories (zero-argument callables returning a :class:`MetricBase`)
    are registered via :meth:`register`.  Passing a class directly is the
    normal usage — each concrete metric class takes no constructor arguments.
    All read methods return freshly instantiated :class:`MetricBase` objects
    sorted by :attr:`~MetricBase.order`.
    """

    METRICS: ClassVar[dict[str, Callable[[], MetricBase]]] = {}
    _loaded: ClassVar[bool] = False

    @classmethod
    def _ensure_loaded(cls) -> None:
        """Fire the registration signal exactly once per process lifetime."""
        if not cls._loaded:
            cls._loaded = True
            register_metrics_signal.send()

    @classmethod
    def register(cls, name: str, metric_factory: Callable[[], MetricBase]) -> None:
        """Register *metric_factory* under *name*.

        *metric_factory* must be a zero-argument callable that returns a
        :class:`MetricBase` instance.  Passing the metric class itself is the
        typical usage (e.g. ``MetricRegistry.register("foo", FooMetric)``).
        """
        cls.METRICS[name] = metric_factory

    @classmethod
    def get_metric(cls, name: str) -> MetricBase | None:
        """Return a configured instance of the named metric, or ``None`` if not found or disabled."""
        cls._ensure_loaded()
        factory = cls.METRICS.get(name)

        if not factory:
            return None

        metric = factory()
        cfg = MetricConfig.for_metric(name)

        if cfg is not None:
            if not cfg.enabled:
                return None

            metric.order = cast(int, cfg.order)
            metric.col_span = cast(int, cfg.col_span)
            metric.row_span = cast(int, cfg.row_span)
            metric.cache_timeout = cast(int, cfg.cache_timeout)
            metric.access_level = str(cfg.access_level or metric.access_level)

        return metric

    @classmethod
    def get_all_metrics(cls) -> list[MetricBase]:
        """Return fresh instances of all registered metrics, sorted by order."""
        cls._ensure_loaded()
        return sorted(
            (factory() for factory in cls.METRICS.values()),
            key=lambda m: m.order,
        )

    @classmethod
    def get_enabled_metrics(cls) -> list[MetricBase]:
        """Return enabled metrics sorted by stored order.

        Queries :class:`~ckanext.better_stats.model.MetricConfig` for each
        registered metric and applies stored overrides (``enabled``, ``order``,
        ``col_span``, ``row_span``, ``cache_timeout``, ``access_level``) to the metric
        instance before returning.  Metrics with ``enabled=False`` are
        excluded.  Falls back to :meth:`get_all_metrics` if the DB is
        unavailable (e.g. during tests without a DB fixture).
        """
        cls._ensure_loaded()

        try:
            results: list[MetricBase] = []
            for name, factory in cls.METRICS.items():
                metric = factory()
                cfg = MetricConfig.for_metric(name)

                if cfg is not None:
                    if not cfg.enabled:
                        continue

                    metric.order = cfg.order  # type: ignore
                    metric.col_span = cfg.col_span  # type: ignore
                    metric.row_span = cfg.row_span  # type: ignore
                    metric.cache_timeout = cfg.cache_timeout  # type: ignore
                    metric.access_level = cfg.access_level or metric.access_level  # type: ignore

                results.append(metric)

            return sorted(results, key=lambda m: m.order)
        except Exception:  # noqa: BLE001
            return cls.get_all_metrics()

    @classmethod
    def reset(cls) -> None:
        """Clear all registered metrics and reset the loaded flag.

        Intended for use in tests only.
        """
        cls.METRICS.clear()
        cls._loaded = False
