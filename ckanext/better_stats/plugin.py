from ckan import plugins, types
from ckan.plugins import toolkit


@toolkit.blanket.blueprints
@toolkit.blanket.helpers
@toolkit.blanket.auth_functions
class BetterStatsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ISignal)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "better_stats")

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            toolkit.signals.ckanext.signal("better_stats:register_metrics"): [
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
