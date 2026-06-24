from pathlib import Path

import pytest

from hw6_race.shared.config import ConfigError, GameConfig, load_config


def test_load_config_reads_valid_file(tmp_config_file: Path) -> None:
    config = load_config(tmp_config_file)
    assert config.grid_size == (5, 5)
    assert config.max_moves == 25
    assert config.num_games == 6
    assert config.max_barriers == 5
    assert config.scoring == {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def test_load_config_missing_file_raises_config_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.json"
    with pytest.raises(ConfigError, match="not found"):
        load_config(missing_path)


def test_load_config_malformed_json_raises_config_error(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(bad_path)


def test_load_config_missing_required_key_raises_config_error(tmp_path: Path) -> None:
    incomplete_path = tmp_path / "incomplete.json"
    incomplete_path.write_text('{"grid_size": [5, 5]}', encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required keys"):
        load_config(incomplete_path)


def test_game_config_raw_returns_underlying_dict(sample_config_data: dict) -> None:
    config = GameConfig(sample_config_data)
    assert config.raw == sample_config_data
