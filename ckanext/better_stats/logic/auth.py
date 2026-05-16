import ckan.plugins.toolkit as tk
from ckan import model, types

from ckanext.better_stats import const
from ckanext.better_stats.metrics import MetricRegistry


@tk.auth_allow_anonymous_access
def better_stats_view_dashboard(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": True}


def better_stats_view_settings(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False, "msg": tk._("Only sysadmins can view metric settings")}


def better_stats_update_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False, "msg": tk._("Only sysadmins can update metric settings")}


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

    access_level = getattr(metric, "access_level", const.AccessLevel.PUBLIC.value)

    if access_level == const.AccessLevel.PUBLIC.value:
        return {"success": True}

    user = model.User.get(context.get("user", ""))

    if not user:
        return {
            "success": False,
            "msg": tk._("Must be logged in to export this metric"),
        }

    if access_level == const.AccessLevel.AUTHENTICATED.value:
        return {"success": True}

    # access_level == const.AccessLevel.ADMIN.value can be passed only by sysadmins
    return {
        "success": user.sysadmin,
        "msg": tk._("Must be a sysadmin to export this metric") if not user.sysadmin else "",
    }
