"""Pluggable visualization-type registry.

A *visualization* is one way a metric can be rendered (``chart``, ``table``,
``card``, ``progress`` — and anything an extension wants to add, e.g. a map).

Each visualization has a backend descriptor (:class:`Visualization`: an ``id``,
a translated ``label`` and an ``icon`` for the pill switcher) and a matching
frontend renderer registered on the JS side via ``ckan.bstats.registerRenderer``.
The data itself is produced by the metric through a conventionally named method
``get_<id>_data`` (see :meth:`MetricBase._compute_viz_data`).

The four built-ins are registered at import time so the registry is always
usable, even outside the CKAN plugin lifecycle (e.g. mkdocs). Extensions add
their own by connecting a receiver to :data:`register_visualizations_signal`
and calling :meth:`VisualizationRegistry.register` from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const


@dataclass(frozen=True)
class Visualization:
    """Descriptor for a single visualization type.

    :param name: Stable string id (matches the ``?type=`` query param, the
        ``get_<name>_data`` method on metrics, and the JS renderer key).
    :param label: Human-readable, translatable label shown on the pill.
    :param icon: Font Awesome class string for the pill icon.
    """

    name: str
    label: str
    icon: str = "fa fa-question"


def viz_id(viz: const.VisualizationType | Visualization | str) -> str:
    """Normalise a visualization reference (enum member, descriptor, or str) to its id."""
    if isinstance(viz, const.VisualizationType):
        return viz.value
    if isinstance(viz, Visualization):
        return viz.name
    return str(viz)


register_visualizations_signal = tk.signals.ckanext.signal(
    "better_stats:register_visualizations",
    "Register custom visualization types for the better_stats extension."
    " Receivers call VisualizationRegistry.register(Visualization(...)).",
)


class VisualizationRegistry:
    """Registry of all available visualization types, keyed by id.

    Built-ins are present from import time. Custom types are added lazily the
    first time the registry is read, by firing
    :data:`register_visualizations_signal` exactly once per process.
    """

    _registry: ClassVar[dict[str, Visualization]] = {}
    _loaded: ClassVar[bool] = False

    @classmethod
    def _ensure_loaded(cls) -> None:
        """Fire the registration signal exactly once per process lifetime."""
        if not cls._loaded:
            cls._loaded = True
            register_visualizations_signal.send()

    @classmethod
    def register(cls, viz: Visualization) -> None:
        """Register (or replace) a visualization descriptor."""
        cls._registry[viz.name] = viz

    @classmethod
    def get(cls, name: str | None) -> Visualization | None:
        """Return the descriptor for *name*, or ``None`` if not registered."""
        cls._ensure_loaded()
        if name is None:
            return None
        return cls._registry.get(name)

    @classmethod
    def has(cls, name: str | None) -> bool:
        """Return ``True`` if a visualization is registered under *name*."""
        return cls.get(name) is not None

    @classmethod
    def resolve(cls, viz: const.VisualizationType | Visualization | str) -> Visualization:
        """Return the registered descriptor for *viz*, or a fallback descriptor.

        The fallback (label = id, default icon) keeps the dashboard rendering
        gracefully even when a metric lists a viz type that nothing registered.
        """
        vid = viz_id(viz)
        return cls.get(vid) or Visualization(name=vid, label=vid)

    @classmethod
    def all(cls) -> dict[str, Visualization]:
        """Return a copy of the full registry (built-ins + custom)."""
        cls._ensure_loaded()
        return dict(cls._registry)


VisualizationRegistry.register(
    Visualization(const.VisualizationType.CHART.value, tk._("Chart"), "fa fa-line-chart"),
)
VisualizationRegistry.register(
    Visualization(const.VisualizationType.TABLE.value, tk._("Table"), "fa fa-table"),
)
VisualizationRegistry.register(
    Visualization(const.VisualizationType.CARD.value, tk._("Card"), "fa fa-calculator"),
)
VisualizationRegistry.register(
    Visualization(const.VisualizationType.PROGRESS.value, tk._("Progress"), "fa fa-tasks"),
)
