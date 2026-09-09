# register_visualizations_signal

Out of the box `ckanext-better-stats` renders metrics as a `chart`, `table`,
`card` or `progress` bar. The `register_visualizations_signal` blinker signal
lets an external extension add **its own visualization types** — a map, a word
cloud, a sparkline, a gauge — that then behave like first-class citizens on the
dashboard: pill switcher, expand modal, embed, export, caching.

A visualization type has **two halves**, and both are keyed by the same string
id:

| Half | Where | What it does |
| --- | --- | --- |
| **Backend descriptor** | Python — `Visualization(id, label, icon)` registered on `VisualizationRegistry` | Gives the pill switcher a label + icon and tells the framework the type exists. The data itself comes from the metric's `get_<id>_data()` method (convention dispatch, same as the built-ins). |
| **Frontend renderer** | JavaScript — `ckan.bstats.registerRenderer(id, fn)` | Draws the visualization into a container element from the metric payload. |

If the ids don't match, the dashboard shows *"No renderer registered for
`<id>`"* in place of the metric.

## Backend: register the type

1. Connect a receiver to the `better_stats:register_visualizations` signal using
   the `ISignal` interface.
2. In the receiver, call
   `VisualizationRegistry.register(Visualization(id, label, icon))`.
3. In your metric, list the id in `supported_visualizations` (and optionally
   `default_visualization`). String ids and the built-in
   `const.VisualizationType` enum members mix freely.
4. Implement `get_<id>_data()` on the metric — it returns the payload your
   renderer will consume. `get_data()` stays the single source of truth; the
   viz method just shapes it.

```python
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase, MetricRegistry
from ckanext.better_stats.visualization import Visualization, VisualizationRegistry

SPARKLINE_VIZ = "sparkline"


class SignupSparklineMetric(MetricBase):
    """New user signups over the last 30 days, drawn as a sparkline."""

    supported_visualizations = [SPARKLINE_VIZ, const.VisualizationType.TABLE]
    default_visualization = SPARKLINE_VIZ
    icon = "fa-solid fa-chart-line"
    supported_export_formats = ["csv", "json", "xlsx"]

    def __init__(self) -> None:
        super().__init__(
            name="signup_sparkline",
            title=tk._("Signup Sparkline"),
            description=tk._("New user registrations per day (last 30 days)"),
            order=200,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict]:
        # ... query your data, return e.g. [{"day": "2026-09-01", "count": 4}, ...]
        ...

    def get_sparkline_data(self) -> dict:
        """Payload consumed by the `sparkline` client renderer."""
        rows = self.get_data()
        return {"values": [r["count"] for r in rows], "labels": [r["day"] for r in rows]}

    def get_table_data(self) -> dict:
        return {
            "headers": [tk._("Day"), tk._("Signups")],
            "rows": [[r["day"], r["count"]] for r in self.get_data()],
        }


class MyExtensionPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ISignal)

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("better_stats:register_visualizations"): [
                self.register_visualizations,
            ],
            tk.signals.ckanext.signal("better_stats:register_metrics"): [
                self.register_metrics,
            ],
        }

    @staticmethod
    def register_visualizations(sender: None):
        VisualizationRegistry.register(
            Visualization(SPARKLINE_VIZ, tk._("Sparkline"), "fa fa-chart-line"),
        )

    @staticmethod
    def register_metrics(sender: None):
        MetricRegistry.register("signup_sparkline", SignupSparklineMetric)
```

## Frontend: register the renderer

A renderer is a function `(container, data, ctx) => void`:

- `container` — the empty `HTMLElement` to draw into.
- `data` — the **full** metric payload from the API
  (`{name, title, description, data, type, ...}`). Your viz payload — whatever
  `get_<id>_data()` returned — is `data.data`.
- `ctx` — `{ contentId, theme, manager }`, where `theme` is `"dark"` or
  `"default"`.

Register it on the global `ckan.bstats` registry. Setting the registry up
defensively means it works no matter whether your bundle loads before or after
the core Better Stats bundle:

