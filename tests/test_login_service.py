import json

import pytest

from ask_notebooklm.login_service import LoginError, LoginService, LoginStatus


def storage_state(expires: int = 4_102_444_800) -> dict:
    return {
        "cookies": [
            {
                "name": "__Secure-1PSID",
                "value": "secret-cookie-value",
                "domain": ".google.com",
                "path": "/",
                "expires": expires,
            }
        ],
        "origins": [],
    }


class FakeBrowserCapture:
    def __init__(self, captured_state: dict | None = None) -> None:
        self.captured_state = captured_state or storage_state()
        self.calls = 0

    def capture(self) -> dict:
        self.calls += 1
        return self.captured_state


def test_login_reuses_valid_stored_session_without_browser_capture(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state()), encoding="utf-8")
    browser = FakeBrowserCapture()

    result = LoginService(path, browser).login(now=1_700_000_000)

    assert result.status == LoginStatus.REUSED
    assert result.session_path == path
    assert browser.calls == 0


def test_login_captures_session_when_storage_is_missing(tmp_path):
    path = tmp_path / "storage_state.json"
    browser = FakeBrowserCapture(storage_state())

    result = LoginService(path, browser).login(now=1_700_000_000)

    assert result.status == LoginStatus.CAPTURED
    assert json.loads(path.read_text(encoding="utf-8")) == storage_state()
    assert browser.calls == 1


def test_login_replaces_expired_stored_session(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state(expires=1_600_000_000)), encoding="utf-8")
    browser = FakeBrowserCapture(storage_state(expires=4_102_444_800))

    result = LoginService(path, browser).login(now=1_700_000_000)

    assert result.status == LoginStatus.CAPTURED
    assert json.loads(path.read_text(encoding="utf-8")) == storage_state()
    assert browser.calls == 1


def test_forced_login_refreshes_valid_stored_session(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state(expires=3_000_000_000)), encoding="utf-8")
    browser = FakeBrowserCapture(storage_state(expires=4_102_444_800))

    result = LoginService(path, browser).login(force=True, now=1_700_000_000)

    assert result.status == LoginStatus.CAPTURED
    assert json.loads(path.read_text(encoding="utf-8")) == storage_state()
    assert browser.calls == 1


def test_login_rejects_captured_invalid_storage_state(tmp_path):
    path = tmp_path / "storage_state.json"
    browser = FakeBrowserCapture({"cookies": "not-a-list"})

    with pytest.raises(LoginError, match="invalid"):
        LoginService(path, browser).login()

    assert not path.exists()


def test_login_rejects_captured_expired_storage_state(tmp_path):
    path = tmp_path / "storage_state.json"
    browser = FakeBrowserCapture(storage_state(expires=1_600_000_000))

    with pytest.raises(LoginError, match="expired"):
        LoginService(path, browser).login(now=1_700_000_000)

    assert not path.exists()
