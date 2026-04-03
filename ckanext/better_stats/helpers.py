import ckan.plugins.toolkit as tk

from ckanext.better_stats import const


def check_user_can_access_metric(metric):
    """Check if current user can access metric"""
    access_level = metric.get_access_level()

    if access_level == const.AccessLevel.PUBLIC.value:
        return True
    elif access_level == const.AccessLevel.AUTHENTICATED.value:
        return tk.current_user.is_authenticated
    elif access_level == const.AccessLevel.ADMIN.value:
        return not tk.current_user.is_anonymous and tk.current_user.sysadmin  # type: ignore

    return False


def bs_get_viz_icon(viz_type: str) -> str:
    return {
        "chart": "fa fa-line-chart",
        "table": "fa fa-table",
        "card": "fa fa-calculator",
    }.get(viz_type, "fa fa-question")


def bs_get_viz_label(viz_type: str) -> str:
    return {"chart": tk._("Chart"), "table": tk._("Table"), "card": tk._("Card")}.get(
        viz_type, viz_type
    )
