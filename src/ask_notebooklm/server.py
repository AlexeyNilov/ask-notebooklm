from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ask_notebooklm.config import ConfigError
from ask_notebooklm.login_service import LoginResult, LoginStatus
from ask_notebooklm.notebooklm_client import (
    AuthRequiredError,
    MalformedResponseError,
    NotebookLMError,
    NotebookLMTransientError,
    NotebookLMValidationError,
)
from ask_notebooklm.services import (
    AskServiceProtocol,
    LoginServiceProtocol,
    build_default_ask_service,
    build_default_login_service,
)


def build_server(
    login_service: LoginServiceProtocol | None = None,
    ask_service: AskServiceProtocol | None = None,
) -> FastMCP:
    login_service = login_service or build_default_login_service()
    ask_service = ask_service or build_default_ask_service()
    server = FastMCP("ask-notebooklm")

    @server.tool(
        name="login",
        description="Capture or refresh the local NotebookLM browser session.",
        annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    )
    async def login() -> str:
        return format_login_result(login_service.login())

    @server.tool(
        name="ask",
        description="Ask a question against the configured read-only NotebookLM notebook.",
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    async def ask(question: str) -> str:
        try:
            return await ask_service.ask(question)
        except KNOWN_USER_ERRORS as error:
            return str(error)

    return server


KNOWN_USER_ERRORS = (
    AuthRequiredError,
    ConfigError,
    MalformedResponseError,
    NotebookLMError,
    NotebookLMTransientError,
    NotebookLMValidationError,
)


def format_login_result(result: LoginResult) -> str:
    if result.status == LoginStatus.REUSED:
        return f"NotebookLM session reused from {result.session_path}."
    return f"NotebookLM session captured at {result.session_path}."
