[![Tests](https://github.com/DataShades/ckanext-better-stats/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-better-stats/actions/workflows/test.yml)

# ckanext-better-stats

The `ckanext-better-stats` is a modular CKAN extension that provides a flexible metrics framework for collecting, processing, and visualizing platform statistics. Each metric encapsulates its own data retrieval logic, access control, caching strategy, and rendering, enabling scalable and customizable analytics without tight coupling to specific visualization backends.

See the [documentation](https://datashades.github.io/ckanext-better-stats/) for more details.

## Tests

To run the tests, do:
```sh
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
