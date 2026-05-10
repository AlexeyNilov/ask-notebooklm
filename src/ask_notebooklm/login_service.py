from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from ask_notebooklm.session_store import SessionState, SessionStore, is_expired, is_storage_state


class BrowserSessionCapture(Protocol):
    def capture(self) -> dict[str, Any]:
        raise NotImplementedError


class LoginStatus(str, Enum):
    REUSED = "reused"
    CAPTURED = "captured"


class LoginError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoginResult:
    status: LoginStatus
    session_path: Path


class LoginService:
    def __init__(self, storage_path: Path | str, browser_capture: BrowserSessionCapture) -> None:
        self.store = SessionStore(storage_path)
        self.browser_capture = browser_capture

    def login(self, force: bool = False, now: float | None = None) -> LoginResult:
        current_time = now or time.time()
        current_session = self.store.load(now=current_time)
        if not force and current_session.state == SessionState.VALID:
            return LoginResult(LoginStatus.REUSED, self.store.path)

        storage_state = self.browser_capture.capture()
        validate_captured_storage_state(storage_state, current_time)
        self.store.save(storage_state)
        return LoginResult(LoginStatus.CAPTURED, self.store.path)


def validate_captured_storage_state(storage_state: object, now: float) -> None:
    if not is_storage_state(storage_state):
        raise LoginError("Captured NotebookLM session storage is invalid.")
    if is_expired(storage_state, now):
        raise LoginError("Captured NotebookLM session storage is expired.")
