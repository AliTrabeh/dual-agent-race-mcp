import time
from unittest.mock import patch

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType
from hw6_race.services.agents.strategies.minimax.evaluation import evaluate_for_cop
from hw6_race.services.agents.strategies.minimax.search import _search, minimax_decide
from hw6_race.services.agents.strategies.minimax.transposition import TranspositionTable
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


def _deadline(seconds: float = 5.0) -> float:
    return time.monotonic() + seconds


def test_minimax_decide_finds_an_immediate_capture_for_the_cop() -> None:
    state = _state(cop_position=(1, 2), thief_position=(2, 2))
    action = minimax_decide(state, AgentRole.COP, depth=4, deadline=_deadline())
    assert action.action_type == ActionType.MOVE
    assert action.direction == MoveDirection.DOWN


def test_minimax_decide_returns_a_legal_move_for_the_thief() -> None:
    state = _state(cop_position=(0, 0), thief_position=(4, 4))
    action = minimax_decide(state, AgentRole.THIEF, depth=4, deadline=_deadline())
    assert action.action_type == ActionType.MOVE
    assert action.direction in (MoveDirection.UP, MoveDirection.LEFT)


def test_minimax_decide_returns_none_when_the_deadline_has_already_passed() -> None:
    state = _state(cop_position=(0, 0), thief_position=(4, 4))
    expired_deadline = time.monotonic() - 1.0
    action = minimax_decide(state, AgentRole.COP, depth=6, deadline=expired_deadline)
    assert action is None


def test_minimax_decide_returns_none_when_no_legal_actions_exist() -> None:
    # Thief boxed into a 1x1 grid has zero legal moves.
    state = RaceState(grid_size=(1, 1), max_moves=5, max_barriers=0, cop_position=(0, 0), thief_position=(0, 0))
    action = minimax_decide(state, AgentRole.THIEF, depth=4, deadline=_deadline())
    assert action is None


def test_deeper_search_still_returns_a_legal_action() -> None:
    state = _state(cop_position=(0, 0), thief_position=(4, 4))
    action = minimax_decide(state, AgentRole.COP, depth=8, deadline=_deadline())
    assert action is not None


def test_minimax_decide_returns_none_when_the_deadline_expires_mid_search() -> None:
    state = _state(cop_position=(2, 2), thief_position=(4, 4))
    with patch(
        "hw6_race.services.agents.strategies.minimax.search.time.monotonic",
        side_effect=[0.0, 0.0, 200.0],
    ):
        action = minimax_decide(state, AgentRole.COP, depth=2, deadline=100.0)
    assert action is None


def test_search_returns_the_leaf_evaluation_when_no_legal_actions_remain() -> None:
    # Cop fully boxed in by barriers, with the barrier cap reached: zero legal actions,
    # but the game is not yet terminal (the Thief is elsewhere).
    state = RaceState(
        grid_size=(3, 3),
        max_moves=25,
        max_barriers=4,
        cop_position=(1, 1),
        thief_position=(0, 0),
        barriers={(0, 1), (1, 0), (1, 2), (2, 1)},
        barriers_placed=4,
    )
    score = _search(
        state,
        AgentRole.COP,
        AgentRole.COP,
        depth=3,
        alpha=float("-inf"),
        beta=float("inf"),
        deadline=_deadline(),
        table=TranspositionTable(),
        evaluate=evaluate_for_cop,
    )
    assert score == evaluate_for_cop(state)
