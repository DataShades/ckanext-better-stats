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
