"""Default deterministic decision strategy (ADR-003) — no randomness.

Falls back to a fixed movement priority order (no opponent-position
knowledge needed) unless the observation carries a `believed_opponent_position`
(HW-F02: an agent's decoded/inferred belief must actually inform its move) —
in that case the Cop chases and the Thief flees, via Manhattan distance.
Out of scope by design: grids smaller than 2x2 (the HW PDF's smallest sanity
stage is 2x2 — see docs/05_testing_strategy.md), where no move may be legal.
"""

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy
from hw6_race.services.agents.strategies.grid_utils import MOVE_DELTAS, stays_in_bounds

_PRIORITY_ORDER = (MoveDirection.RIGHT, MoveDirection.DOWN, MoveDirection.LEFT, MoveDirection.UP)


class HeuristicStrategy(DecisionStrategy):
    """Always returns a legal move when one exists; never places a barrier."""

    def decide(self, observation: AgentObservation) -> AgentAction:
        if observation.believed_opponent_position is not None and observation.role is not None:
            action = self._chase_or_flee(observation)
            if action is not None:
                return action
        return self._default_move(observation)

    def _default_move(self, observation: AgentObservation) -> AgentAction:
        for direction in _PRIORITY_ORDER:
            if stays_in_bounds(observation, direction):
                return AgentAction(action_type=ActionType.MOVE, direction=direction)
        return AgentAction(action_type=ActionType.MOVE, direction=_PRIORITY_ORDER[0])

    def _chase_or_flee(self, observation: AgentObservation) -> AgentAction | None:
        """Cop minimizes, Thief maximizes, Manhattan distance to the belief."""
        row, col = observation.own_position
        target_row, target_col = observation.believed_opponent_position
        seeking = observation.role == AgentRole.COP

        candidates: list[tuple[int, MoveDirection]] = []
        for direction in _PRIORITY_ORDER:
            if not stays_in_bounds(observation, direction):
                continue
            d_row, d_col = MOVE_DELTAS[direction]
            distance = abs(row + d_row - target_row) + abs(col + d_col - target_col)
            candidates.append((distance, direction))

        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=not seeking)
        return AgentAction(action_type=ActionType.MOVE, direction=candidates[0][1])
