from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan.common import config
from ckan.lib.plugins import get_permission_labels
from ckan.lib.search.common import make_connection
from ckan.lib.search.query import solr_literal


def solr_search(fq: str | list[str] = "", client: Any = None, **params: Any) -> Any:
    """Run a SOLR query with the current user's permission labels applied.

    Merges the permission label filter with any caller-supplied *fq*, then
    forwards *params* to pysolr's ``Solr.search``.

    This lets metrics run arbitrary SOLR queries (e.g. ``facet.range``) while
    still respecting dataset visibility — exactly what ``package_search`` does
    internally but without its limited parameter surface.

    The query is always scoped to the current site's ``site_id`` (as every CKAN
    core search is), so metrics never count documents belonging to another CKAN
    instance sharing the same SOLR core.

    When making multiple queries in one metric, pass a shared *client* (from
    ``make_connection()``) to avoid creating a new HTTP session per call:

        client = make_connection()
        r1 = solr_search(..., client=client)
        r2 = solr_search(..., client=client)

    :param fq: Extra filter query string or list of strings.
    :param client: Optional pre-built pysolr ``Solr`` instance. A new one is
        created via ``make_connection()`` when omitted.
    :param params: Keyword arguments forwarded verbatim to ``solr.search()``.
    :returns: The raw pysolr ``Results`` object.
    """
    user = None if tk.current_user.is_anonymous else tk.current_user
    labels = get_permission_labels().get_user_dataset_labels(user)
    permission_fq = f"permission_labels:({' OR '.join(labels)})"
    site_fq = f"+site_id:{solr_literal(config.get('ckan.site_id'))}"

    if isinstance(fq, list):
        all_fq = [site_fq, permission_fq, *fq]
    elif fq:
        all_fq = [site_fq, permission_fq, fq]
    else:
        all_fq = [site_fq, permission_fq]

    if client is None:
        client = make_connection()

    return client.search("*:*", fq=all_fq, **params)
