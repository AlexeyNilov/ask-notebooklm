# Requirements

## EARS (Easy Approach to Requirements Syntax)

Use the EARS structure for precise requirements:

> **While** `<optional precondition>`, **when** `<optional trigger>`, **the system shall** `<system response>`.

This helps ensure requirements are:

* Context-aware
* Trigger-based
* Action-specific

## Actual requirements

### Scope

This project shall provide a minimal stdio MCP server that lets Codex ask questions
against Google NotebookLM by reusing a local authenticated browser session.

The first version shall support only:

* login/session capture
* session reuse
* asking a question against an existing NotebookLM notebook

The first version shall not support notebook creation, source upload, source
management, artifact generation, audio/video generation, or multi-user hosted
operation.

### Assumptions

* Users run the MCP server locally on a trusted machine.
* Users already have a Google account with access to NotebookLM.
* Users already have at least one NotebookLM notebook available.
* The target NotebookLM notebook ID is configured in a local `.env` file as
  `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`.
* Authentication is stored locally and is not committed to git.
* NotebookLM access depends on undocumented Google endpoints and may break when
  Google changes its internal APIs.
* The project reimplements only the small NotebookLM RPC surface required for
  login/session reuse and asking questions.
* The project is distributed as a Python package installable with plain `pip`.
* All NotebookLM API use is read-only. The system must not create, update,
  delete, upload, or generate NotebookLM content.

### Functional requirements

#### MCP server

* **When** Codex starts the configured command, **the system shall** run as a
  stdio MCP server.
* **When** Codex lists available tools, **the system shall** expose a login tool
  and an ask tool.
* **When** Codex lists available tools, **the system shall not** expose tools
  that create notebooks, upload sources, modify sources, delete data, or
  generate NotebookLM artifacts.
* **When** an MCP request fails, **the system shall** return a structured MCP
  error message instead of writing user-facing errors to stdout.
* **While** running over stdio, **when** the system logs diagnostics, **the
  system shall** write logs to stderr or a configured log destination, not
  stdout.

#### Packaging and installation

* **When** the package is built, **the system shall** use `pyproject.toml` as the
  source of package metadata and build configuration.
* **When** a user installs the project with `pip install .`, **the system shall**
  install the MCP server and its runtime dependencies.
* **When** a user installs the package, **the system shall** provide a console
  entry point that starts the stdio MCP server.
* **When** package metadata is defined, **the system shall** include the package
  name, version, Python version requirement, runtime dependencies, and console
  script entry point.

#### Login and session reuse

* **When** a user invokes the login tool without a valid stored session, **the
  system shall** launch an interactive browser login flow.
* **When** the user completes browser login, **the system shall** persist the
  minimum session data required to authenticate future NotebookLM requests.
* **When** a valid stored session exists, **the system shall** reuse it without
  asking the user to log in again.
* **When** the stored session is expired or rejected, **the system shall** return
  a clear re-authentication error that instructs the user to run the login tool.
* **When** session data is stored, **the system shall** place it outside tracked
  source files by default.
* **When** session storage is configured, **the system shall** support an
  explicit storage path suitable for tests and advanced users.

#### Asking NotebookLM questions

* **When** Codex invokes the ask tool with a question, **the system shall** read
  the configured NotebookLM notebook ID from
  `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID`.
* **When** a configured notebook ID is available, **the system shall** send the
  question to that NotebookLM notebook using the stored authenticated session.
* **When** NotebookLM returns an answer, **the system shall** return the answer
  text to Codex as the MCP tool result.
* **When** the configured notebook ID is missing, empty, or invalid, **the
  system shall** return a configuration error before calling NotebookLM.
* **When** the question is missing or empty, **the system shall** return a
  validation error before calling NotebookLM.
* **When** NotebookLM returns citations or source references, **the system
  should** include them in the tool result if they can be represented without
  adding substantial complexity.
* **When** NotebookLM rate limits, rejects, or times out a request, **the system
  shall** return a clear transient failure message to Codex.

#### Read-only API boundary

* **When** the system calls NotebookLM APIs, **the system shall** limit calls to
  session validation and question-answering operations required for read-only
  access.
* **When** a potential implementation path requires creating notebooks,
  uploading sources, editing source content, deleting data, or generating
  artifacts, **the system shall** reject that path for the minimal release.
* **When** tests cover the NotebookLM client, **the system shall** include a test
  that prevents write-oriented RPC methods from being exposed through the MCP
  server.

### Non-functional requirements

* **When** implementation begins, **the system shall** be developed test-first
  for local validation, session decision logic, NotebookLM client behavior, and
  MCP tool behavior.
* **When** implementation integrates with NotebookLM, **the system shall** call
  the minimal undocumented NotebookLM RPC endpoints directly instead of wrapping
  `notebooklm-py` as a runtime dependency.
* **When** tests exercise NotebookLM behavior, **the system shall** mock external
  browser, network, and Google services rather than requiring live NotebookLM
  access.
* **When** code handles authentication data, **the system shall** avoid logging
  cookies, tokens, browser storage state, or account identifiers.
* **When** adding dependencies, **the system shall** justify each dependency by
  a concrete need in MCP transport, browser login, or HTTP/session handling.
* **When** public commands, MCP tool schemas, storage layout, or data flow
  change, **the system shall** update `README.md`.
