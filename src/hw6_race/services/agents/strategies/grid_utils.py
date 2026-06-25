"""Shared grid bounds-checking, used by every DecisionStrategy that reasons
about movement — defined once so HeuristicStrategy and LLMDecisionStrategy
never duplicate this logic (SG-C04).
"""

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import AgentObservation

MOVE_DELTAS: dict[MoveDirection, tuple[int, int]] = {
    MoveDirection.UP: (-1, 0),
    MoveDirection.DOWN: (1, 0),
    MoveDirection.LEFT: (0, -1),
    MoveDirection.RIGHT: (0, 1),
}


def stays_in_bounds(observation: AgentObservation, direction: MoveDirection) -> bool:
    """Return True if moving `direction` from the observation's position is legal."""
    row, col = observation.own_position
    d_row, d_col = MOVE_DELTAS[direction]
    rows, cols = observation.grid_size
    return 0 <= row + d_row < rows and 0 <= col + d_col < cols
