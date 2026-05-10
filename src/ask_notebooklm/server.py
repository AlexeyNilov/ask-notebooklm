from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def build_server() -> FastMCP:
    server = FastMCP("ask-notebooklm")

    @server.tool(
        name="login",
        description="Capture or refresh the local NotebookLM browser session.",
        annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    )
    async def login() -> str:
        return "NotebookLM login is not implemented yet."

    @server.tool(
        name="ask",
        description="Ask a question against the configured read-only NotebookLM notebook.",
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    async def ask(question: str) -> str:
        _ = question
        return "NotebookLM ask is not implemented yet."

    return server
