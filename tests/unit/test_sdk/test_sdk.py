from hw6_race.sdk import Hw6RaceSDK
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
