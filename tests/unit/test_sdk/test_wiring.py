import pytest

from hw6_race.constants import AgentRole
from hw6_race.sdk import wiring
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy
from hw6_race.services.agents.strategies.llm_strategy import LLMDecisionStrategy
from hw6_race.services.agents.strategies.minimax.strategy import MinimaxDecisionStrategy
from hw6_race.services.mcp.auth import AuthError
from hw6_race.shared.config import GameConfig
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


@pytest.fixture
def gatekeeper(tmp_rate_limits_file, fake_clock) -> ApiGatekeeper:
    config = RateLimitConfig.from_file(tmp_rate_limits_file)
    return ApiGatekeeper(config, service="default", clock=fake_clock)


def test_stub_complete_returns_unknown_for_interpret_prompts() -> None:
    prompt = "If they revealed a believed grid position, reply with exactly 'ROW,COL'."
    assert wiring._stub_complete(prompt) == "UNKNOWN"


def test_stub_complete_returns_generic_text_for_compose_prompts() -> None:
    assert wiring._stub_complete("Describe your situation") == "no comment"


def test_build_default_llm_client_routes_through_the_gatekeeper(gatekeeper) -> None:
    client = wiring.build_default_llm_client(gatekeeper)
    assert client.generate("Describe your situation") == "no comment"


def test_build_auth_manager_registers_both_roles() -> None:
    manager = wiring.build_auth_manager()
    manager.verify(wiring.LOCAL_COP_TOKEN, AgentRole.COP.value)
    manager.verify(wiring.LOCAL_THIEF_TOKEN, AgentRole.THIEF.value)


def test_build_auth_manager_tokens_are_role_specific() -> None:
    manager = wiring.build_auth_manager()
    with pytest.raises(AuthError):
        manager.verify(wiring.LOCAL_COP_TOKEN, AgentRole.THIEF.value)


def test_build_agents_returns_correctly_roled_agents(gatekeeper, sample_game_config) -> None:
    llm_client = wiring.build_default_llm_client(gatekeeper)
    cop_agent, thief_agent = wiring.build_agents(sample_game_config, llm_client)
    assert cop_agent.role == AgentRole.COP
    assert thief_agent.role == AgentRole.THIEF


def test_build_strategy_defaults_to_minimax(gatekeeper, sample_game_config) -> None:
    llm_client = wiring.build_default_llm_client(gatekeeper)
    strategy = wiring._build_strategy(sample_game_config, llm_client)
    assert isinstance(strategy, MinimaxDecisionStrategy)


def test_build_strategy_selects_llm(gatekeeper, sample_config_data) -> None:
    llm_client = wiring.build_default_llm_client(gatekeeper)
    config = GameConfig({**sample_config_data, "decision_strategy": "llm"})
    strategy = wiring._build_strategy(config, llm_client)
    assert isinstance(strategy, LLMDecisionStrategy)


def test_build_strategy_selects_heuristic(gatekeeper, sample_config_data) -> None:
    llm_client = wiring.build_default_llm_client(gatekeeper)
    config = GameConfig({**sample_config_data, "decision_strategy": "heuristic"})
    strategy = wiring._build_strategy(config, llm_client)
    assert isinstance(strategy, HeuristicStrategy)


def test_build_clients_returns_two_independently_bound_clients() -> None:
    auth_manager = wiring.build_auth_manager()
    cop_client, thief_client = wiring.build_clients(auth_manager)
    assert cop_client is not thief_client


def test_build_explicit_remote_clients_returns_two_distinct_clients() -> None:
    cop_client, thief_client = wiring.build_explicit_remote_clients(
        "https://cop.example.com", "cop-tok",
        "https://thief.example.com", "thief-tok",
    )
    assert cop_client is not thief_client


def test_build_bonus_round_clients_returns_own_and_bonus_opponent() -> None:
    from hw6_race.constants import AgentRole
    from hw6_race.services.mcp.client import BonusOpponentClient

    own, opp = wiring.build_bonus_round_clients(
        "https://our.example.com", "our-tok",
        "https://their.example.com", "their-tok",
        AgentRole.COP,
    )
    assert isinstance(opp, BonusOpponentClient)
    assert opp._our_role == AgentRole.COP
    assert own._token == "our-tok"




def test_build_llm_client_from_env_falls_back_to_stub_when_unset(
    gatekeeper, monkeypatch
) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    client = wiring.build_llm_client_from_env(gatekeeper)

    assert client.generate("Describe your situation") == "no comment"


def test_build_llm_client_from_env_falls_back_when_provider_set_but_no_key(
    gatekeeper, monkeypatch
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    client = wiring.build_llm_client_from_env(gatekeeper)

    assert client.generate("Describe your situation") == "no comment"


def test_build_llm_client_from_env_builds_anthropic_client_when_configured(
    gatekeeper, monkeypatch
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "fake-key-for-construction-only")
    monkeypatch.setenv("LLM_MODEL", "claude-sonnet-4-6")

    client = wiring.build_llm_client_from_env(gatekeeper)

    assert isinstance(client, wiring.GatekeptLLMClient)
    assert isinstance(client._complete_fn, wiring.AnthropicCompleteFn)
    assert client._complete_fn._model == "claude-sonnet-4-6"
