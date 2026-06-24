"""Async game-loop bridging the MCP layer (Chunk 3), agent layer (Chunk 4), and
race engine (Chunk 5) into one runnable match (HW-F01/F02/F15).

Implements its own per-sub-game alternation rather than reusing
race_engine.play_sub_game's sync loop, so MCP client connections stay open for
a whole match instead of reconnecting per move (ADR-007, docs/PLAN.md).
RaceState/scoring are reused directly — never reimplemented here.
"""

import logging

from hw6_race.constants import AgentRole, GameOutcome
from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.agents.models import AgentObservation
from hw6_race.services.mcp.client import AgentMCPClient
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.race.race_engine import default_start_positions
from hw6_race.services.race.race_state import RaceState
from hw6_race.services.race.scoring import score_sub_game
from hw6_race.shared.config import GameConfig

logger = logging.getLogger(__name__)


def observation_for(state: RaceState, role: AgentRole) -> AgentObservation:
    """Build the AgentObservation `role` is allowed to see from `state`."""
    position = state.cop_position if role == AgentRole.COP else state.thief_position
    barriers_remaining = (
        state.max_barriers - state.barriers_placed if role == AgentRole.COP else 0
    )
    return AgentObservation(
        own_position=position, grid_size=state.grid_size, barriers_remaining=barriers_remaining
    )


async def take_turn(
    state: RaceState,
    role: AgentRole,
    agent: BaseAgent,
    own_client: AgentMCPClient,
    opponent_client: AgentMCPClient,
) -> None:
    """One agent's full turn: drain inbox + interpret, compose + relay, decide + apply."""
    inbox = await own_client.get_inbox()
    for text in inbox:
        inference = agent.interpret_message(text)
        logger.debug("[%s] inferred %s from %r", role.value, inference, text)

    observation = observation_for(state, role)
    message = agent.compose_message(observation)
    await own_client.send_message(message)
    await opponent_client.receive_message(message)

    action = agent.decide_action(observation)
    state.apply_action(role, action)


async def play_sub_game_async(
    config: GameConfig,
    thief_agent: BaseAgent,
    cop_agent: BaseAgent,
    thief_client: AgentMCPClient,
    cop_client: AgentMCPClient,
    cop_start: tuple[int, int],
    thief_start: tuple[int, int],
) -> SubGameResult:
    """Run one sub-game to a terminal outcome via real agent/MCP turns."""
    state = RaceState(
        grid_size=config.grid_size,
        max_moves=config.max_moves,
        max_barriers=config.max_barriers,
        cop_position=cop_start,
        thief_position=thief_start,
    )
    outcome = state.check_outcome()
    while outcome is None:
        await take_turn(state, AgentRole.THIEF, thief_agent, thief_client, cop_client)
        outcome = state.check_outcome()
        if outcome is not None:
            break
        await take_turn(state, AgentRole.COP, cop_agent, cop_client, thief_client)
        outcome = state.check_outcome()
    return score_sub_game(outcome, state.move_count, config)


async def play_game_async(
    config: GameConfig,
    thief_agent: BaseAgent,
    cop_agent: BaseAgent,
    thief_client: AgentMCPClient,
    cop_client: AgentMCPClient,
) -> GameResult:
    """Run `config.num_games` sub-games and aggregate the result.

    A sub-game that raises (e.g. an MCP call failing) is recorded as a
    Technical Loss rather than crashing the whole match — full rerun-to-6
    bookkeeping is Chunk 7's responsibility (PRD-005), not implemented here.
    """
    result = GameResult()
    async with cop_client, thief_client:
        for _ in range(config.num_games):
            cop_start, thief_start = default_start_positions(config)
            try:
                sub_game = await play_sub_game_async(
                    config, thief_agent, cop_agent, thief_client, cop_client, cop_start, thief_start
                )
            except Exception:
                logger.exception("Sub-game failed; recording as Technical Loss")
                sub_game = score_sub_game(GameOutcome.TECHNICAL_LOSS, move_count=0, config=config)
            result.sub_games.append(sub_game)
    return result
