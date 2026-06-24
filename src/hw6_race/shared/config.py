"""Config loading/validation (SG-C09). All game parameters come from here, never hard-coded."""

import json
from pathlib import Path
from typing import Any

from hw6_race.constants import DEFAULT_CONFIG_PATH

REQUIRED_KEYS = ("grid_size", "max_moves", "num_games", "max_barriers", "scoring")


class ConfigError(Exception):
    """Raised when the configuration file is missing, malformed, or incomplete.

    Input: a config file path. Output: none (exception). Setup: none.
    """


class GameConfig:
    """Typed view over `config/setup.json`.

    Input: path to a JSON config file (Setup data).
    Output: validated, attribute-accessible game parameters.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def grid_size(self) -> tuple[int, int]:
        size = self._data["grid_size"]
        return int(size[0]), int(size[1])

    @property
    def max_moves(self) -> int:
        return int(self._data["max_moves"])

    @property
    def num_games(self) -> int:
        return int(self._data["num_games"])

    @property
    def max_barriers(self) -> int:
        return int(self._data["max_barriers"])

    @property
    def scoring(self) -> dict[str, int]:
        return dict(self._data["scoring"])

    @property
    def raw(self) -> dict[str, Any]:
        return self._data


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> GameConfig:
    """Load and validate `config/setup.json`-style game configuration.

    Raises ConfigError on a missing file, invalid JSON, or missing required keys,
    rather than letting a raw KeyError/JSONDecodeError leak to callers.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file {config_path}: {exc}") from exc

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ConfigError(f"Config file {config_path} is missing required keys: {missing}")

    return GameConfig(data)
