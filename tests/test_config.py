import pytest

from ask_notebooklm.config import CONFIG_NOTEBOOK_ID, ConfigError, load_config


def test_load_config_reads_notebook_id_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv(CONFIG_NOTEBOOK_ID, raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text(f"{CONFIG_NOTEBOOK_ID}=abc123\n", encoding="utf-8")

    config = load_config(env_path)

    assert config.read_only_notebook_id == "abc123"


def test_load_config_prefers_process_environment(monkeypatch, tmp_path):
    monkeypatch.setenv(CONFIG_NOTEBOOK_ID, "from-process")
    env_path = tmp_path / ".env"
    env_path.write_text(f"{CONFIG_NOTEBOOK_ID}=from-file\n", encoding="utf-8")

    config = load_config(env_path)

    assert config.read_only_notebook_id == "from-process"


def test_load_config_rejects_missing_notebook_id(monkeypatch, tmp_path):
    monkeypatch.delenv(CONFIG_NOTEBOOK_ID, raising=False)

    with pytest.raises(ConfigError, match=CONFIG_NOTEBOOK_ID):
        load_config(tmp_path / ".env")
