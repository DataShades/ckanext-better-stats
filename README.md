[![Tests](https://github.com/DataShades/ckanext-better-stats/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-better-stats/actions/workflows/test.yml)

# ckanext-better-stats

The `ckanext-better-stats` is a modular CKAN extension that provides a flexible metrics framework for collecting, processing, and visualizing platform statistics. Each metric encapsulates its own data retrieval logic, access control, caching strategy, and rendering (table, chart or card), enabling scalable and customizable analytics without tight coupling to specific visualization backends.

## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.10 and earlier | no           |
| 2.11+            | yes          |


## Installation

1. `pip install -e .` or `pip install ckanext-better-stats`

2. Add `better_stats` to the `ckan.plugins` setting in your CKAN config file.

3. Restart CKAN.

## Signals

### `before_metric_render` signal

Fired after metric visualization data is fetched, before it is returned to the client.
Receivers accept (sender, context) where context is a dict with keys 'metric', 'viz_type' (str), and 'data' (dict|None).
Return a replacement data dict to override the value, or None to leave it unchanged. The first non-None return wins.

```python
def get_signal_subscriptions(self):
    return {
        tk.signals.ckanext.signal("better_stats:before_metric_render"): [
            self.on_before_metric_render,
        ],
    }

@staticmethod
def on_before_metric_render(sender, context):
    if context["metric"].name == "dataset_count":
        # Enrich or transform data; return modified copy
        return {**context["data"], "value": context["data"]["value"] + 10}
    return None  # no change
```

## Config settings

None at present

## Tests

To run the tests, do:
```sh
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
