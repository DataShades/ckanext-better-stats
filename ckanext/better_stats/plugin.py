from ckan import plugins as p
from ckan import types
from ckan.common import CKANConfig
from ckan.plugins import tk


@tk.blanket.blueprints
@tk.blanket.helpers
@tk.blanket.auth_functions
class BetterStatsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ISignal)

    # IConfigurer

    def update_config(self, config_: CKANConfig) -> None:
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "better_stats")

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("better_stats:register_metrics"): [
                self.register_metrics,
            ],
        }

    @staticmethod
    def register_metrics(sender: None):
        from ckanext.better_stats.metrics import dataset_metrics as ds_metrics
        from ckanext.better_stats.metrics import system_metrics as sys_metrics
        from ckanext.better_stats.metrics.base import MetricRegistry

        # Register metrics
        MetricRegistry.register("dataset_count", ds_metrics.DatasetCountMetric)
        MetricRegistry.register("datasets_by_org", ds_metrics.DatasetsByOrganizationMetric)
        MetricRegistry.register("dataset_creation_history", ds_metrics.DatasetCreationHistoryMetric)
        MetricRegistry.register("memory", sys_metrics.MemoryMetric)
        MetricRegistry.register("cpu", sys_metrics.CPUMetric)
        MetricRegistry.register("disk_usage", sys_metrics.DiskUsageMetric)
