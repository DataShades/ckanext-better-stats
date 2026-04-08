# Installation

## Requirements

Redis must be configured and running.

Compatibility with core CKAN versions:

| CKAN version     | Compatible?   |
| ---------------- | ------------- |
| 2.10 and earlier | no            |
| 2.11+            | yes           |

## Installation

1. `pip install -e .` or `pip install ckanext-better-stats`

2. Add `better_stats` to the `ckan.plugins` setting in your CKAN config file.

3. Restart CKAN.
