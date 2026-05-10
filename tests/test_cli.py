from ask_notebooklm.cli import main


def test_main_reports_not_implemented_without_stdout(capsys):
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "not implemented" in captured.err
