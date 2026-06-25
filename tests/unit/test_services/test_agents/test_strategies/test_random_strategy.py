import random

from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.random_strategy import RandomDecisionStrategy


def _observation(**overrides) -> AgentObservation:
    defaults = {
        "own_position": (2, 2),
        "grid_size": (5, 5),
        "barriers_remaining": 5,
        "role": AgentRole.THIEF,
    }
    defaults.update(overrides)
    return AgentObservation(**defaults)


def test_decide_returns_a_move_action() -> None:
    strategy = RandomDecisionStrategy(rng=random.Random(0))
    action = strategy.decide(_observation())
    assert action.action_type == ActionType.MOVE


def test_decide_never_picks_a_direction_that_leaves_the_grid() -> None:
    strategy = RandomDecisionStrategy(rng=random.Random(0))
    for _ in range(20):
        action = strategy.decide(_observation(own_position=(0, 0)))
        assert action.direction.value in ("down", "right")


def test_decide_is_deterministic_with_a_seeded_rng() -> None:
    first = RandomDecisionStrategy(rng=random.Random(42)).decide(_observation())
    second = RandomDecisionStrategy(rng=random.Random(42)).decide(_observation())
    assert first == second


def test_decide_uses_a_real_rng_by_default() -> None:
    strategy = RandomDecisionStrategy()
    action = strategy.decide(_observation())
    assert action.action_type == ActionType.MOVE
