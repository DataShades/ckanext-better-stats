# Implementation Plan: ckanext-better-stats

## Architecture Overview

The existing foundation is solid: a working `MetricBase` ABC, a `MetricRegistry` singleton, three viz types (chart/table/card), CSV/JSON export, a `register_metrics` ISignal, and a Bootstrap 5 frontend managed by a single JS class. What's missing or incomplete:

- Caching is a stub (`get_cached_data()` just calls `get_data()`)
- Settings page is a stub (always returns 403)
- `get_chart_data()` and `get_table_data()` are abstract — every metric must implement both even if it only supports one
- No `before_metric_render` signal
- No iframe embed or image export
- UI needs a full rework

---

## Phase 4 — UI/UX Overhaul


### 4.6 JavaScript Module Split

Break the monolithic `BetterStatsManager` into focused files (concatenated by webassets):

```
assets/js/
  bstats-stats-manager.js    # CKAN module entry point; orchestrates all others
  bstats-chart-renderer.js   # Chart.js wrapper (create, destroy, update, export PNG)
  bstats-table-renderer.js   # Table build + client-side sort
  bstats-card-renderer.js    # Card number + trend badge
  bstats-progress-renderer.js# Bootstrap progress bar (memory, disk, CPU)
  bstats-export.js           # All export actions (CSV, JSON, PNG, embed modal)
  bstats-embed.js            # Standalone embed page renderer (separate bundle)
  vendor/
    chart.min.js
    snapdom.min.js
    Sortable.min.js           # Settings page drag-to-reorder
```

**Key JS improvements:**
- Parallel metric loading: replace `for…of await` loop with `Promise.all()`
- Per-metric loading state (each card shows its own skeleton independently)
- Toast notifications for copy / export success (Bootstrap 5 `Toast` component)
- Cache age displayed in card footer, updated every 60 s with `setInterval`

## Phase 5 — Developer & Operator Experience

### 5.1 CKAN Config Declaration (`IConfigDeclaration`)

Register all options with type validation so they appear in `ckan config-tool --help`:

```ini
ckanext.better_stats.cache_enabled = true
ckanext.better_stats.cache_timeout = 3600
ckanext.better_stats.embed_allowed_origins = *
ckanext.better_stats.default_access_level = public
ckanext.better_stats.disabled_metrics =             # space-separated list of metric names
```

### 5.2 Signal Catalogue

Document both public signals in `ckanext/better_stats/__init__.py` (module docstring):

| Signal | Sender | Kwargs | Expected return |
|---|---|---|---|
| `better_stats:register_metrics` | `None` | — | — (receivers call `MetricRegistry.register()`) |
| `better_stats:before_metric_render` | `None` | `metric`, `viz_type`, `data` | Modified `data` dict, or `None` to skip |

### 5.3 Custom Metric Example

Third-party extensions subscribe to `better_stats:register_metrics`:

```python
# another_extension/plugin.py
def get_signal_subscriptions(self):
    return {
        tk.signals.ckanext.signal("better_stats:register_metrics"): [
            self.register_my_metrics,
        ],
    }

@staticmethod
def register_my_metrics(sender):
    from ckanext.better_stats.metrics.base import MetricRegistry
    from .metrics import MyCustomMetric
    MetricRegistry.register("my_metric", MyCustomMetric)
```

### 5.4 Tests

| Area | Approach |
|---|---|
| `MetricBase` subclass contract | Pure unit tests — no DB, no CKAN |
| `MetricRegistry` signal firing | Mock the signal; verify registration |
| Caching | Test `_MemoryCache` directly; Redis not required |
| Views (`/metric/`, `/export/`, `/embed/`) | CKAN `test_client()` fixtures |
| `before_metric_render` | Subscribe a test receiver; assert data mutation |
| `MetricConfig` model | CKAN DB fixtures with rollback |
| Auth functions | Standard `check_access` pattern |

Use `pytest-ckan` fixtures (`ckan_config`, `app`, `clean_db`). All tests must pass without Redis.

---

## Implementation Order

| # | Task | Phase |
|---|---|---|
| 1 | `MetricConfig` model + Alembic migration | 1.1 |
| 2 | Iframe embed endpoint + `embed.html` + `bstats-embed.js` | 2.1 |
| 3 | Image export (html2canvas + Chart.js `toBase64Image`) | 2.2 |
| 4 | Export improvements (filename, JSON envelope, auth) | 2.3 |
| 5 | Settings page auth fix + routes + UI | 3 |
| 6 | CSS/SCSS overhaul (variables, grid, card redesign) | 4.1–4.3 |
| 7 | JS module split + parallel loading + toasts + cache age | 4.6 |
| 8 | Progress viz type | 4.7 |
| 9 | `IConfigDeclaration` + config options | 5.1 |
| 10 | Tests | 5.4 |
