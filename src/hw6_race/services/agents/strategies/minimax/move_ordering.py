"""Move ordering to improve alpha-beta pruning — search good moves first so
more of the tree gets cut. Reuses the same metrics evaluation.py uses,
never reimplements legality or distance math (SG-C04).
"""

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.agents.strategies.grid_utils import MOVE_DELTAS
from hw6_race.services.race.race_state import RaceState

_DIRECTION_PRIORITY = {
    MoveDirection.RIGHT: 0,
    MoveDirection.DOWN: 1,
    MoveDirection.LEFT: 2,
    MoveDirection.UP: 3,
}


def _is_immediate_capture(state: RaceState, cop_action: AgentAction) -> bool:
    if cop_action.action_type != ActionType.MOVE:
        return False
    d_row, d_col = MOVE_DELTAS[cop_action.direction]
    destination = (state.cop_position[0] + d_row, state.cop_position[1] + d_col)
    return destination == state.thief_position


def order_cop_actions(state: RaceState, actions: list[AgentAction]) -> list[AgentAction]:
    """Immediate captures first, then moves toward the Thief, barrier last."""

    def sort_key(action: AgentAction) -> tuple:
        if _is_immediate_capture(state, action):
            return (0, 0)
        if action.action_type == ActionType.PLACE_BARRIER:
            return (2, 0)
        d_row, d_col = MOVE_DELTAS[action.direction]
        new_distance = abs(state.cop_position[0] + d_row - state.thief_position[0]) + abs(
            state.cop_position[1] + d_col - state.thief_position[1]
        )
        return (1, new_distance, _DIRECTION_PRIORITY[action.direction])

    return sorted(actions, key=sort_key)


def order_thief_actions(state: RaceState, actions: list[AgentAction]) -> list[AgentAction]:
    """Moves that increase distance from the Cop first."""

    def sort_key(action: AgentAction) -> tuple:
        d_row, d_col = MOVE_DELTAS[action.direction]
        new_distance = abs(state.thief_position[0] + d_row - state.cop_position[0]) + abs(
            state.thief_position[1] + d_col - state.cop_position[1]
        )
        return (-new_distance, _DIRECTION_PRIORITY[action.direction])

    return sorted(actions, key=sort_key)
