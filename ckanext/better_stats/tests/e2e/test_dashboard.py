from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.playwright
@pytest.mark.usefixtures("with_plugins")
class TestDashboard:
    def test_dashboard_renders(self, page: Page):
        """Dashboard loads and shows the metrics grid with default metrics."""
        page.goto("/better_stats/dashboard")

        grid = page.locator(".bstats-dashboard")
        expect(grid).to_be_visible()

        expect(grid.locator(".metric-title").get_by_text("Total Datasets", exact=True)).to_be_visible()
        expect(grid.locator(".metric-title").get_by_text("Datasets by Organization", exact=True)).to_be_visible()

    def test_dashboard_anonymous_has_no_settings_link(self, page: Page):
        """Anonymous users see the dashboard but no Settings button."""
        page.goto("/better_stats/dashboard")
        expect(page.locator(".bstats-toolbar a[href='/better_stats/settings']")).to_have_count(0)

    def test_dashboard_sysadmin_sees_settings_link(self, page: Page, sysadmin: dict[str, Any], login: Any):
        """Sysadmins see the Settings link in the dashboard toolbar."""
        login(sysadmin)
        page.goto("/better_stats/dashboard")
        expect(page.locator(".bstats-toolbar a[href='/better_stats/settings']")).to_be_visible()

    def test_dashboard_filter_pills_present(self, page: Page):
        """Group-filter pills include the always-on 'All' option."""
        page.goto("/better_stats/dashboard")
        expect(page.locator(".bstats-group-pill[data-group='all']")).to_be_visible()

    def test_export_metric_csv(self, page: Page):
        """Exporting a metric as CSV triggers a downloadable file."""
        page.goto("/better_stats/dashboard")
        with page.expect_download() as download_info:
            page.evaluate(
                "url => { window.location.href = url; }",
                "/better_stats/export/dataset_count?format=csv",
            )

        download = download_info.value
        assert download.suggested_filename.startswith("dataset_count_")
        assert download.suggested_filename.endswith(".csv")

    def test_export_unknown_metric_returns_404(self, page: Page):
        """Exporting a metric that does not exist returns a 404 JSON response."""
        response = page.request.get("/better_stats/export/no_such_metric?format=csv")
        assert response.status == 404

    def test_export_unsupported_format_returns_400(self, page: Page):
        """Requesting an unsupported export format returns 400."""
        response = page.request.get("/better_stats/export/dataset_count?format=pdf")
        assert response.status == 400
