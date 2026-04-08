# Available Metrics

`ckanext-better-stats` ships with a collection of built-in metrics that you can use out-of-the-box. Below is the documentation generated directly from the metric definitions.

## Dataset Metrics
These metrics track the number and status of datasets and resources.

{{ render_metric('dataset_count') }}

{{ render_metric('dataset_completeness') }}

{{ render_metric('datasets_by_org') }}

{{ render_metric('dataset_creation_history') }}

{{ render_metric('resources_by_format') }}

{{ render_metric('top_tags') }}

{{ render_metric('datasets_without_resources') }}

{{ render_metric('stale_datasets') }}

## Organization Metrics
These metrics provide insights into organization activity and structure.

{{ render_metric('organization_count') }}

{{ render_metric('organization_membership') }}

{{ render_metric('organization_overview') }}

{{ render_metric('inactive_organizations') }}

## User Metrics
Track platform users.

{{ render_metric('user_count') }}

## System Metrics
Underlying system performance (CPU, Memory, Disk).

{{ render_metric('memory') }}

{{ render_metric('cpu') }}

{{ render_metric('disk_usage') }}

