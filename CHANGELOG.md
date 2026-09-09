# Changelog

All notable changes to `ckanext-better-stats` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-09-09

### Removed

- **BREAKING:** the `better_stats:before_metric_render` signal
  (`before_metric_render_signal`). Consuming a return value from a fan-out
  signal made the outcome depend on receiver order and silently let one
  subscriber shadow the others. To customise a built-in metric, subclass it and
  re-register it under the same name via `better_stats:register_metrics` — see
  [Overriding a built-in metric](https://datashades.github.io/ckanext-better-stats/signals/register_metrics/#overriding-a-built-in-metric).

### Added

- Documentation for registering custom visualization types
  (`better_stats:register_visualizations`), with `better_stats_demo` as the
  reference implementation.
- Documentation for overriding a built-in metric by subclassing and
  re-registering.

### Fixed

- `solr_search` now scopes every query to the current site's `site_id`, like
  all CKAN core searches. Previously `DatasetCreationHistoryMetric` could count
  datasets belonging to another CKAN instance sharing the same SOLR core.

## [1.1.0] - 2026-08-31

Released as git tag `v1.1.0`.

## [1.0.0] - 2026-08-07

Released as git tag `v1.0.0`.

---

Earlier releases (`v0.3.0`–`v0.9.1`) are recorded as git tags only.

[Unreleased]: https://github.com/DataShades/ckanext-better-stats/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/DataShades/ckanext-better-stats/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/DataShades/ckanext-better-stats/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/DataShades/ckanext-better-stats/releases/tag/v1.0.0
