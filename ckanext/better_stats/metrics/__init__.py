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


def get_all_metrics() -> dict[str, type[MetricBase]]:
    return {
        "dataset_count": DatasetCountMetric,
        "datasets_by_org": DatasetsByOrganizationMetric,
        "dataset_creation_history": DatasetCreationHistoryMetric,
        "resources_by_format": ResourcesByFormatMetric,
        "top_tags": TopTagsMetric,
        "datasets_without_resources": DatasetsWithoutResourcesMetric,
        "stale_datasets": StaleDatasetsMetric,
        "organization_count": OrganizationCountMetric,
        "organization_membership": OrganizationMembershipMetric,
        "organization_overview": OrganizationOverviewMetric,
        "organization_sizes": OrganizationSizesMetric,
        "inactive_organizations": InactiveOrganizationsMetric,
        "user_count": UserCountMetric,
        "dataset_completeness": DatasetCompletenessMetric,
        "memory": MemoryMetric,
        "cpu": CPUMetric,
        "disk_usage": DiskUsageMetric,
    }
