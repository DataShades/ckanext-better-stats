from __future__ import annotations

from typing import Any

import pytest
from flask_login import encode_cookie  # pyright: ignore[reportUnknownVariableType]
from playwright.sync_api import BrowserContext, Page, expect

from ckan import types

expect.set_options(timeout=1000)


@pytest.fixture(autouse=True)
def page_timeout_(page: Page):
    """Reduce locator's timeout from 30s to 5s."""
    page.set_default_timeout(5000)


@pytest.fixture
def browser_context_args(browser_context_args: dict[str, Any], ckan_config: dict[str, Any]):
    """Modify playwright's standard configuration of browser's context."""
    browser_context_args["base_url"] = ckan_config["ckan.site_url"]
    return browser_context_args


@pytest.fixture
def token_login(api_token_factory: Any, page: Page):
    """Provides a function for authentication using API token.

    Usage:
        def test_example(page: Page, token_login):
            token_login("myuser")

    This will set the Authorization header for subsequent requests made by the page. To
    log out, call token_login with `None` or empty string, e.g., `token_login(None)`.
    """

    def authenticator(user: str | dict[str, Any], _page: Page | None = None):
        if _page is None:
            _page = page

        if isinstance(user, dict):
            user = user["name"]

        token: str = api_token_factory(user=user)["token"] if user else ""

        _page.set_extra_http_headers({"Authorization": token})

    return authenticator


@pytest.fixture
def login(page: Page, context: BrowserContext, ckan_config: types.FixtureCkanConfig, with_request_context: Any):
    """Provides a function for authentication by setting the remember cookie.

    Usage:
        def test_example(page: Page, login):
            login("testuser")
            page.goto("http://example.com/protected")

    This will set the remember cookie for 'testuser', allowing access to protected pages. To
    log out, call login with `None` or empty string, e.g., `login(None)`.
    """

    def authenticator(user: str | dict[str, Any], _page: Page | None = None):
        if _page is None:
            _page = page

        if isinstance(user, dict):
            user = user["name"]

        key = ckan_config["REMEMBER_COOKIE_NAME"]
        url = ckan_config["ckan.site_url"]

        if user:
            context.clear_cookies()
            context.add_cookies([{"name": key, "value": encode_cookie(user), "url": url}])
        else:
            context.clear_cookies()

    return authenticator


@pytest.fixture
def wait_for_ckan(page: Page):
    """Wait JS initialization before processing with page testing."""

    def waiter(_page: Page | None = None):
        if _page is None:
            _page = page

        page.wait_for_function("() => window.ckan && window.ckan.SITE_ROOT")

    return waiter


@pytest.fixture
def goto(wait_for_ckan: Any, page: Page):
    """Page transition with autowait for CKAN initialization."""

    def switcher(url: str, _page: Page | None = None, **kwargs: Any):
        if _page is None:
            _page = page

        result = page.goto(url, **kwargs)
        wait_for_ckan(page)
        return result

    return switcher
