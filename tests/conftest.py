"""Shared pytest fixtures for the hw6_race test suite."""

import json
from pathlib import Path

import pytest

from hw6_race.shared.config import GameConfig


@pytest.fixture
def sample_config_data() -> dict:
    """A minimal, valid game config dict matching config/setup.json's schema."""
    return {
        "version": "1.00",
        "grid_size": [5, 5],
        "max_moves": 25,
        "num_games": 6,
        "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    }


@pytest.fixture
def sample_game_config(sample_config_data: dict) -> GameConfig:
    return GameConfig(sample_config_data)


@pytest.fixture
def tmp_config_file(tmp_path: Path, sample_config_data: dict) -> Path:
    """Write sample_config_data to a temp file and return its path."""
    config_path = tmp_path / "setup.json"
    config_path.write_text(json.dumps(sample_config_data), encoding="utf-8")
    return config_path


@pytest.fixture
def sample_rate_limits_data() -> dict:
    """A minimal, valid rate-limit config dict matching config/rate_limits.json's schema."""
    return {
        "version": "1.00",
        "services": {
            "default": {
                "requests_per_minute": 30,
                "requests_per_hour": 500,
                "concurrent_max": 5,
                "retry_after_seconds": 30,
                "max_retries": 3,
            }
        },
    }


@pytest.fixture
def tmp_rate_limits_file(tmp_path: Path, sample_rate_limits_data: dict) -> Path:
    rate_limits_path = tmp_path / "rate_limits.json"
    rate_limits_path.write_text(json.dumps(sample_rate_limits_data), encoding="utf-8")
    return rate_limits_path


class FakeClock:
    """Deterministic, manually-advanced clock for rate-limit tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock()


class FakeLLMClient:
    """Test double for LLMClient — returns canned responses or raises, deterministically."""

    def __init__(self, responses: list[str] | None = None, raises: Exception | None = None) -> None:
        self._responses = list(responses or [])
        self._raises = raises
        self.prompts_seen: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts_seen.append(prompt)
        if self._raises is not None:
            raise self._raises
        if self._responses:
            return self._responses.pop(0)
        return ""


@pytest.fixture
def fake_llm_client_factory():
    return FakeLLMClient
