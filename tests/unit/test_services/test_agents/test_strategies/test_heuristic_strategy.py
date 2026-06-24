import pytest

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy


@pytest.fixture
def strategy() -> HeuristicStrategy:
    return HeuristicStrategy()


def _observation(position: tuple[int, int], grid_size: tuple[int, int] = (5, 5)) -> AgentObservation:
    return AgentObservation(own_position=position, grid_size=grid_size, barriers_remaining=0)


def test_top_left_corner_moves_right(strategy: HeuristicStrategy) -> None:
    action = strategy.decide(_observation((0, 0)))
    assert action.action_type == ActionType.MOVE
    assert action.direction == MoveDirection.RIGHT


def test_bottom_right_corner_moves_left(strategy: HeuristicStrategy) -> None:
    action = strategy.decide(_observation((4, 4)))
    assert action.direction == MoveDirection.LEFT


def test_top_right_corner_moves_down(strategy: HeuristicStrategy) -> None:
    action = strategy.decide(_observation((0, 4)))
    assert action.direction == MoveDirection.DOWN


def test_bottom_left_corner_moves_right(strategy: HeuristicStrategy) -> None:
    action = strategy.decide(_observation((4, 0)))
    assert action.direction == MoveDirection.RIGHT


def test_never_chooses_to_place_a_barrier(strategy: HeuristicStrategy) -> None:
    for position in [(0, 0), (4, 4), (2, 2), (0, 4), (4, 0)]:
        action = strategy.decide(_observation(position))
        assert action.action_type == ActionType.MOVE


@pytest.mark.parametrize(
    "position",
    [(0, 0), (1, 1), (2, 2), (4, 4), (0, 4), (4, 0), (3, 1)],
)
def test_chosen_move_always_stays_within_grid_bounds(
    strategy: HeuristicStrategy, position: tuple[int, int]
) -> None:
    observation = _observation(position)
    action = strategy.decide(observation)
    delta = {
        MoveDirection.UP: (-1, 0),
        MoveDirection.DOWN: (1, 0),
        MoveDirection.LEFT: (0, -1),
        MoveDirection.RIGHT: (0, 1),
    }[action.direction]
    new_row = position[0] + delta[0]
    new_col = position[1] + delta[1]
    assert 0 <= new_row < observation.grid_size[0]
    assert 0 <= new_col < observation.grid_size[1]


def test_works_on_a_non_square_grid(strategy: HeuristicStrategy) -> None:
    action = strategy.decide(_observation((0, 0), grid_size=(4, 6)))
    assert action.direction == MoveDirection.RIGHT


def test_falls_back_to_first_priority_direction_on_a_1x1_grid(strategy: HeuristicStrategy) -> None:
    """Documented out-of-scope edge case (no legal move exists on a 1x1 grid)."""
    action = strategy.decide(_observation((0, 0), grid_size=(1, 1)))
    assert action.direction == MoveDirection.RIGHT
