from ckan import types
from ckan.logic.schema import validator_args

from ckanext.better_stats import const


@validator_args
def better_stats_update_metric(
    not_missing: types.Validator,
    not_empty: types.Validator,
    ignore_missing: types.Validator,
    unicode_safe: types.Validator,
    boolean_validator: types.Validator,
    int_validator: types.Validator,
    is_positive_integer: types.Validator,
    one_of: types.ValidatorFactory,
) -> types.Schema:

    return {
        "metric_name": [not_missing, not_empty, unicode_safe],
        "enabled": [ignore_missing, boolean_validator],
        "order": [ignore_missing, int_validator],
        "grid_size": [
            ignore_missing,
            unicode_safe,
            one_of([e.value for e in const.GridSize]),
        ],
        "access_level": [
            ignore_missing,
            unicode_safe,
            one_of([e.value for e in const.AccessLevel]),
        ],
        "cache_timeout": [ignore_missing, is_positive_integer],
        "__extras": [ignore_missing],
    }
