from ckan import plugins as p
from ckan import types
from ckan.common import CKANConfig
from ckan.plugins import toolkit as tk


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
        from ckanext.better_stats.metrics import register_metrics

        register_metrics()
