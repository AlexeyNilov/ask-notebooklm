from pathlib import Path

import pytest

from ask_notebooklm.config import AppConfig
from ask_notebooklm.notebooklm_client import AuthRequiredError
from ask_notebooklm.services import AskService
from ask_notebooklm.session_store import LoadedSession, SessionState


class FakeSessionStore:
    def __init__(self, session: LoadedSession) -> None:
        self.session = session

    def load(self) -> LoadedSession:
        return self.session


class FakeNotebookClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    async def ask(self, notebook_id: str, question: str):
        self.calls.append((notebook_id, question))
        return FakeAskResult(self.answer)


class FakeAskResult:
    def __init__(self, answer: str) -> None:
        self.answer = answer


@pytest.mark.anyio
async def test_ask_service_loads_config_session_and_calls_notebook_client():
    storage_state = {"cookies": [], "origins": []}
    notebook_client = FakeNotebookClient("answer text")

    service = AskService(
        config_loader=lambda: AppConfig(read_only_notebook_id="notebook-123"),
        session_store=FakeSessionStore(LoadedSession(SessionState.VALID, Path("state.json"), storage_state)),
        client_factory=lambda state: notebook_client,
    )

    answer = await service.ask("What matters?")

    assert answer == "answer text"
    assert notebook_client.calls == [("notebook-123", "What matters?")]


@pytest.mark.anyio
async def test_ask_service_reports_expired_session_before_notebook_request():
    notebook_client = FakeNotebookClient("unused")
    service = AskService(
        config_loader=lambda: AppConfig(read_only_notebook_id="notebook-123"),
        session_store=FakeSessionStore(LoadedSession(SessionState.EXPIRED, Path("state.json"))),
        client_factory=lambda state: notebook_client,
    )

    with pytest.raises(AuthRequiredError, match="login"):
        await service.ask("What matters?")

    assert notebook_client.calls == []
