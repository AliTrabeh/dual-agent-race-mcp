"""Default deterministic decision strategy (ADR-003) — no LLM, no randomness.

Tries movement directions in a fixed priority order and returns the first one
that stays within grid bounds. Exists so the system has a working, fully
testable default instead of (or before) the optional Q-Learning strategy.
Out of scope by design: grids smaller than 2x2 (the HW PDF's smallest sanity
stage is 2x2 — see docs/05_testing_strategy.md), where no move may be legal.
"""

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy

_PRIORITY_ORDER = (MoveDirection.RIGHT, MoveDirection.DOWN, MoveDirection.LEFT, MoveDirection.UP)

_DELTAS: dict[MoveDirection, tuple[int, int]] = {
    MoveDirection.UP: (-1, 0),
    MoveDirection.DOWN: (1, 0),
    MoveDirection.LEFT: (0, -1),
    MoveDirection.RIGHT: (0, 1),
}


class HeuristicStrategy(DecisionStrategy):
    """Always returns a legal move when one exists; never places a barrier."""

    def decide(self, observation: AgentObservation) -> AgentAction:
        for direction in _PRIORITY_ORDER:
            if self._stays_in_bounds(observation, direction):
                return AgentAction(action_type=ActionType.MOVE, direction=direction)
        return AgentAction(action_type=ActionType.MOVE, direction=_PRIORITY_ORDER[0])

    @staticmethod
    def _stays_in_bounds(observation: AgentObservation, direction: MoveDirection) -> bool:
        row, col = observation.own_position
        d_row, d_col = _DELTAS[direction]
        rows, cols = observation.grid_size
        return 0 <= row + d_row < rows and 0 <= col + d_col < cols
