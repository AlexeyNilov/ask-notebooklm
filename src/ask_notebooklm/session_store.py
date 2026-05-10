from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SessionState(str, Enum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    EXPIRED = "expired"


@dataclass(frozen=True)
class LoadedSession:
    state: SessionState
    path: Path
    storage_state: dict[str, Any] | None = field(default=None, repr=False)


class SessionStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @classmethod
    def default(cls) -> SessionStore:
        return cls(default_storage_path())

    def load(self, now: float | None = None) -> LoadedSession:
        if not self.path.exists():
            return LoadedSession(SessionState.MISSING, self.path)

        try:
            storage_state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return LoadedSession(SessionState.INVALID, self.path)

        if not is_storage_state(storage_state):
            return LoadedSession(SessionState.INVALID, self.path)
        if is_expired(storage_state, now or time.time()):
            return LoadedSession(SessionState.EXPIRED, self.path)
        return LoadedSession(SessionState.VALID, self.path, storage_state)

    def save(self, storage_state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(storage_state, indent=2, sort_keys=True)
        self.path.write_text(f"{payload}\n", encoding="utf-8")


def default_storage_path() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base) / "ask-notebooklm" / "storage_state.json"
    return Path.home() / ".ask-notebooklm" / "storage_state.json"


def is_storage_state(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    cookies = value.get("cookies")
    origins = value.get("origins")
    return isinstance(cookies, list) and isinstance(origins, list)


def is_expired(storage_state: dict[str, Any], now: float) -> bool:
    persistent_expiries = cookie_expiries(storage_state)
    return bool(persistent_expiries) and all(expires <= now for expires in persistent_expiries)


def cookie_expiries(storage_state: dict[str, Any]) -> list[float]:
    expiries: list[float] = []
    for cookie in storage_state["cookies"]:
        if not isinstance(cookie, dict):
            continue
        expires = cookie.get("expires")
        if isinstance(expires, int | float) and expires > 0:
            expiries.append(float(expires))
    return expiries
