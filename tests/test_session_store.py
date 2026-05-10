import json
from pathlib import Path

from ask_notebooklm.session_store import SessionState, SessionStore


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


def test_default_storage_path_is_outside_project_source(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    store = SessionStore.default()

    assert store.path == tmp_path / "ask-notebooklm" / "storage_state.json"


def test_explicit_storage_path_is_supported(tmp_path):
    path = tmp_path / "custom-state.json"

    store = SessionStore(path)

    assert store.path == path


def test_load_returns_valid_session_for_storage_state_with_unexpired_cookie(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state()), encoding="utf-8")

    session = SessionStore(path).load(now=1_700_000_000)

    assert session.state == SessionState.VALID
    assert session.path == path


def test_load_returns_missing_when_storage_file_does_not_exist(tmp_path):
    session = SessionStore(tmp_path / "missing.json").load()

    assert session.state == SessionState.MISSING


def test_load_returns_invalid_for_malformed_json(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text("{", encoding="utf-8")

    session = SessionStore(path).load()

    assert session.state == SessionState.INVALID


def test_load_returns_invalid_for_unexpected_storage_shape(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps({"cookies": "not-a-list"}), encoding="utf-8")

    session = SessionStore(path).load()

    assert session.state == SessionState.INVALID


def test_load_returns_expired_when_all_persistent_cookies_are_expired(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state(expires=1_600_000_000)), encoding="utf-8")

    session = SessionStore(path).load(now=1_700_000_000)

    assert session.state == SessionState.EXPIRED


def test_save_persists_storage_state_and_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "storage_state.json"

    SessionStore(path).save(storage_state())

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["cookies"][0]["name"] == "__Secure-1PSID"


def test_loaded_session_repr_does_not_include_cookie_values(tmp_path):
    path = tmp_path / "storage_state.json"
    path.write_text(json.dumps(storage_state()), encoding="utf-8")

    session = SessionStore(path).load()

    assert "secret-cookie-value" not in repr(session)
