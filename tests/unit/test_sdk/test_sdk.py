import pytest

from hw6_race.sdk import Hw6RaceSDK
from hw6_race.services.race.models import GameResult
from hw6_race.shared.config import GameConfig


class _FakeLLMClient:
    def generate(self, prompt: str) -> str:
        return "ok"


def test_sdk_uses_an_explicitly_injected_llm_client(sample_game_config: GameConfig) -> None:
    injected = _FakeLLMClient()
    sdk = Hw6RaceSDK(config=sample_game_config, llm_client=injected)
    assert sdk._llm_client is injected


def test_sdk_config_property_returns_the_constructed_config(sample_game_config: GameConfig) -> None:
    sdk = Hw6RaceSDK(config=sample_game_config)
    assert sdk.config is sample_game_config


def test_send_match_report_is_noop_without_gmail_credentials(
    sample_game_config: GameConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GMAIL_OAUTH_CLIENT_SECRET_PATH", raising=False)
    monkeypatch.delenv("GMAIL_OAUTH_TOKEN_PATH", raising=False)
    sdk = Hw6RaceSDK(config=sample_game_config, llm_client=_FakeLLMClient())
    sdk.send_match_report(GameResult(sub_games=[]))


def test_send_match_report_sends_report_when_mailer_is_available(
    sample_game_config: GameConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[dict] = []

    class _FakeMailer:
        def send_report(self, report: dict) -> None:
            sent.append(report)

    monkeypatch.setattr(
        "hw6_race.services.reporting.mailer.build_mailer_from_env",
        lambda gk: _FakeMailer(),
    )
    sdk = Hw6RaceSDK(config=sample_game_config, llm_client=_FakeLLMClient())
    sdk.send_match_report(GameResult(sub_games=[]))

    assert len(sent) == 1
    assert "group_name" in sent[0]


def test_run_bonus_match_delegates_to_bonus_module(
    sample_game_config: GameConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list = []
    monkeypatch.setattr("hw6_race.sdk.bonus.run_bonus_match", lambda config, llm: called.append(True))

    sdk = Hw6RaceSDK(config=sample_game_config, llm_client=_FakeLLMClient())
    sdk.run_bonus_match()

    assert called == [True]


def test_send_match_report_swallows_mailer_errors(
    sample_game_config: GameConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hw6_race.services.reporting.mailer import MailerError

    class _FailingMailer:
        def send_report(self, report: dict) -> None:
            raise MailerError("test failure")

    monkeypatch.setattr(
        "hw6_race.services.reporting.mailer.build_mailer_from_env",
        lambda gk: _FailingMailer(),
    )
    sdk = Hw6RaceSDK(config=sample_game_config, llm_client=_FakeLLMClient())
    sdk.send_match_report(GameResult(sub_games=[]))
