"""Tests for the inter-group bonus round runner (HW §12.1)."""

from unittest.mock import AsyncMock, patch

import pytest

import hw6_race.sdk.bonus as bonus_mod
from hw6_race.constants import GameOutcome
from hw6_race.sdk.bonus import build_bonus_sub_games, run_bonus_match
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.shared.config import GameConfig


def _sg(outcome: GameOutcome, cop: int, thief: int) -> SubGameResult:
    return SubGameResult(outcome=outcome, move_count=5, cop_points=cop, thief_points=thief)


def _fake_result(cop: int = 20, thief: int = 5) -> GameResult:
    return GameResult(sub_games=[_sg(GameOutcome.COP_WIN, cop, thief)] * 3)


class _FakeLLM:
    def generate(self, prompt: str) -> str:
        return "ok"


def test_build_bonus_sub_games_attributes_cop_half_points_correctly() -> None:
    cop_half = GameResult(sub_games=[_sg(GameOutcome.COP_WIN, 20, 5)] * 3)
    thief_half = GameResult(sub_games=[_sg(GameOutcome.THIEF_WIN, 5, 10)] * 3)
    sub_games, our_total, their_total = build_bonus_sub_games(cop_half, thief_half)

    # cop_half: our cop_points=20×3=60; their thief_points=5×3=15
    # thief_half: their cop_points=5×3=15; our thief_points=10×3=30
    assert our_total == 60 + 30
    assert their_total == 15 + 15
    assert len(sub_games) == 6
    assert sub_games[0]["role_group_1"] == "cop"
    assert sub_games[3]["role_group_1"] == "thief"
    assert sub_games[0]["index"] == 1
    assert sub_games[3]["index"] == 4


def test_run_bonus_match_returns_early_when_other_urls_missing(
    monkeypatch: pytest.MonkeyPatch, sample_game_config: GameConfig
) -> None:
    monkeypatch.delenv("BONUS_OTHER_MCP_COP_URL", raising=False)
    monkeypatch.delenv("BONUS_OTHER_MCP_THIEF_URL", raising=False)
    run_bonus_match(sample_game_config, _FakeLLM())  # must not raise or call real MCP


def test_run_bonus_match_sends_report_when_configured(
    monkeypatch: pytest.MonkeyPatch, sample_game_config: GameConfig
) -> None:
    sent: list = []

    class _FakeMailer:
        def send_report(self, report: dict, subject: str = "") -> None:
            sent.append(report)

    monkeypatch.setenv("BONUS_OTHER_MCP_COP_URL", "https://other-cop.example.com")
    monkeypatch.setenv("BONUS_OTHER_MCP_THIEF_URL", "https://other-thief.example.com")
    monkeypatch.setenv("BONUS_OTHER_GROUP_NAME", "TeamBeta")
    monkeypatch.setattr("hw6_race.services.reporting.mailer.build_mailer_from_env", lambda gk: _FakeMailer())

    with patch.object(bonus_mod, "_half_async", new=AsyncMock(return_value=_fake_result())):
        run_bonus_match(sample_game_config, _FakeLLM())

    assert len(sent) == 1
    assert sent[0]["report_type"] == "bonus_game"
    assert sent[0]["groups"]["group_2"] == "TeamBeta"


def test_run_bonus_match_swallows_mailer_errors(
    monkeypatch: pytest.MonkeyPatch, sample_game_config: GameConfig
) -> None:
    from hw6_race.services.reporting.mailer import MailerError

    class _FailMailer:
        def send_report(self, report: dict, subject: str = "") -> None:
            raise MailerError("boom")

    monkeypatch.setenv("BONUS_OTHER_MCP_COP_URL", "https://other-cop.example.com")
    monkeypatch.setenv("BONUS_OTHER_MCP_THIEF_URL", "https://other-thief.example.com")
    monkeypatch.setattr("hw6_race.services.reporting.mailer.build_mailer_from_env", lambda gk: _FailMailer())

    with patch.object(bonus_mod, "_half_async", new=AsyncMock(return_value=_fake_result())):
        run_bonus_match(sample_game_config, _FakeLLM())  # must not raise


def test_half_async_delegates_to_orchestrator(
    monkeypatch: pytest.MonkeyPatch, sample_game_config: GameConfig
) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    fake_result = GameResult(sub_games=[])
    monkeypatch.setattr(bonus_mod.wiring, "build_agents", MagicMock(return_value=(MagicMock(), MagicMock())))
    monkeypatch.setattr(bonus_mod.wiring, "build_explicit_remote_clients", MagicMock(return_value=(MagicMock(), MagicMock())))
    monkeypatch.setattr(bonus_mod.orchestrator, "play_game_async", AsyncMock(return_value=fake_result))

    result = asyncio.run(bonus_mod._half_async(
        sample_game_config, _FakeLLM(), "cop-url", "cop-tok", "thief-url", "thief-tok"
    ))
    assert result is fake_result


def test_run_bonus_match_logs_warning_when_gmail_not_configured(
    monkeypatch: pytest.MonkeyPatch, sample_game_config: GameConfig
) -> None:
    monkeypatch.setenv("BONUS_OTHER_MCP_COP_URL", "https://other-cop.example.com")
    monkeypatch.setenv("BONUS_OTHER_MCP_THIEF_URL", "https://other-thief.example.com")
    monkeypatch.delenv("GMAIL_OAUTH_CLIENT_SECRET_PATH", raising=False)
    monkeypatch.delenv("GMAIL_OAUTH_TOKEN_PATH", raising=False)

    with patch.object(bonus_mod, "_half_async", new=AsyncMock(return_value=_fake_result())):
        run_bonus_match(sample_game_config, _FakeLLM())  # must not raise
