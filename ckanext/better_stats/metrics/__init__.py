from collections.abc import Callable

from ckan import plugins as p

from ckanext.better_stats.metrics.base import MetricRegistry

from .base import MetricBase
from .dataset_metrics import (
    DatasetCountMetric,
    DatasetCreationHistoryMetric,
    DatasetsByOrganizationMetric,
    DatasetsWithoutResourcesMetric,
    ResourcesByFormatMetric,
    StaleDatasetsMetric,
    TopTagsMetric,
)
from .organization_metrics import (
    InactiveOrganizationsMetric,
    OrganizationCountMetric,
    OrganizationHierarchyMetric,
    OrganizationMembershipMetric,
    OrganizationOverviewMetric,
    OrganizationSizesMetric,
)
from .portal_metrics import DatasetCompletenessMetric, UserCountMetric
from .system_metrics import CPUMetric, DiskUsageMetric, MemoryMetric

__all__ = [
    "MetricBase",
    "DatasetCountMetric",
    "DatasetsByOrganizationMetric",
    "DatasetCreationHistoryMetric",
    "ResourcesByFormatMetric",
    "TopTagsMetric",
    "DatasetsWithoutResourcesMetric",
    "StaleDatasetsMetric",
    "OrganizationCountMetric",
    "OrganizationHierarchyMetric",
    "OrganizationMembershipMetric",
    "OrganizationOverviewMetric",
    "OrganizationSizesMetric",
    "InactiveOrganizationsMetric",
    "UserCountMetric",
    "DatasetCompletenessMetric",
    "MemoryMetric",
    "CPUMetric",
    "DiskUsageMetric",
]


def register_metrics():
    MetricRegistry.register("dataset_count", DatasetCountMetric)
    MetricRegistry.register("datasets_by_org", DatasetsByOrganizationMetric)
    MetricRegistry.register("dataset_creation_history", DatasetCreationHistoryMetric)
    MetricRegistry.register("resources_by_format", ResourcesByFormatMetric)
    MetricRegistry.register("top_tags", TopTagsMetric)
    MetricRegistry.register("datasets_without_resources", DatasetsWithoutResourcesMetric)
    MetricRegistry.register("stale_datasets", StaleDatasetsMetric)
    MetricRegistry.register("organization_count", OrganizationCountMetric)
    MetricRegistry.register("organization_membership", OrganizationMembershipMetric)
    MetricRegistry.register("organization_overview", OrganizationOverviewMetric)
    MetricRegistry.register("organization_sizes", OrganizationSizesMetric)
    MetricRegistry.register("inactive_organizations", InactiveOrganizationsMetric)
    MetricRegistry.register("user_count", UserCountMetric)
    MetricRegistry.register("dataset_completeness", DatasetCompletenessMetric)
    MetricRegistry.register("memory", MemoryMetric)
    MetricRegistry.register("cpu", CPUMetric)
    MetricRegistry.register("disk_usage", DiskUsageMetric)

    if p.plugin_loaded("hierarchy_display"):
        MetricRegistry.register("organization_hierarchy", OrganizationHierarchyMetric)


def get_all_metrics() -> dict[str, Callable[[], MetricBase]]:
    """Return every registered metric as ``{name: factory}``.

    Sourced from :class:`MetricRegistry` so the dispatch table has a single
    source of truth. Calls :func:`register_metrics` directly to populate the
    registry for callers outside the CKAN plugin lifecycle (e.g. mkdocs).

    The hierarchy metric is included unconditionally in the returned mapping
    so documentation builds can render it even when ``hierarchy_display``
    isn't loaded; the global registry itself stays gated.
    """
    register_metrics()
    metrics = dict(MetricRegistry.METRICS)
    metrics.setdefault("organization_hierarchy", OrganizationHierarchyMetric)
    return metrics
