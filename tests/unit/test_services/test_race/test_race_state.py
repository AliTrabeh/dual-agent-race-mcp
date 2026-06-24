import pytest

from hw6_race.constants import AgentRole, GameOutcome, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.race.exceptions import IllegalActionError, IllegalMoveError
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


@pytest.mark.parametrize(
    "direction,expected",
    [
        (MoveDirection.RIGHT, (2, 3)),
        (MoveDirection.DOWN, (3, 2)),
        (MoveDirection.LEFT, (2, 1)),
        (MoveDirection.UP, (1, 2)),
    ],
)
def test_legal_move_in_each_direction_from_the_center(direction, expected) -> None:
    state = _state(thief_position=(2, 2))
    state.apply_action(AgentRole.THIEF, AgentAction(ActionType.MOVE, direction))
    assert state.thief_position == expected
    assert state.move_count == 1


@pytest.mark.parametrize(
    "position,direction",
    [
        ((0, 2), MoveDirection.UP),
        ((4, 2), MoveDirection.DOWN),
        ((2, 0), MoveDirection.LEFT),
        ((2, 4), MoveDirection.RIGHT),
    ],
)
def test_move_off_each_edge_is_rejected(position, direction) -> None:
    state = _state(thief_position=position)
    with pytest.raises(IllegalMoveError):
        state.apply_action(AgentRole.THIEF, AgentAction(ActionType.MOVE, direction))


def test_cop_moving_onto_thief_triggers_cop_win() -> None:
    state = _state(cop_position=(0, 2), thief_position=(2, 2))
    state.apply_action(AgentRole.THIEF, AgentAction(ActionType.MOVE, MoveDirection.UP))
    assert state.check_outcome() is None
    state.apply_action(AgentRole.COP, AgentAction(ActionType.MOVE, MoveDirection.DOWN))
    assert state.check_outcome() == GameOutcome.COP_WIN


def test_thief_moving_onto_cop_also_triggers_cop_win() -> None:
    state = _state(cop_position=(1, 2), thief_position=(2, 2))
    state.apply_action(AgentRole.THIEF, AgentAction(ActionType.MOVE, MoveDirection.UP))
    assert state.check_outcome() == GameOutcome.COP_WIN


def test_same_cell_start_is_an_immediate_cop_win() -> None:
    state = _state(cop_position=(2, 2), thief_position=(2, 2))
    assert state.check_outcome() == GameOutcome.COP_WIN
    assert state.move_count == 0


def test_thief_survives_to_the_move_limit_with_no_capture() -> None:
    state = _state(cop_position=(0, 0), thief_position=(4, 4), max_moves=4)
    cop_dirs = [MoveDirection.RIGHT, MoveDirection.LEFT]
    thief_dirs = [MoveDirection.LEFT, MoveDirection.RIGHT]
    for i in range(2):
        state.apply_action(AgentRole.THIEF, AgentAction(ActionType.MOVE, thief_dirs[i]))
        state.apply_action(AgentRole.COP, AgentAction(ActionType.MOVE, cop_dirs[i]))
    assert state.move_count == 4
    assert state.check_outcome() == GameOutcome.THIEF_WIN


def test_move_count_below_limit_is_still_ongoing() -> None:
    state = _state(cop_position=(0, 0), thief_position=(4, 4), max_moves=25)
    state.move_count = 24
    assert state.check_outcome() is None


def test_cop_can_place_a_barrier_on_its_own_cell() -> None:
    state = _state(cop_position=(1, 1))
    state.apply_action(AgentRole.COP, AgentAction(ActionType.PLACE_BARRIER))
    assert (1, 1) in state.barriers
    assert state.barriers_placed == 1
    assert state.move_count == 1


def test_cop_placing_a_sixth_barrier_is_rejected() -> None:
    state = _state(cop_position=(0, 0), max_barriers=1)
    state.apply_action(AgentRole.COP, AgentAction(ActionType.PLACE_BARRIER))
    with pytest.raises(IllegalActionError, match="already placed the max"):
        state.apply_action(AgentRole.COP, AgentAction(ActionType.PLACE_BARRIER))


def test_thief_attempting_to_place_a_barrier_is_rejected() -> None:
    state = _state()
    with pytest.raises(IllegalActionError, match="Only the Cop"):
        state.apply_action(AgentRole.THIEF, AgentAction(ActionType.PLACE_BARRIER))


def test_barrier_blocks_only_the_cops_movement_into_that_cell() -> None:
    state = _state(cop_position=(2, 2), thief_position=(0, 0))
    state.apply_action(AgentRole.COP, AgentAction(ActionType.PLACE_BARRIER))

    state.cop_position = (1, 2)  # simulate the Cop having stepped away afterward
    assert state.is_legal_move(AgentRole.COP, MoveDirection.DOWN) is False  # (2,2) is barriered

    state.thief_position = (3, 2)
    assert state.is_legal_move(AgentRole.THIEF, MoveDirection.UP) is True  # Thief passes freely


def test_works_on_a_non_square_grid() -> None:
    state = _state(grid_size=(4, 6), cop_position=(0, 0), thief_position=(3, 5))
    assert state.in_bounds((3, 5)) is True
    assert state.in_bounds((4, 5)) is False
    assert state.in_bounds((3, 6)) is False
