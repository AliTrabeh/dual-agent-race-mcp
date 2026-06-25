"""Synchronized single-role game loops for the inter-group bonus round (HW §12.1).

In the bonus round each group runs only their assigned role.  The opponent's
turns arrive as NL messages relayed to our own MCP server by the other
group's script, signalling that the opponent has moved.
"""

import asyncio
import logging

from hw6_race.constants import AgentRole, GameOutcome
from hw6_race.sdk import orchestrator
from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.mcp.client import AgentMCPClient
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.race.race_engine import default_start_positions
from hw6_race.services.race.race_state import RaceState
from hw6_race.services.race.scoring import score_sub_game
from hw6_race.shared.config import GameConfig

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 2.0
_DEFAULT_TIMEOUT = 300.0


async def wait_for_opponent_message(
    client: AgentMCPClient, timeout: float = _DEFAULT_TIMEOUT
) -> str | None:
    """Poll `client`'s inbox every 2 s until a message arrives or timeout elapses."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        msgs = await client.get_inbox()
        if msgs:
            return msgs[-1]
        await asyncio.sleep(_POLL_INTERVAL)
    logger.warning("Timed out waiting for opponent message after %.0fs", timeout)
    return None


def _update_opponent_position(
    state: RaceState, opp_role: AgentRole, agent: BaseAgent, text: str
) -> None:
    """Parse `text` for the opponent's position and write it directly into `state`."""
    inference = agent.interpret_message(text)
    if inference.believed_position and inference.confidence == "stated":
        if opp_role == AgentRole.THIEF:
            state.thief_position = inference.believed_position
        else:
            state.cop_position = inference.believed_position


def _action_from_state(old_pos, new_pos, old_b: int, new_b: int) -> dict:
    if new_b > old_b:
        return {"type": "barrier"}
    dirs = {(-1, 0): "up", (1, 0): "down", (0, -1): "left", (0, 1): "right"}
    direction = dirs.get((new_pos[0] - old_pos[0], new_pos[1] - old_pos[1]), "stay")
    return {"type": "move", "direction": direction}


async def _play_one_role_sub_game(
    config: GameConfig,
    our_agent: BaseAgent,
    our_role: AgentRole,
    own_client: AgentMCPClient,
    opponent_client: AgentMCPClient,
    cop_start: tuple[int, int],
    thief_start: tuple[int, int],
    timeout: float,
) -> SubGameResult:
    """One sub-game where we control `our_role` and wait for the opponent's turns."""
    opp_role = AgentRole.THIEF if our_role == AgentRole.COP else AgentRole.COP
    _us = cop_start if our_role == AgentRole.COP else thief_start
    _them = thief_start if our_role == AgentRole.COP else cop_start
    state = RaceState(
        grid_size=config.grid_size,
        max_moves=config.max_moves,
        max_barriers=config.max_barriers,
        cop_position=cop_start,
        thief_position=thief_start,
    )
    await own_client.init_bonus_subgame(_us)
    try: await opponent_client.start_subgame(_them)
    except Exception: logger.warning("opponent start_subgame failed — continuing")
    outcome = state.check_outcome()
    while outcome is None:
        for role in (AgentRole.THIEF, AgentRole.COP):  # Thief moves first (HW-F04)
            if role == our_role:
                _old = state.cop_position if role == AgentRole.COP else state.thief_position
                _old_b = state.barriers_placed
                await orchestrator.take_turn(state, role, our_agent, own_client, opponent_client)
                _new = state.cop_position if role == AgentRole.COP else state.thief_position
                _act = _action_from_state(_old, _new, _old_b, state.barriers_placed)
                try: await opponent_client.choose_action(_act)
                except Exception: logger.warning("opponent choose_action failed — continuing")
                await own_client.set_bonus_position(_new)
            else:
                msg = await wait_for_opponent_message(own_client, timeout)
                if msg is None:
                    logger.error("Opponent timed out — recording Technical Loss")
                    return score_sub_game(GameOutcome.TECHNICAL_LOSS, state.move_count, config)
                _update_opponent_position(state, opp_role, our_agent, msg)
                state.move_count += 1
            outcome = state.check_outcome()
            if outcome is not None:
                break
    return score_sub_game(outcome, state.move_count, config)


async def play_cop_only_game_async(
    config: GameConfig,
    cop_agent: BaseAgent,
    cop_client: AgentMCPClient,
    thief_client: AgentMCPClient,
    timeout: float = _DEFAULT_TIMEOUT,
) -> GameResult:
    """Run `config.num_games` sub-games where we control the Cop."""
    result = GameResult()
    async with cop_client, thief_client:
        for _ in range(config.num_games):
            cop_s, thief_s = default_start_positions(config)
            result.sub_games.append(
                await _play_one_role_sub_game(
                    config, cop_agent, AgentRole.COP,
                    cop_client, thief_client, cop_s, thief_s, timeout,
                )
            )
    return result


async def play_thief_only_game_async(
    config: GameConfig,
    thief_agent: BaseAgent,
    thief_client: AgentMCPClient,
    cop_client: AgentMCPClient,
    timeout: float = _DEFAULT_TIMEOUT,
) -> GameResult:
    """Run `config.num_games` sub-games where we control the Thief."""
    result = GameResult()
    async with thief_client, cop_client:
        for _ in range(config.num_games):
            cop_s, thief_s = default_start_positions(config)
            result.sub_games.append(
                await _play_one_role_sub_game(
                    config, thief_agent, AgentRole.THIEF,
                    thief_client, cop_client, cop_s, thief_s, timeout,
                )
            )
    return result
