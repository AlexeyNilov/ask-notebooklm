from pathlib import Path

import pytest

from ask_notebooklm.config import ConfigError
from ask_notebooklm.login_service import LoginResult, LoginStatus
from ask_notebooklm.notebooklm_client import AuthRequiredError
from ask_notebooklm.server import build_server


class FakeLoginService:
    def __init__(self, result: LoginResult) -> None:
        self.result = result
        self.calls = 0

    def login(self) -> LoginResult:
        self.calls += 1
        return self.result


class FakeAskService:
    def __init__(self, answer: str | Exception) -> None:
        self.answer = answer
        self.questions: list[str] = []

    async def ask(self, question: str) -> str:
        self.questions.append(question)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


@pytest.mark.anyio
async def test_login_tool_calls_login_service():
    login_service = FakeLoginService(LoginResult(LoginStatus.REUSED, Path("state.json")))
    server = build_server(login_service=login_service, ask_service=FakeAskService("unused"))

    _, structured = await server.call_tool("login", {})

    assert login_service.calls == 1
    assert structured["result"] == "NotebookLM session reused from state.json."


@pytest.mark.anyio
async def test_ask_tool_calls_ask_service_with_question():
    ask_service = FakeAskService("answer text")
    server = build_server(
        login_service=FakeLoginService(LoginResult(LoginStatus.REUSED, Path("state.json"))),
        ask_service=ask_service,
    )

    _, structured = await server.call_tool("ask", {"question": "What matters?"})

    assert ask_service.questions == ["What matters?"]
    assert structured["result"] == "answer text"


@pytest.mark.anyio
async def test_ask_tool_returns_reauthentication_message_for_expired_session():
    ask_service = FakeAskService(
        AuthRequiredError("NotebookLM session expired. Run the login tool.")
    )
    server = build_server(
        login_service=FakeLoginService(LoginResult(LoginStatus.REUSED, Path("state.json"))),
        ask_service=ask_service,
    )

    _, structured = await server.call_tool("ask", {"question": "What matters?"})

    assert structured["result"] == "NotebookLM session expired. Run the login tool."


@pytest.mark.anyio
async def test_ask_tool_returns_configuration_message_for_missing_notebook_id():
    ask_service = FakeAskService(
        ConfigError("NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID must be set in .env.")
    )
    server = build_server(
        login_service=FakeLoginService(LoginResult(LoginStatus.REUSED, Path("state.json"))),
        ask_service=ask_service,
    )

    _, structured = await server.call_tool("ask", {"question": "What matters?"})

    assert structured["result"] == "NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID must be set in .env."
