"""LLM-driven decision strategy (HW-F02/F19): asks the LLM which direction to
move (or whether to place a barrier), instead of following a fixed rule, so
an agent's *action* — not just its chat message — reflects real reasoning.

Falls back to another DecisionStrategy whenever the LLM fails, replies with
something unparseable, or chooses an action that turns out illegal — never
crashes, never lets an illegal action reach the race engine.
"""

import logging

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy
from hw6_race.services.agents.strategies.grid_utils import stays_in_bounds
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy

logger = logging.getLogger(__name__)

_DIRECTION_WORDS: dict[str, MoveDirection] = {d.name: d for d in MoveDirection}
_BARRIER_WORD = "PLACE_BARRIER"


class LLMDecisionStrategy(DecisionStrategy):
    """Setup: an LLMClient and a fallback DecisionStrategy (default: Heuristic).
    Input: an AgentObservation. Output: an AgentAction chosen by asking the
    LLM and validating it for legality, or the fallback's choice otherwise.
    """

    def __init__(self, llm_client: LLMClient, fallback: DecisionStrategy | None = None) -> None:
        self._llm_client = llm_client
        self._fallback = fallback or HeuristicStrategy()

    def decide(self, observation: AgentObservation) -> AgentAction:
        try:
            response = self._llm_client.generate(self._build_prompt(observation))
        except Exception:
            logger.exception("LLM failed while deciding a move; using the fallback strategy")
            return self._fallback.decide(observation)

        action = self._parse(response, observation)
        if action is None:
            logger.warning("Could not parse a legal action from LLM response: %r", response)
            return self._fallback.decide(observation)
        return action

    def _build_prompt(self, observation: AgentObservation) -> str:
        role = observation.role
        parts = [
            f"You are the {role.value if role else 'agent'} in a grid pursuit game.",
            f"Your position is {observation.own_position} on a {observation.grid_size} "
            "grid (rows, cols), 0-indexed.",
        ]
        if observation.believed_opponent_position is not None:
            parts.append(f"You believe the opponent is at {observation.believed_opponent_position}.")

        options = "UP, DOWN, LEFT, RIGHT"
        if role == AgentRole.COP and observation.barriers_remaining > 0:
            parts.append(
                f"You may also place a barrier on your own current cell "
                f"({observation.barriers_remaining} remaining) to block your own future "
                "movement through it."
            )
            options += f", {_BARRIER_WORD}"
        parts.append(f"Choose your next action. Reply with ONLY one of: {options}. No explanation.")
        return " ".join(parts)

    def _parse(self, response: str, observation: AgentObservation) -> AgentAction | None:
        tokens = (response or "").strip().upper().split()
        word = tokens[0] if tokens else ""

        if word == _BARRIER_WORD:
            if observation.role == AgentRole.COP and observation.barriers_remaining > 0:
                return AgentAction(action_type=ActionType.PLACE_BARRIER)
            return None

        direction = _DIRECTION_WORDS.get(word)
        if direction is None or not stays_in_bounds(observation, direction):
            return None
        return AgentAction(action_type=ActionType.MOVE, direction=direction)
