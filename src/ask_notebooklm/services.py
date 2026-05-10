from __future__ import annotations

from collections.abc import Awaitable, Callable
from inspect import isawaitable
from pathlib import Path
from typing import Any, Protocol

import httpx

from ask_notebooklm.browser_login import PlaywrightBrowserSessionCapture
from ask_notebooklm.config import AppConfig, load_config
from ask_notebooklm.login_service import LoginResult, LoginService
from ask_notebooklm.notebooklm_client import AuthRequiredError, NotebookLMAskClient
from ask_notebooklm.session_store import (
    LoadedSession,
    SessionState,
    SessionStore,
    default_storage_path,
)


class LoginServiceProtocol(Protocol):
    def login(self) -> LoginResult:
        raise NotImplementedError


class AskServiceProtocol(Protocol):
    async def ask(self, question: str) -> str:
        raise NotImplementedError


class SessionStoreProtocol(Protocol):
    def load(self) -> LoadedSession:
        raise NotImplementedError


class NotebookClientProtocol(Protocol):
    async def ask(self, notebook_id: str, question: str) -> Any:
        raise NotImplementedError


ConfigLoader = Callable[[], AppConfig]
ClientFactory = Callable[[dict[str, Any]], NotebookClientProtocol | Awaitable[NotebookClientProtocol]]


class AskService:
    def __init__(
        self,
        config_loader: ConfigLoader = load_config,
        session_store: SessionStoreProtocol | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self.config_loader = config_loader
        self.session_store = session_store or SessionStore.default()
        self.client_factory = client_factory

    async def ask(self, question: str) -> str:
        config = self.config_loader()
        session = self.session_store.load()
        storage_state = require_valid_storage_state(session)
        if self.client_factory is None:
            return await ask_with_default_client(storage_state, config.read_only_notebook_id, question)
        client = await resolve_client(self.client_factory(storage_state))
        result = await client.ask(config.read_only_notebook_id, question)
        return str(result.answer)


def require_valid_storage_state(session: LoadedSession) -> dict[str, Any]:
    if session.state == SessionState.VALID and session.storage_state is not None:
        return session.storage_state
    raise AuthRequiredError(f"NotebookLM session is {session.state.value}. Run the login tool.")


async def resolve_client(
    client_or_awaitable: NotebookClientProtocol | Awaitable[NotebookClientProtocol],
) -> NotebookClientProtocol:
    if isawaitable(client_or_awaitable):
        return await client_or_awaitable
    return client_or_awaitable


async def ask_with_default_client(storage_state: dict[str, Any], notebook_id: str, question: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        client = await NotebookLMAskClient.from_storage_state(http_client, storage_state)
        result = await client.ask(notebook_id, question)
        return result.answer


def build_default_login_service() -> LoginService:
    storage_path = default_storage_path()
    profile_path = default_browser_profile_path(storage_path)
    return LoginService(storage_path, PlaywrightBrowserSessionCapture(profile_path))


def build_default_ask_service() -> AskService:
    return AskService()


def default_browser_profile_path(storage_path: Path) -> Path:
    return storage_path.parent / "browser_profile"