```javascript
// assets/js/my-sparkline.js
(function () {
    window.ckan = window.ckan || {};
    ckan.bstats = ckan.bstats || {};
    ckan.bstats.renderers = ckan.bstats.renderers || {};
    ckan.bstats.registerRenderer =
        ckan.bstats.registerRenderer ||
        function (type, fn) { ckan.bstats.renderers[type] = fn; };

    ckan.bstats.registerRenderer("sparkline", function (container, data, ctx) {
        var payload = (data && data.data) || {};
        var values = payload.values || [];
        if (!values.length) {
            container.textContent = "No data";
            return;
        }

        var max = Math.max.apply(null, values);
        var w = 120, h = 32, step = w / (values.length - 1 || 1);
        var points = values
            .map(function (v, i) { return (i * step) + "," + (h - (v / max) * h); })
            .join(" ");

        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", "0 0 " + w + " " + h);
        svg.setAttribute("width", "100%");
        var poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        poly.setAttribute("fill", "none");
        poly.setAttribute("stroke", ctx.theme === "dark" ? "#93c5fd" : "#2563eb");
        poly.setAttribute("stroke-width", "2");
        poly.setAttribute("points", points);
        svg.appendChild(poly);
        container.appendChild(svg);
    });
})();
```

## Load the renderer on the dashboard

Ship the script as a webasset and pull it in from `page.html` so it loads on
every page (and therefore on the dashboard), regardless of plugin load order:

```yaml
# assets/webassets.yml
my_ext-bstats-js:
  filter: rjsmin
  output: ckanext-my_ext/%(version)s-bstats.js
  contents:
    - js/my-sparkline.js
  extra:
    preload:
      - base/main
```

{% raw %}
```html
{# templates/page.html #}
{% ckan_extends %}

{%- block scripts %}
    {{ super() }}
    {% asset 'my_ext/my_ext-bstats-js' %}
{% endblock %}
```
{% endraw %}

That's it — the metric appears on the dashboard with a **Sparkline** pill, and
expand / embed / export / caching all work with no extra code.

## Reference implementation: `better_stats_demo`

The repo ships a `better_stats_demo` plugin that registers **two** custom
visualization types and **four** demo metrics against them (all backed by
fixed-seed fake data, so it never touches the database):

| Viz type | Renderer | Metrics | Notes |
| --- | --- | --- | --- |
| `map` | `ckanext/better_stats_demo/assets/ts/bstats-maps.ts` | `user_origin`, `datasets_by_region`, `download_activity` | Leaflet + `leaflet.heat`. One data-driven renderer; each metric ships its own `tiles` / `style` / `color` in the payload, so three metrics look completely different through one viz type. |
| `tag_cloud` | `ckanext/better_stats_demo/assets/ts/bstats-tag-cloud.ts` | `popular_tags` | Dependency-free — pure DOM, font-size scaled by count. Good starting point to copy. |

Key files to read:

- `ckanext/better_stats_demo/metrics/tag_cloud.py` — descriptor + metric +
  `register_visualizations()` in one small module.
- `ckanext/better_stats_demo/metrics/map.py` — one renderer shared by several
  metrics.
- `ckanext/better_stats_demo/assets/ts/bstats-viz.ts` — the renderer contract
  (`VizContext`, `VizRenderer`) and the idempotent `registerRenderer` helper.
- `ckanext/better_stats_demo/templates/page.html` — how the renderer bundle is
  loaded.
- `ckanext/better_stats_demo/plugin.py` — wiring both `better_stats:register_*`
  signals via `ISignal`.

Enable it with `better_stats better_stats_demo` in `ckan.plugins` to see the
demo metrics on your dashboard (they are `admin`-only, so view the dashboard as
a sysadmin).

## Notes

- **The id is the contract.** The `Visualization` id, the
  `get_<id>_data` method name, the `supported_visualizations` entry and the
  `registerRenderer` key must all be the same string.
- **Export still works.** A custom-viz metric exports via `get_export_data()`
  (which defaults to `get_table_data()`), so give the metric a `table`
  visualization too, or override `get_export_data()`.
- **Caching is automatic.** `get_<id>_data()` output is cached in Redis under
  the metric's `cache_timeout` just like the built-ins.
- **Missing renderer.** If the backend registers a type but no JS renderer is
  found for it at render time, the card shows *"No renderer registered for
  `<id>`"* rather than failing silently.
