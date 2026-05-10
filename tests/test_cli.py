from ask_notebooklm.cli import main


class FakeServer:
    def __init__(self) -> None:
        self.transports: list[str] = []

    def run(self, transport: str = "stdio") -> None:
        self.transports.append(transport)


def test_main_runs_mcp_server_over_stdio_without_stdout(capsys):
    server = FakeServer()

    exit_code = main([], server_factory=lambda: server)

    captured = capsys.readouterr()

    assert exit_code == 0
    assert server.transports == ["stdio"]
    assert captured.out == ""
    assert captured.err == ""


def test_main_prints_help_without_starting_server(capsys):
    server = FakeServer()

    exit_code = main(["--help"], server_factory=lambda: server)

    captured = capsys.readouterr()

    assert exit_code == 0
    assert server.transports == []
    assert "stdio MCP server" in captured.out


def test_main_reports_startup_error_to_stderr(capsys):
    def raise_error() -> FakeServer:
        raise RuntimeError("boom")

    exit_code = main([], server_factory=raise_error)

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "boom" in captured.err
