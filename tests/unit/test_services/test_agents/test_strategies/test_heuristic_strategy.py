import pytest

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy


@pytest.fixture
def strategy() -> HeuristicStrategy:
    return HeuristicStrategy()


def _observation(
    position: tuple[int, int],
    grid_size: tuple[int, int] = (5, 5),
    role: AgentRole | None = None,
    believed_opponent_position: tuple[int, int] | None = None,
) -> AgentObservation:
    return AgentObservation(
        own_position=position,
        grid_size=grid_size,
        barriers_remaining=0,
        role=role,
        believed_opponent_position=believed_opponent_position,
    )


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


def test_cop_chases_toward_the_believed_opponent_position(strategy: HeuristicStrategy) -> None:
    observation = _observation(
        (0, 2), role=AgentRole.COP, believed_opponent_position=(4, 2)
    )
    action = strategy.decide(observation)
    assert action.direction == MoveDirection.DOWN  # minimizes distance to (4, 2)


def test_thief_flees_from_the_believed_opponent_position(strategy: HeuristicStrategy) -> None:
    observation = _observation(
        (0, 0), role=AgentRole.THIEF, believed_opponent_position=(0, 1)
    )
    action = strategy.decide(observation)
    assert action.direction == MoveDirection.DOWN  # maximizes distance from (0, 1)


def test_belief_without_a_role_falls_back_to_the_default_move(strategy: HeuristicStrategy) -> None:
    """Guards the (role=None, belief=set) combination, which shouldn't occur in
    practice since observation_for() always supplies a role, but must not crash."""
    observation = _observation((0, 0), role=None, believed_opponent_position=(4, 4))
    action = strategy.decide(observation)
    assert action.direction == MoveDirection.RIGHT


def test_chase_falls_back_to_default_when_no_legal_candidate_exists(
    strategy: HeuristicStrategy,
) -> None:
    """A belief is present but the grid is too small for any legal move (1x1)."""
    observation = _observation(
        (0, 0), grid_size=(1, 1), role=AgentRole.COP, believed_opponent_position=(0, 0)
    )
    action = strategy.decide(observation)
    assert action.direction == MoveDirection.RIGHT
