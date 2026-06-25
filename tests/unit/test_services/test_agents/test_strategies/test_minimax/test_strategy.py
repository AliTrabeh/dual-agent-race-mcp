from unittest.mock import patch

from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.minimax.strategy import MinimaxDecisionStrategy


def _observation(**overrides) -> AgentObservation:
    defaults = {
        "own_position": (1, 2),
        "grid_size": (5, 5),
        "barriers_remaining": 5,
        "role": AgentRole.COP,
        "believed_opponent_position": (2, 2),
        "max_moves": 25,
        "max_barriers": 5,
    }
    defaults.update(overrides)
    return AgentObservation(**defaults)


def test_decide_returns_a_legal_capture_move_when_one_exists() -> None:
    strategy = MinimaxDecisionStrategy(depth=4)
    action = strategy.decide(_observation())
    assert action.action_type == ActionType.MOVE


def test_decide_uses_the_default_prior_on_the_first_call_without_a_belief() -> None:
    strategy = MinimaxDecisionStrategy(depth=4)
    observation = _observation(believed_opponent_position=None, own_position=(0, 0))
    action = strategy.decide(observation)
    assert action is not None
    assert strategy._estimated_opponent_position == (4, 4)


def test_decide_remembers_the_last_belief_when_a_new_one_is_not_available() -> None:
    strategy = MinimaxDecisionStrategy(depth=4)
    strategy.decide(_observation(believed_opponent_position=(3, 3)))
    action = strategy.decide(_observation(believed_opponent_position=None))
    assert action is not None
    assert strategy._estimated_opponent_position == (3, 3)


def test_decide_falls_back_to_the_heuristic_when_search_finds_nothing() -> None:
    strategy = MinimaxDecisionStrategy(depth=4)
    with patch(
        "hw6_race.services.agents.strategies.minimax.strategy.minimax_decide", return_value=None
    ):
        action = strategy.decide(_observation())
    assert action.action_type == ActionType.MOVE


def test_decide_falls_back_to_the_heuristic_when_search_raises() -> None:
    strategy = MinimaxDecisionStrategy(depth=4)
    with patch(
        "hw6_race.services.agents.strategies.minimax.strategy.minimax_decide",
        side_effect=RuntimeError("boom"),
    ):
        action = strategy.decide(_observation())
    assert action.action_type == ActionType.MOVE
