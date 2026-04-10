import ckan.plugins.toolkit as tk
from ckan import model, types

from ckanext.better_stats import const


@tk.auth_allow_anonymous_access
def better_stats_view_dashboard(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": True}


def better_stats_view_settings(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False}


def better_stats_update_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    return {"success": False}


@tk.auth_allow_anonymous_access
@tk.auth_sysadmins_check
def better_stats_export_metric(context: types.Context, data_dict: types.DataDict) -> types.AuthResult:
    """Allow export if the user can view the metric.

    Sysadmins always pass.  For everyone else the caller must supply
    ``data_dict["metric"]`` — a :class:`~ckanext.better_stats.metrics.base.MetricBase`
    instance — so that the access level can be checked.
    """
    metric = data_dict.get("metric")

    if metric is None:
        return {"success": False, "msg": tk._("Metric not specified")}

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
    return {"success": user.sysadmin}
