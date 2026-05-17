import ckan.plugins.toolkit as tk
from ckan import model, types

from ckanext.better_stats import const
from ckanext.better_stats.metrics import MetricBase, MetricRegistry


@tk.auth_allow_anonymous_access
def better_stats_view_dashboard(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": True}


def better_stats_view_settings(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False, "msg": tk._("Only sysadmins can view metric settings")}


def better_stats_update_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False, "msg": tk._("Only sysadmins can update metric settings")}


@tk.auth_allow_anonymous_access
@tk.auth_sysadmins_check
def better_stats_read_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    """Check if the current user can read the specified metric.

    Parameters:
        metric_name: The name of the metric to read.
    """
    metric = MetricRegistry.get_metric(data_dict.get("metric_name", ""))

    if metric is None:
        return {"success": False, "msg": tk._("Metric not specified")}

    return _check_metric_access(
        context,
        metric,
        not_logged_in_msg=tk._("Must be logged in to read this metric"),
        not_sysadmin_msg=tk._("Must be a sysadmin to read this metric"),
    )


@tk.auth_allow_anonymous_access
@tk.auth_sysadmins_check
def better_stats_export_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    """Check if the current user can export the specified metric.

    Parameters:
        metric_name: The name of the metric to export.
    """
    metric = MetricRegistry.get_metric(data_dict.get("metric_name", ""))

    if metric is None:
        return {"success": False, "msg": tk._("Metric not specified")}

    if not metric.can_export():
        return {"success": False, "msg": tk._("This metric cannot be exported")}

    return _check_metric_access(
        context,
        metric,
        not_logged_in_msg=tk._("Must be logged in to export this metric"),
        not_sysadmin_msg=tk._("Must be a sysadmin to export this metric"),
    )


def _check_metric_access(
    context: types.Context,
    metric: MetricBase,
    not_logged_in_msg: str,
    not_sysadmin_msg: str,
) -> types.AuthResult:
    """Evaluate *metric*'s ``access_level`` against the user in *context*.

    Both messages are passed in fully translated so gettext extraction keeps
    working and callers can phrase the verb naturally ("read", "export").
    """
    access_level = getattr(metric, "access_level", const.AccessLevel.PUBLIC.value)

    if access_level == const.AccessLevel.PUBLIC.value:
        return {"success": True}

    user = model.User.get(context.get("user", ""))

    if not user:
        return {"success": False, "msg": not_logged_in_msg}

    if access_level == const.AccessLevel.AUTHENTICATED.value:
        return {"success": True}

    # access_level == const.AccessLevel.ADMIN.value can be passed only by sysadmins
    return {
        "success": user.sysadmin,
        "msg": not_sysadmin_msg if not user.sysadmin else "",
    }
