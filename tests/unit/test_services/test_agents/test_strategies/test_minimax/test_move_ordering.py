from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.agents.strategies.minimax.board_utils import legal_actions
from hw6_race.services.agents.strategies.minimax.move_ordering import (
    order_cop_actions,
    order_thief_actions,
)
from hw6_race.services.race.race_state import RaceState


def _state(**overrides) -> RaceState:
    defaults = {
        "grid_size": (5, 5),
        "max_moves": 25,
        "max_barriers": 5,
        "cop_position": (0, 0),
        "thief_position": (4, 4),
    }
    defaults.update(overrides)
    return RaceState(**defaults)


def test_order_cop_actions_puts_immediate_capture_first() -> None:
    state = _state(cop_position=(1, 2), thief_position=(2, 2))
    actions = legal_actions(state, AgentRole.COP)
    ordered = order_cop_actions(state, actions)
    assert ordered[0] == AgentAction(ActionType.MOVE, MoveDirection.DOWN)


def test_order_cop_actions_puts_barrier_last() -> None:
    state = _state(cop_position=(2, 2), thief_position=(4, 4))
    actions = legal_actions(state, AgentRole.COP)
    ordered = order_cop_actions(state, actions)
    assert ordered[-1].action_type == ActionType.PLACE_BARRIER


def test_order_thief_actions_puts_the_distance_increasing_move_first() -> None:
    state = _state(cop_position=(2, 0), thief_position=(2, 2))
    actions = legal_actions(state, AgentRole.THIEF)
    ordered = order_thief_actions(state, actions)
    assert ordered[0].direction == MoveDirection.RIGHT
