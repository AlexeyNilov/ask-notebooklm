import asyncio

from ask_notebooklm.server import build_server


def list_tool_defs():
    server = build_server()
    return asyncio.run(server.list_tools())


def test_server_exposes_login_and_ask_tools():
    tool_names = {tool.name for tool in list_tool_defs()}

    assert tool_names == {"ask", "login"}


def test_ask_tool_accepts_question_without_notebook_id():
    tools_by_name = {tool.name: tool for tool in list_tool_defs()}

    ask_schema = tools_by_name["ask"].inputSchema

    assert ask_schema["required"] == ["question"]
    assert "question" in ask_schema["properties"]
    assert "notebook_id" not in ask_schema["properties"]


def test_server_exposes_no_write_or_generation_tools():
    write_terms = {
        "add",
        "create",
        "delete",
        "edit",
        "generate",
        "remove",
        "source",
        "upload",
    }

    tool_names = {tool.name for tool in list_tool_defs()}

    assert not tool_names.intersection(write_terms)
