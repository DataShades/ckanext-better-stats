from __future__ import annotations

from unittest import mock

import pytest

from ckanext.better_stats import search


@pytest.fixture
def fake_perm_labels():
    """Stub get_permission_labels so SOLR isn't called."""
    perm = mock.MagicMock()
    perm.get_user_dataset_labels.return_value = ["public", "user-1"]

    with mock.patch("ckanext.better_stats.search.get_permission_labels", return_value=perm):
        yield perm


def test_solr_search_combines_fq_string(fake_perm_labels: mock.MagicMock) -> None:
    fake_client = mock.MagicMock()
    with mock.patch("ckanext.better_stats.search.tk.current_user") as mock_user:
        mock_user.is_anonymous = True
        search.solr_search(fq="state:active", client=fake_client, rows=10)
    fake_client.search.assert_called_once_with(
        "*:*",
        fq=["permission_labels:(public OR user-1)", "state:active"],
        rows=10,
    )


def test_solr_search_combines_fq_list(fake_perm_labels: mock.MagicMock) -> None:
    fake_client = mock.MagicMock()
    with mock.patch("ckanext.better_stats.search.tk.current_user") as mock_user:
        mock_user.is_anonymous = True
        search.solr_search(fq=["a:1", "b:2"], client=fake_client)
    args, kwargs = fake_client.search.call_args
    assert kwargs["fq"] == ["permission_labels:(public OR user-1)", "a:1", "b:2"]


def test_solr_search_no_extra_fq(fake_perm_labels: mock.MagicMock) -> None:
    fake_client = mock.MagicMock()
    with mock.patch("ckanext.better_stats.search.tk.current_user") as mock_user:
        mock_user.is_anonymous = True
        search.solr_search(client=fake_client)
    _, kwargs = fake_client.search.call_args
    assert kwargs["fq"] == ["permission_labels:(public OR user-1)"]


def test_solr_search_creates_default_client(fake_perm_labels: mock.MagicMock) -> None:
    fake_client = mock.MagicMock()
    with mock.patch("ckanext.better_stats.search.make_connection", return_value=fake_client) as mk:
        with mock.patch("ckanext.better_stats.search.tk.current_user") as mock_user:
            mock_user.is_anonymous = True
            search.solr_search()
    mk.assert_called_once()
    fake_client.search.assert_called_once()
