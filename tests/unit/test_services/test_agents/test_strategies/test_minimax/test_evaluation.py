from hw6_race.services.agents.strategies.minimax.evaluation import (
    WIN_SCORE,
    evaluate_for_cop,
    evaluate_for_thief,
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


def test_evaluate_for_cop_scores_a_capture_as_the_win_score() -> None:
    state = _state(cop_position=(2, 2), thief_position=(2, 2))
    assert evaluate_for_cop(state) == WIN_SCORE


def test_evaluate_for_cop_scores_thief_survival_as_negative_win_score() -> None:
    state = _state(move_count=25, max_moves=25)
    assert evaluate_for_cop(state) == -WIN_SCORE


def test_evaluate_for_thief_scores_survival_as_the_win_score() -> None:
    state = _state(move_count=25, max_moves=25)
    assert evaluate_for_thief(state) == WIN_SCORE


def test_evaluate_for_thief_scores_a_capture_as_negative_win_score() -> None:
    state = _state(cop_position=(2, 2), thief_position=(2, 2))
    assert evaluate_for_thief(state) == -WIN_SCORE


def test_evaluate_for_cop_prefers_being_closer_to_the_thief() -> None:
    far = _state(cop_position=(0, 0), thief_position=(4, 4))
    near = _state(cop_position=(3, 3), thief_position=(4, 4))
    assert evaluate_for_cop(near) > evaluate_for_cop(far)


def test_evaluate_for_thief_prefers_being_farther_from_the_cop() -> None:
    far = _state(cop_position=(0, 0), thief_position=(4, 4))
    near = _state(cop_position=(3, 3), thief_position=(4, 4))
    assert evaluate_for_thief(far) > evaluate_for_thief(near)
