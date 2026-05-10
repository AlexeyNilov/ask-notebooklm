# Decisions

## Why record decisions

Write down key development decisions while the context is fresh. A short note today can save hours later by explaining what was chosen, what was rejected, and why the trade-off made sense at the time.

## Guidance

Use a lightweight Architecture Decision Record (ADR) style:

* Record decisions that affect architecture, data flow, public APIs, dependencies, deployment, security, or long-term maintenance.
* Write the decision when it is made, not after the context has faded.
* Prefer short entries that explain the context, decision, alternatives, and consequences.
* Include enough reasoning for a future maintainer to understand the trade-off.
* Do not document every small implementation detail; focus on choices that would be costly or confusing to rediscover.
* Update or supersede earlier decisions instead of silently rewriting history.

## Entry template

```markdown
### YYYY-MM-DD: Decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What problem, constraint, or trade-off led to this decision?

**Decision:** What was chosen?

**Alternatives considered:** What other options were rejected, and why?

**Consequences:** What becomes easier, harder, riskier, or more constrained?
```

## Actual decisions

### 2026-05-10: Reimplement minimal NotebookLM RPC surface

**Status:** Accepted

**Context:** The project needs only login/session reuse and asking questions from
Codex through a local stdio MCP server. `notebooklm-py` provides a broader API
and CLI, but using it as a runtime dependency would import more behavior,
interfaces, and dependency decisions than the first release needs.

**Decision:** Reimplement only the tiny NotebookLM RPC surface needed for this
project. Use `notebooklm-py` as read-only reference material for request shape,
session handling, and failure modes.

**Alternatives considered:** Wrap `notebooklm-py` directly as the NotebookLM
client. This would reduce initial reverse-engineering, but it would couple this
project's minimal MCP behavior to a larger external library and make it harder
to keep the public surface intentionally small.

**Consequences:** The first implementation can stay focused and dependency-light.
The project takes on responsibility for tracking any Google NotebookLM RPC
changes that affect login/session reuse or asking questions.

### 2026-05-10: Package with pyproject.toml and plain pip

**Status:** Accepted

**Context:** The project should be distributable as a Python package while
keeping the contributor workflow simple. The package needs a standard place for
metadata, runtime dependencies, build configuration, and a console entry point
that Codex can run as a stdio MCP server.

**Decision:** Use `pyproject.toml` for package metadata and build configuration.
Support installation with plain `pip`, starting with `pip install .` for local
use.

**Alternatives considered:** Adopt `uv` as the project workflow. `uv` would be
useful for faster environment management, but it is not required for the minimal
package distribution goal and would add a tool choice before the project needs
it.

**Consequences:** Users can install the server with familiar Python packaging
commands. The project still needs clear README instructions for creating a
virtual environment, installing the package, configuring `.env`, and pointing
Codex at the console entry point.

### 2026-05-10: Keep NotebookLM API use read-only

**Status:** Accepted

**Context:** The application is meant to let Codex ask questions against an
existing NotebookLM notebook. Write operations would add risk because the project
uses undocumented NotebookLM endpoints and because Codex tool calls should not
accidentally alter a user's notebooks or sources.

**Decision:** Limit the MCP server to read-only NotebookLM behavior. The target
notebook is configured with `NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID` in `.env`. The
server may authenticate, reuse sessions, validate access, and ask questions, but
it must not create notebooks, upload sources, edit sources, delete data, or
generate NotebookLM artifacts.

**Alternatives considered:** Expose a broader NotebookLM automation surface.
That may be useful later, but it conflicts with the minimal first release and
increases the chance of accidental data changes.

**Consequences:** The MCP surface stays small and safer for Codex use. Future
write-capable features must be treated as a separate design decision, with new
requirements, tests, documentation, and probably explicit tool names that make
the write behavior impossible to miss.
