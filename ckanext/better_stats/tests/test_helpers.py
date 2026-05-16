from __future__ import annotations

from collections.abc import Callable
from unittest import mock

import pytest

from ckanext.better_stats import const, helpers
from ckanext.better_stats.metrics.base import MetricBase


class TestUserCheckAccess:
    def test_check_user_can_access_public_metric(self, metric_factory: Callable[..., MetricBase]) -> None:
        metric = metric_factory(name="x", access_level=const.AccessLevel.PUBLIC.value)
        assert helpers.check_user_can_access_metric(metric) is True

    def test_check_user_can_access_authenticated(self, metric_factory: Callable[..., MetricBase]) -> None:
        metric = metric_factory(name="x", access_level=const.AccessLevel.AUTHENTICATED.value)

        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.is_authenticated = True
            assert helpers.check_user_can_access_metric(metric) is True

            mock_user.is_authenticated = False
            assert helpers.check_user_can_access_metric(metric) is False

    def test_check_user_can_access_admin(self, metric_factory: Callable[..., MetricBase]) -> None:
        metric = metric_factory(name="x", access_level=const.AccessLevel.ADMIN.value)

        with mock.patch("ckan.plugins.toolkit.current_user") as mock_user:
            mock_user.is_anonymous = False
            mock_user.sysadmin = True
            assert helpers.check_user_can_access_metric(metric) is True

            mock_user.sysadmin = False
            assert helpers.check_user_can_access_metric(metric) is False

            mock_user.is_anonymous = True
            mock_user.sysadmin = True
            assert helpers.check_user_can_access_metric(metric) is False

    def test_check_user_cant_access_unknown_level(self, metric_factory: Callable[..., MetricBase]) -> None:
        metric = metric_factory(name="xxx", access_level="xxx")
        assert helpers.check_user_can_access_metric(metric) is False


@pytest.mark.parametrize(
    ("viz_type", "expected"),
    [
        ("chart", "fa fa-line-chart"),
        ("table", "fa fa-table"),
        ("card", "fa fa-calculator"),
        ("progress", "fa fa-tasks"),
        ("unknown", "fa fa-question"),
        (None, "fa fa-question"),
    ],
)
def test_bs_get_viz_icon(viz_type: str, expected: str) -> None:
    assert helpers.bs_get_viz_icon(viz_type) == expected


@pytest.mark.parametrize(
    ("viz_type", "expected"),
    [
        ("chart", "Chart"),
        ("table", "Table"),
        ("card", "Card"),
        ("progress", "Progress"),
        ("custom", "custom"),
    ],
)
def test_bs_get_viz_label(viz_type: str, expected: str) -> None:
    assert helpers.bs_get_viz_label(viz_type) == expected


@pytest.mark.usefixtures("with_request_context")
def test_bs_get_embed_code_contains_url() -> None:
    snippet = helpers.bs_get_embed_code("dataset_count", width="800", height="600")
    assert 'width="800"' in snippet
    assert 'height="600"' in snippet
    assert "dataset_count" in snippet
    assert snippet.startswith("<iframe")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (512, "512.00 B"),
        (2048, "2.00 KB"),
        (5 * 1024**2, "5.00 MB"),
        (3 * 1024**3, "3.00 GB"),
        (1024**4, "1.00 TB"),
        (1024**5, "1.00 PB"),
    ],
)
def test_bs_format_bytes(value: float, expected: str) -> None:
    assert helpers.bs_format_bytes(value) == expected
