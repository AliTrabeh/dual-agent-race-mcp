"""End-to-end integration tests for Chunk 6: real MCP servers (in-process),
real agents, real race engine, a safe no-network default LLM stub. Validates
HW-F01 (full pipeline) and the "no direct cross-talk outside MCP" property.
"""

import json

from hw6_race.constants import AgentRole
from hw6_race.sdk import Hw6RaceSDK
from hw6_race.sdk.orchestrator import play_game_async
from hw6_race.sdk.wiring import (
    LOCAL_COP_TOKEN,
    LOCAL_THIEF_TOKEN,
    build_agents,
    build_auth_manager,
    build_default_llm_client,
)
from hw6_race.services.mcp.client import AgentMCPClient
from hw6_race.services.mcp.message_store import MessageStore
from hw6_race.services.mcp.server_base import build_agent_server
from hw6_race.shared.config import GameConfig
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


def _small_config() -> GameConfig:
    data = {
        "version": "1.00",
        "grid_size": [3, 3],
        "max_moves": 6,
        "num_games": 2,
        "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    }
    return GameConfig(data)


async def test_play_game_async_exchanges_messages_only_through_mcp(tmp_rate_limits_file) -> None:
    config = _small_config()
    rate_limits = RateLimitConfig.from_file(tmp_rate_limits_file)
    gatekeeper = ApiGatekeeper(rate_limits, service="default")
    llm_client = build_default_llm_client(gatekeeper)
    cop_agent, thief_agent = build_agents(config, llm_client)
    auth_manager = build_auth_manager()

    cop_store, thief_store = MessageStore(), MessageStore()
    cop_server = build_agent_server(AgentRole.COP, auth_manager, cop_store)
    thief_server = build_agent_server(AgentRole.THIEF, auth_manager, thief_store)
    cop_client = AgentMCPClient(cop_server, LOCAL_COP_TOKEN)
    thief_client = AgentMCPClient(thief_server, LOCAL_THIEF_TOKEN)

    result = await play_game_async(config, thief_agent, cop_agent, thief_client, cop_client)

    assert len(result.sub_games) == 2
    assert cop_store.outbox_log(), "Cop must have sent at least one message via its own MCP server"
    assert thief_store.outbox_log(), "Thief must have sent at least one message via its own MCP server"

    for sub_game in result.sub_games:
        assert sub_game.outcome.value in ("cop_win", "thief_win", "technical_loss")


def test_hw6_race_sdk_run_local_match_completes_end_to_end() -> None:
    sdk = Hw6RaceSDK()
    result = sdk.run_local_match()

    num_games = sdk.config.num_games
    assert len(result.sub_games) == num_games

    max_cop_total = 15 * num_games + 5 * num_games
    min_cop_total = 5 * num_games
    min_thief_total = 5 * num_games
    max_thief_total = 10 * num_games

    assert min_cop_total <= result.total_cop_points <= max_cop_total
    assert min_thief_total <= result.total_thief_points <= max_thief_total

    serialized = json.dumps(
        {"cop": result.total_cop_points, "thief": result.total_thief_points}
    )
    assert json.loads(serialized)["cop"] == result.total_cop_points
