# ask-notebooklm

Read-only stdio MCP server for asking questions against a configured
Google NotebookLM notebook from Codex.

## Scope

The first release is intentionally small:

* run locally as a stdio MCP server
* capture and reuse a local NotebookLM browser session
* ask questions against one configured NotebookLM notebook
* avoid all NotebookLM write operations

The server must not create notebooks, upload sources, edit sources, delete data,
or generate NotebookLM artifacts.

## Configuration

Create a local `.env` file:

```text
NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID=<your notebook id>
```

`.env` is local-only and must not be committed.

Session data is stored outside the repository by default:

* Windows: `%LOCALAPPDATA%\ask-notebooklm\storage_state.json`
* Other platforms: `~/.ask-notebooklm/storage_state.json`

Tests and advanced local setups can pass an explicit session storage path.

Login capture opens a local Chromium browser with a persistent profile and waits
for Google authentication cookies before saving session state. It does not ask
for credentials in the terminal.

## MCP tools

The stdio MCP server exposes only:

* `login`: capture or refresh the local NotebookLM browser session
* `ask`: ask a question against `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`

No write-oriented NotebookLM tools are exposed.

## NotebookLM API boundary

The ask client uses NotebookLM's internal streaming question endpoint directly.
It reads cookies from the captured browser session, fetches NotebookLM page
tokens, sends a question to the configured notebook, and parses the streamed
answer response.

This endpoint is undocumented and may change without notice.

## Development

Create a virtual environment with Python 3.10 or newer, then install the package
in editable mode:

```powershell
pip install -e ".[dev]"
```

Run tests:

```powershell
python -m pytest
```

Run the console entry point:

```powershell
ask-notebooklm
```

The command starts the stdio MCP server. Do not wrap it with scripts that write
to stdout, because stdout is reserved for MCP protocol messages.

## Codex MCP configuration

Configure Codex to run the installed console command from this project
environment:

```toml
[mcp_servers.ask_notebooklm]
command = "C:\\an\\git\\ask-notebooklm\\.venv\\Scripts\\ask-notebooklm.exe"
cwd = "C:\\an\\git\\ask-notebooklm"
```
