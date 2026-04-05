import ckan.plugins.toolkit as tk
from ckan import model

from ckanext.better_stats import const


def better_stats_view_dashboard(context, data_dict):
    return {"success": True}


def better_stats_view_settings(context, data_dict):
    return {"success": False}


@tk.auth_sysadmins_check
def better_stats_export_metric(context, data_dict):
    """Allow export if the user can view the metric.

    Sysadmins always pass.  For everyone else the caller must supply
    ``data_dict["metric"]`` — a :class:`~ckanext.better_stats.metrics.base.MetricBase`
    instance — so that the access level can be checked.
    """
    user = model.User.get(context.get("user", ""))
    metric = data_dict.get("metric")

    if metric is None:
        return {"success": False, "msg": tk._("Metric not specified")}

    if not user:
        return {"success": False, "msg": tk._("You've to be authorized to export the memtrics")}

    access_level = getattr(metric, "access_level", const.AccessLevel.PUBLIC.value)

    if access_level == const.AccessLevel.PUBLIC.value:
        return {"success": True}

    if access_level == const.AccessLevel.AUTHENTICATED.value:
        if user:
            return {"success": True}

        return {
            "success": False,
            "msg": tk._("Must be logged in to export this metric"),
        }

    # access_level == const.AccessLevel.ADMIN.value can be passed only by sysadmins
    return {"success": user.sysadmin}
