# Custom Metrics

The `ckanext-better-stats` extension is built to be extensible. You can register your own custom metrics from another CKAN extension by acting upon the provided signal `register_metrics_signal` and inheriting from `MetricBase`.

## 1. Create your Metric Class
First, define a custom metric by inheriting from `MetricBase`. You must implement the `get_data` abstract method. You may also specify supported visualization formats.

```python
import ckan.plugins.toolkit as tk

from ckanext.better_stats.metrics.base import MetricBase
from ckanext.better_stats import const

class MyCustomMetric(MetricBase):
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
        # Example logic: count custom records from the database
        return 42

    def get_card_data(self) -> dict:
        return {"value": self.get_data(), "label": self.title}

    def get_table_data(self) -> dict:
        return {
            "headers": ["Metric", "Value"],
            "rows": [["Awesome Things", self.get_data()]]
        }
```

## 2. Register via Signals
In your extension's `plugin.py` or initialization file, connect a function to `register_metrics_signal` to append your metric to the `MetricRegistry`.

```python
from ckanext.better_stats.metrics.base import MetricRegistry, register_metrics_signal
from .my_metrics import MyCustomMetric

@register_metrics_signal.connect
def register_my_metrics(sender, **kwargs):
    """
    Hook into better_stats and inject our custom metric.
    """
    MetricRegistry.register("my_custom_metric", MyCustomMetric)
```

## 3. Override Render Output (Optional)
If you need to intercept and override data right before it is forwarded to the client for rendering, you can connect to `before_metric_render_signal`.

```python
from ckanext.better_stats.metrics.base import before_metric_render_signal

@before_metric_render_signal.connect
def modify_metric_data(sender, context, **kwargs):
    metric = context["metric"]
    viz_type = context["viz_type"]
    data = context["data"]

    if metric.name == "my_custom_metric" and viz_type == "card":
        # Override the payload value
        return {"value": 9000, "label": "It's over 9000!"}

    # Return None to pass modifications to other receivers or use the default
    return None
```
