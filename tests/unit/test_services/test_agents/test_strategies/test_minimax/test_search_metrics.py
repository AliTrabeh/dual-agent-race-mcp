from hw6_race.constants import AgentRole
from hw6_race.services.agents.strategies.minimax.search_metrics import (
    bfs_distance,
    cop_threat_positions,
    distance_for_role,
    is_safe_for_thief,
    mobility_for_role,
    reachable_area,
    reachable_area_for_role,
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


def test_bfs_distance_on_an_open_grid_equals_manhattan_distance() -> None:
    assert bfs_distance((5, 5), frozenset(), (0, 0), (4, 4)) == 8


def test_bfs_distance_is_zero_for_the_same_cell() -> None:
    assert bfs_distance((5, 5), frozenset(), (2, 2), (2, 2)) == 0


def test_bfs_distance_routes_around_a_blocking_cell() -> None:
    # (0,1) blocked: (0,0)->(0,2) must detour, e.g. via (1,0)/(1,1)/(1,2) or (0,0)->(1,0)->(1,1)->(0,1)? no, (0,1) itself blocked
    distance = bfs_distance((3, 3), frozenset({(0, 1)}), (0, 0), (0, 2))
    assert distance == 4  # (0,0)->(1,0)->(1,1)->(1,2)->(0,2)


def test_bfs_distance_returns_none_when_fully_boxed_in() -> None:
    # Corner (0,0) on a 3x3 grid has exactly 2 neighbors: (0,1) and (1,0). Block both.
    distance = bfs_distance((3, 3), frozenset({(0, 1), (1, 0)}), (0, 0), (2, 2))
    assert distance is None


def test_reachable_area_on_an_open_grid_is_the_whole_grid() -> None:
    assert reachable_area((3, 3), frozenset(), (0, 0)) == 9


def test_reachable_area_shrinks_when_boxed_in() -> None:
    assert reachable_area((3, 3), frozenset({(0, 1), (1, 0)}), (0, 0)) == 1


def test_distance_for_role_cop_respects_barriers() -> None:
    state = _state(cop_position=(0, 0), thief_position=(2, 2), barriers={(0, 1), (1, 0)})
    assert distance_for_role(state, AgentRole.COP) is None


def test_distance_for_role_thief_ignores_barriers() -> None:
    state = _state(cop_position=(0, 0), thief_position=(2, 2), barriers={(0, 1), (1, 0)})
    assert distance_for_role(state, AgentRole.THIEF) == 4


def test_reachable_area_for_role_cop_respects_barriers() -> None:
    state = _state(cop_position=(0, 0), grid_size=(3, 3), barriers={(0, 1), (1, 0)})
    assert reachable_area_for_role(state, AgentRole.COP) == 1


def test_mobility_for_role_counts_only_move_actions() -> None:
    state = _state(cop_position=(0, 0))
    assert mobility_for_role(state, AgentRole.COP) == 2  # RIGHT, DOWN only at the corner


def test_cop_threat_positions_includes_current_cell_and_legal_destinations() -> None:
    state = _state(cop_position=(2, 2))
    threats = cop_threat_positions(state)
    assert (2, 2) in threats
    assert (2, 3) in threats
    assert (1, 2) in threats
    assert len(threats) == 5  # stay + 4 legal directions from the center


def test_is_safe_for_thief_false_when_cop_threatens_the_cell() -> None:
    state = _state(cop_position=(2, 2))
    assert is_safe_for_thief(state, (2, 3)) is False


def test_is_safe_for_thief_true_when_far_from_any_cop_threat() -> None:
    state = _state(cop_position=(0, 0))
    assert is_safe_for_thief(state, (4, 4)) is True
