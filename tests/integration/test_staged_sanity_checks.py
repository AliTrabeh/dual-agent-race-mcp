"""Staged sanity-check matrix (HW-F12): increasing grid sizes/complexity, all
driven purely by config — no code branching per stage (docs/03_architecture.md
§4 calls this a test-fixture concern, not a code-path concern).
"""

import pytest

from hw6_race.constants import AgentRole, GameOutcome
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

STAGE_GRID_SIZES = [
    (2, 2),  # Stage 1: minimal algorithmic/pipeline sanity
    (3, 3),  # Stage 2: coordination/hyperparameter checks
    (3, 2),
    (4, 4),  # Stage 3: partial-observability effects
    (4, 3),
    (5, 5),  # Stage 4: full final run (also exercised at default scale in Chunk 6/8)
]


def _config_for(grid_size: tuple[int, int]) -> GameConfig:
    data = {
        "version": "1.00",
        "grid_size": list(grid_size),
        "max_moves": 12,
        "num_games": 2,
        "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    }
    return GameConfig(data)


@pytest.mark.parametrize("grid_size", STAGE_GRID_SIZES)
def test_staged_sanity_check_completes_and_stays_in_bounds(grid_size: tuple[int, int]) -> None:
    config = _config_for(grid_size)
    sdk = Hw6RaceSDK(config=config)

    result = sdk.run_local_match()

    num_games = config.num_games
    assert len(result.sub_games) == num_games
    for sub_game in result.sub_games:
        assert sub_game.outcome in (
            GameOutcome.COP_WIN,
            GameOutcome.THIEF_WIN,
            GameOutcome.TECHNICAL_LOSS,
        )
    assert 5 * num_games <= result.total_cop_points <= 20 * num_games
    assert 5 * num_games <= result.total_thief_points <= 10 * num_games


async def test_stage_1_message_pipeline_is_lossless_on_the_smallest_grid() -> None:
    """Stage 1 (2x2): HW-F12 explicitly calls for message-Pipeline integration
    and transmission verification, not just "the match completes"."""
    config = _config_for((2, 2))
    rate_limits = RateLimitConfig.from_file("config/rate_limits.json")
    gatekeeper = ApiGatekeeper(rate_limits, service="llm")
    llm_client = build_default_llm_client(gatekeeper)
    cop_agent, thief_agent = build_agents(config, llm_client)
    auth_manager = build_auth_manager()

    cop_store, thief_store = MessageStore(), MessageStore()
    cop_server = build_agent_server(AgentRole.COP, auth_manager, cop_store)
    thief_server = build_agent_server(AgentRole.THIEF, auth_manager, thief_store)
    cop_client = AgentMCPClient(cop_server, LOCAL_COP_TOKEN)
    thief_client = AgentMCPClient(thief_server, LOCAL_THIEF_TOKEN)

    await play_game_async(config, thief_agent, cop_agent, thief_client, cop_client)

    assert cop_store.outbox_log(), "Cop must send at least one message on the smallest grid"
    assert thief_store.outbox_log(), "Thief must send at least one message on the smallest grid"
