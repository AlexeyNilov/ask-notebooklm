# TODO

## Assumptions

* Build a new local stdio MCP server in this repository.
* Treat `notebooklm-py` as read-only reference material.
* Keep the first release limited to login/session reuse and asking questions.
* Configure the target NotebookLM notebook ID in a local `.env` file using
  `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`.
* Reimplement only the tiny NotebookLM RPC surface needed by this project.
* Distribute the application as a pip-installable Python package.
* Keep all NotebookLM API usage read-only.

## Implementation plan

1. Scaffold package metadata.
   * Add `pyproject.toml` for package metadata and build configuration.
   * Use plain `pip` workflows for installation and development.
   * Define the package name, version, Python version requirement, dependencies,
     and console script entry point.
   * Record packaging decisions in `doc/decisions.md`.

2. Scaffold the Python project.
   * Add package layout for the MCP server, NotebookLM client, session storage,
     configuration, and CLI entry point.
   * Add test framework configuration.
   * Add `.env.example` with `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`.
   * Confirm `.env` is ignored.
   * Add development commands to `README.md`.

3. Define MCP tool schemas test-first.
   * Add a failing test that verifies the server exposes a login tool.
   * Add a failing test that verifies the server exposes an ask tool.
   * Add a failing test that verifies the server exposes no write-oriented
     NotebookLM tools.
   * Add a failing test that verifies tool errors are returned through MCP
     results, not stdout.

4. Implement session storage test-first.
   * Add tests for resolving the default storage path.
   * Add tests for reading a valid stored session.
   * Add tests for missing, invalid, and expired session states.
   * Implement storage without logging sensitive session contents.

5. Implement login flow test-first.
   * Add tests around the login orchestration boundary using injected browser
     automation.
   * Implement browser login/session capture behind a small interface.
   * Verify repeated login calls reuse or replace stored session data
     predictably.

6. Implement NotebookLM ask client test-first.
   * Add tests for loading `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID` from `.env`.
   * Add tests for validating notebook ID configuration and question input.
   * Add tests for successful answer extraction from a representative response.
   * Add tests for authentication failure, rate limiting, timeout, and malformed
     response handling.
   * Implement the smallest direct RPC client surface needed by the MCP ask
     tool.

7. Wire MCP tools to application services.
   * Add tests proving `login` calls the login service and returns clear status.
   * Add tests proving `ask` loads configuration and session state, calls
     NotebookLM, and returns the answer text.
   * Add tests proving expired sessions produce a re-authentication message.

8. Add local integration checks.
   * Run the MCP server over stdio locally.
   * Verify Codex can discover the tools.
   * Verify a real login flow on a local machine.
   * Verify asking a real existing notebook works.

9. Document usage.
   * Add install/setup instructions to `README.md`.
   * Document `pip install .` usage.
   * Add Codex MCP configuration example.
   * Document required `.env` settings, including
     `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`.
   * Document where session data is stored.
   * Document the read-only NotebookLM API boundary.
   * Document limitations and the risk of undocumented NotebookLM APIs changing.

10. Prepare the first usable release.
    * Run the full automated test suite.
    * Review logs and error messages for leaked credentials.
    * Confirm `.env` and session files are ignored.
    * Tag the minimal supported behavior in documentation.
