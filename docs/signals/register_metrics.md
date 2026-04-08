# register_metrics_signal

The `ckanext-better-stats` extension exposes `register_metrics_signal`, a blinker signal that allows external CKAN extensions to register their own custom metrics.

## Registration Process

1. Inherit from `ckanext.better_stats.metrics.base.MetricBase`.
2. Implement your metric logic (at a minimum, provide a `get_data()` method).
3. Connect a receiver function to `register_metrics_signal` using the `ISignal` interface.
4. Call `MetricRegistry.register(name, MetricClass)` inside your receiver.

See the example below:

```python
import ckan.plugins.toolkit as tk

from ckanext.better_stats.metrics.base import MetricBase, MetricRegistry, register_metrics_signal
from ckanext.better_stats import const

class MyCustomMetric(MetricBase):
    """Tracks things across the portal."""

    supported_visualizations = [
        const.VisualizationType.CARD,
        const.VisualizationType.TABLE
    ]
    default_visualization = const.VisualizationType.CARD
    icon = "fa-solid fa-star"

    def __init__(self) -> None:
        super().__init__(
            name="my_custom_metric",
            title=tk._("My Custom Metric"),
            description=tk._("Tracks awesome things across the portal"),
            order=200,
            access_level=const.AccessLevel.PUBLIC.value,
        )

    def get_data(self) -> int:
        return 42

    def get_card_data(self) -> dict:
        return {"value": self.get_data(), "label": self.title}

    def get_table_data(self) -> dict:
        return {
            "headers": ["Metric", "Value"],
            "rows": [["Awesome Things", self.get_data()]]
        }


class MyExtensionPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ISignal)

    ...

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("better_stats:register_metrics"): [
                self.register_metrics,
            ],
        }

    @staticmethod
    def register_metrics(sender: None):
        MetricRegistry.register("my_custom_metric", MyCustomMetric)

```

As a result, your metric will be available in the dashboard right away. See how it looks in the example below:

![custom metric example](./../image/custom_metric.png)
