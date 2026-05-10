from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

CONFIG_NOTEBOOK_ID = "NOTEBOOKLM_READ_ONLY_NOTEBOOK_ID"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppConfig:
    read_only_notebook_id: str


def load_config(env_path: Path | str = ".env") -> AppConfig:
    values = dotenv_values(env_path)
    notebook_id = os.getenv(CONFIG_NOTEBOOK_ID) or values.get(CONFIG_NOTEBOOK_ID)
    if not notebook_id or not notebook_id.strip():
        raise ConfigError(f"{CONFIG_NOTEBOOK_ID} must be set in .env.")
    return AppConfig(read_only_notebook_id=notebook_id.strip())
