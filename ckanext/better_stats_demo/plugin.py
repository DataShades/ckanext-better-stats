from ckan import plugins as p
from ckan import types
from ckan.common import CKANConfig
from ckan.plugins import toolkit as tk

from ckanext.better_stats_demo.metrics import register_metrics, register_visualizations


class BetterStatsDemoPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ISignal)

    # IConfigurer

    def update_config(self, config_: CKANConfig) -> None:
        tk.add_template_directory(config_, "templates")
        tk.add_resource("assets", "better_stats_demo")

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("better_stats:register_metrics"): [
                self.register_metrics,
            ],
            tk.signals.ckanext.signal("better_stats:register_visualizations"): [
                self.register_visualizations,
            ],
        }

    @staticmethod
    def register_metrics(sender: None):
        register_metrics()

    @staticmethod
    def register_visualizations(sender: None):
        register_visualizations()
