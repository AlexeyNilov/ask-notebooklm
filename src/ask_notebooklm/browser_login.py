from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, sync_playwright


NOTEBOOKLM_URL = "https://notebooklm.google.com/"
GOOGLE_AUTH_COOKIE_NAMES = {"__Secure-1PSID", "__Secure-3PSID", "SID", "HSID", "SSID"}


class PlaywrightBrowserSessionCapture:
    def __init__(
        self,
        profile_dir: Path | str,
        login_url: str = NOTEBOOKLM_URL,
        timeout_seconds: int = 180,
    ) -> None:
        self.profile_dir = Path(profile_dir)
        self.login_url = login_url
        self.timeout_seconds = timeout_seconds

    def capture(self) -> dict[str, Any]:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
            )
            return capture_storage_state(context, self.login_url, self.timeout_seconds)


def capture_storage_state(context: BrowserContext, login_url: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        page = context.new_page()
        page.goto(login_url)
        wait_for_google_auth_cookie(context, page, timeout_seconds)
        return context.storage_state()
    finally:
        context.close()


def wait_for_google_auth_cookie(context: BrowserContext, page: Page, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if has_google_auth_cookie(context.cookies()):
            return
        page.wait_for_timeout(1_000)
    raise TimeoutError("Timed out waiting for NotebookLM browser login.")


def has_google_auth_cookie(cookies: list[dict[str, Any]]) -> bool:
    return any(is_google_auth_cookie(cookie) for cookie in cookies)


def is_google_auth_cookie(cookie: dict[str, Any]) -> bool:
    domain = str(cookie.get("domain", ""))
    name = str(cookie.get("name", ""))
    return domain.endswith(".google.com") and name in GOOGLE_AUTH_COOKIE_NAMES
