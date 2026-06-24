from pathlib import Path

import pytest

from hw6_race.services.agents.llm_client import GatekeptLLMClient
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig, RateLimitExceededError


@pytest.fixture
def gatekeeper(tmp_rate_limits_file: Path, fake_clock) -> ApiGatekeeper:
    config = RateLimitConfig.from_file(tmp_rate_limits_file)
    return ApiGatekeeper(config, service="default", clock=fake_clock)


def test_generate_calls_complete_fn_with_the_prompt_and_returns_its_result(
    gatekeeper: ApiGatekeeper,
) -> None:
    seen_prompts = []

    def complete_fn(prompt: str) -> str:
        seen_prompts.append(prompt)
        return "a response"

    client = GatekeptLLMClient(gatekeeper, complete_fn)
    result = client.generate("hello model")

    assert result == "a response"
    assert seen_prompts == ["hello model"]


def test_generate_routes_through_the_gatekeeper_rate_limit(gatekeeper: ApiGatekeeper) -> None:
    client = GatekeptLLMClient(gatekeeper, lambda prompt: "ok")
    for _ in range(30):
        client.generate("prompt")

    with pytest.raises(RateLimitExceededError):
        client.generate("one too many")


def test_swapping_complete_fn_requires_no_change_to_generate(gatekeeper: ApiGatekeeper) -> None:
    """Proves provider choice (HW-F19) is purely a constructor-time decision."""
    client_a = GatekeptLLMClient(gatekeeper, lambda prompt: "provider A")
    client_b = GatekeptLLMClient(gatekeeper, lambda prompt: "provider B")

    assert client_a.generate("x") == "provider A"
    assert client_b.generate("x") == "provider B"
