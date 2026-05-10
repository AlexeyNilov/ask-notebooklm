import subprocess
import sys
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
CONSOLE_SCRIPT = ROOT / ".venv" / "Scripts" / "ask-notebooklm.exe"


def test_installed_console_script_prints_help_without_stderr():
    completed = subprocess.run(
        [str(CONSOLE_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "stdio MCP server" in completed.stdout
    assert completed.stderr == ""


@pytest.mark.anyio
async def test_stdio_server_exposes_read_only_tools():
    server_params = StdioServerParameters(
        command=str(PYTHON),
        args=["-m", "ask_notebooklm.cli"],
        cwd=ROOT,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

    tool_names = {tool.name for tool in tools.tools}

    assert tool_names == {"ask", "login"}
