from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from ckan.plugins import toolkit as tk
from ckan.tests.helpers import call_auth

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


@pytest.mark.usefixtures("with_plugins")
class TestViewDashboardAuth:
    def test_anonymous_user_view_dashboard(self, metric_factory: Callable[..., MetricBase]):
        """Anonymous users cannot view settings."""
        metric = metric_factory(name="x")

        assert (
            call_auth(
                "better_stats_view_dashboard",
                context={"user": None},
                metric_name=metric.name,
            )
            is True
        )

    def test_authenticated_user_view_dashboard(
        self,
        user: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Authenticated users cannot view dashboard."""
        metric = metric_factory(name="x")

        assert (
            call_auth(
                "better_stats_view_dashboard",
                context={"user": user["name"]},
                metric_name=metric.name,
            )
            is True
        )

    def test_sysadmin_user_view_dashboard(
        self,
        sysadmin: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Sysadmin users can view dashboard."""
        metric = metric_factory(name="x")

        assert (
            call_auth(
                "better_stats_view_dashboard",
                context={"user": sysadmin["name"]},
                metric_name=metric.name,
            )
            is True
        )


@pytest.mark.usefixtures("with_plugins")
class TestViewSettingsAuth:
    def test_anonymous_user_view_settings(self, metric_factory: Callable[..., MetricBase]):
        """Anonymous users cannot view settings."""
        metric = metric_factory(name="x")

        with pytest.raises(
            tk.NotAuthorized,
            match="Action better_stats_view_settings requires an authenticated user",
        ):
            call_auth(
                "better_stats_view_settings",
                context={"user": None},
                metric_name=metric.name,
            )

    def test_authenticated_user_view_settings(
        self,
        user: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Authenticated users cannot view settings."""
        metric = metric_factory(name="x")

        with pytest.raises(tk.NotAuthorized, match=tk._("Only sysadmins can view metric settings")):
            call_auth(
                "better_stats_view_settings",
                context={"user": user["name"]},
                metric_name=metric.name,
            )

    def test_sysadmin_user_view_settings(
        self,
        sysadmin: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Sysadmin users can view settings."""
        metric = metric_factory(name="x")

        assert (
            call_auth(
                "better_stats_view_settings",
                context={"user": sysadmin["name"]},
                metric_name=metric.name,
            )
            is True
        )


@pytest.mark.usefixtures("with_plugins")
class TestUpdateMetricAuth:
    def test_anonymous_user_update(self, metric_factory: Callable[..., MetricBase]):
        """Anonymous users cannot update metrics."""
        metric = metric_factory(name="x")

        with pytest.raises(
            tk.NotAuthorized,
            match="Action better_stats_update_metric requires an authenticated user",
        ):
            call_auth(
                "better_stats_update_metric",
                context={"user": None},
                metric_name=metric.name,
            )

    def test_authenticated_user_update(
        self,
        user: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Authenticated users cannot update metrics."""
        metric = metric_factory(name="x")

        with pytest.raises(tk.NotAuthorized, match=tk._("Only sysadmins can update metric settings")):
            call_auth(
                "better_stats_update_metric",
                context={"user": user["name"]},
                metric_name=metric.name,
            )

    def test_sysadmin_user_update(
        self,
        sysadmin: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
    ):
        """Sysadmin users can update metrics."""
        metric = metric_factory(name="x")

        assert (
            call_auth(
                "better_stats_update_metric",
                context={"user": sysadmin["name"]},
                metric_name=metric.name,
            )
            is True
        )


@pytest.mark.usefixtures("with_plugins")
class TestExportMetricAuth:
    @pytest.mark.parametrize(
        ("access_level", "expected"),
        [
            (const.AccessLevel.PUBLIC.value, True),
            (const.AccessLevel.AUTHENTICATED.value, False),
            (const.AccessLevel.ADMIN.value, False),
        ],
    )
    def test_anonymous_user_export(
        self,
        metric_factory: Callable[..., MetricBase],
        access_level: str,
        expected: bool,
    ):
        """Anonymous users cannot export metrics."""
        metric = metric_factory(name="x", access_level=access_level)

        if expected:
            return call_auth(
                "better_stats_export_metric",
                context={"user": None},
                metric_name=metric.name,
            )

        with pytest.raises(tk.NotAuthorized, match="Must be logged in to export this metric"):
            call_auth(
                "better_stats_export_metric",
                context={"user": None},
                metric_name=metric.name,
            )

    @pytest.mark.parametrize(
        ("access_level", "expected"),
        [
            (const.AccessLevel.PUBLIC.value, True),
            (const.AccessLevel.AUTHENTICATED.value, True),
            (const.AccessLevel.ADMIN.value, False),
        ],
    )
    def test_authenticated_user_export(
        self,
        user: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
        access_level: str,
        expected: bool,
    ):
        """Authenticated users cannot export metrics."""
        metric = metric_factory(name="x", access_level=access_level)

        if expected:
            return call_auth(
                "better_stats_export_metric",
                context={"user": user["name"]},
                metric_name=metric.name,
            )

        with pytest.raises(tk.NotAuthorized, match="Must be a sysadmin to export this metric"):
            call_auth(
                "better_stats_export_metric",
                context={"user": user["name"]},
                metric_name=metric.name,
            )

    @pytest.mark.parametrize(
        ("access_level", "expected"),
        [
            (const.AccessLevel.PUBLIC.value, True),
            (const.AccessLevel.AUTHENTICATED.value, True),
            (const.AccessLevel.ADMIN.value, True),
        ],
    )
    def test_sysadmin_user_export(
        self,
        sysadmin: dict[str, Any],
        metric_factory: Callable[..., MetricBase],
        access_level: str,
        expected: bool,
    ):
        """Sysadmin users can export metrics."""
        metric = metric_factory(name="x", access_level=access_level)

        assert (
            call_auth(
                "better_stats_export_metric",
                context={"user": sysadmin["name"]},
                metric_name=metric.name,
            )
            is expected
        )
