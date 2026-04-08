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
    OrganizationMembershipMetric,
    OrganizationOverviewMetric,
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
    "OrganizationMembershipMetric",
    "OrganizationOverviewMetric",
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
    MetricRegistry.register("inactive_organizations", InactiveOrganizationsMetric)
    MetricRegistry.register("user_count", UserCountMetric)
    MetricRegistry.register("dataset_completeness", DatasetCompletenessMetric)
    MetricRegistry.register("memory", MemoryMetric)
    MetricRegistry.register("cpu", CPUMetric)
    MetricRegistry.register("disk_usage", DiskUsageMetric)
