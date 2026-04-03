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


def bs_get_embed_url(metric_name: str) -> str:
    """Return the absolute URL for the embed page for *metric_name*."""
    return tk.url_for(
        "better_stats.embed_metric", metric_name=metric_name, _external=True
    )


def bs_get_embed_code(metric_name: str, width: str = "600", height: str = "400") -> str:
    """Return a ready-to-paste <iframe> embed snippet."""
    return (
        f'<iframe src="{bs_get_embed_url(metric_name)}" '
        f'width="{width}" height="{height}" '
        f'frameborder="0" '
        f'style="border:1px solid #e2e8f0;border-radius:8px">'
        f"</iframe>"
    )
