from hw6_race.services.agents.strategies.minimax.features import (
    _UNREACHABLE_DISTANCE_PENALTY,
    compute_features,
)
from hw6_race.services.race.race_state import RaceState


def test_compute_features_on_an_open_grid() -> None:
    state = RaceState(
        grid_size=(5, 5), max_moves=25, max_barriers=5, cop_position=(0, 0), thief_position=(4, 4)
    )
    features = compute_features(state)

    assert features.cop_thief_distance == 8
    assert features.cop_mobility == 2
    assert features.thief_mobility == 2
    assert features.cop_reachable_area == 25
    assert features.thief_reachable_area == 25
    assert features.barriers_used == 0
    assert features.barriers_remaining == 5


def test_compute_features_uses_the_penalty_when_cop_is_boxed_in() -> None:
    state = RaceState(
        grid_size=(3, 3),
        max_moves=25,
        max_barriers=5,
        cop_position=(0, 0),
        thief_position=(2, 2),
        barriers={(0, 1), (1, 0)},
    )
    features = compute_features(state)

    assert features.cop_thief_distance == _UNREACHABLE_DISTANCE_PENALTY
    assert features.cop_reachable_area == 1
