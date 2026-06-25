from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType
from hw6_race.services.agents.strategies.minimax.board_utils import clone_state
from hw6_race.services.agents.strategies.minimax.fallback import fallback_action
from hw6_race.services.agents.strategies.minimax.search_metrics import is_safe_for_thief
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


def test_cop_fallback_captures_when_adjacent() -> None:
    state = _state(cop_position=(1, 2), thief_position=(2, 2))
    action = fallback_action(state, AgentRole.COP)
    assert action.action_type == ActionType.MOVE
    assert action.direction == MoveDirection.DOWN


def test_thief_fallback_never_walks_into_the_cop() -> None:
    state = _state(cop_position=(2, 2), thief_position=(2, 3))
    action = fallback_action(state, AgentRole.THIEF)
    assert action.action_type == ActionType.MOVE
    assert action.direction != MoveDirection.LEFT


def test_thief_fallback_only_picks_a_move_the_cop_cannot_threaten_next() -> None:
    # Thief at (2,2): only LEFT->(2,1) is threatened by cop at (2,0); the rest are safe.
    state = _state(cop_position=(2, 0), thief_position=(2, 2))
    action = fallback_action(state, AgentRole.THIEF)

    next_state = clone_state(state)
    next_state.apply_action(AgentRole.THIEF, action)
    assert is_safe_for_thief(state, next_state.thief_position)


def test_thief_fallback_never_returns_a_barrier_action() -> None:
    state = _state(thief_position=(2, 2))
    action = fallback_action(state, AgentRole.THIEF)
    assert action.action_type != ActionType.PLACE_BARRIER
