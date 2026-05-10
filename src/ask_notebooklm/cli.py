from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import Literal, Protocol

from ask_notebooklm.server import build_server


class RunnableServer(Protocol):
    def run(
        self,
        transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
        mount_path: str | None = None,
    ) -> None:
        raise NotImplementedError


ServerFactory = Callable[[], RunnableServer]


def default_server_factory() -> RunnableServer:
    return build_server()


def main(
    argv: Sequence[str] | None = None,
    server_factory: ServerFactory = default_server_factory,
) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if wants_help(args):
        sys.stdout.write(help_text())
        return 0

    try:
        server_factory().run("stdio")
    except Exception as error:
        sys.stderr.write(f"ask-notebooklm failed to start: {error}\n")
        return 1
    return 0


def wants_help(args: Sequence[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in args)


def help_text() -> str:
    return (
        "ask-notebooklm\n\n"
        "Runs the read-only NotebookLM stdio MCP server.\n\n"
        "Usage:\n"
        "  ask-notebooklm\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
