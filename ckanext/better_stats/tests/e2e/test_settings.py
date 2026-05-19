from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.playwright
@pytest.mark.usefixtures("with_plugins")
class TestSettings:
    def test_settings_forbidden_for_anonymous(self, page: Page):
        """Anonymous users hit a 403 page when accessing settings."""
        response = page.goto("/better_stats/settings")
        assert response is not None
        assert response.status == 403

    def test_settings_forbidden_for_user(self, page: Page, user: dict[str, Any], login: Any):
        """Normal users hit a 403 page when accessing settings."""
        login(user)
        response = page.goto("/better_stats/settings")
        assert response is not None
        assert response.status == 403
        expect(page.locator(".module-content").get_by_text("Only sysadmins are allowed")).to_be_visible()

    def test_settings_allowed_for_sysadmin(self, page: Page, sysadmin: dict[str, Any], login: Any):
        """Sysadmins reach the settings dashboard with the metrics grid."""
        login(sysadmin)
        response = page.goto("/better_stats/settings")
        assert response is not None
        assert response.status == 200

        expect(page.get_by_role("heading", name="Better Stats — Settings")).to_be_visible()
        expect(page.locator("table.table-header tbody tr.metric-row").first).to_be_visible()
