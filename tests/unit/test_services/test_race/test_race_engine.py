"""Tests use scripted/stateless policy stubs, not real DecisionStrategy objects —
the engine has no knowledge of agents/LLMs, only of (RaceState) -> AgentAction
callables, per PRD-003 scope. Policies read only from the passed-in RaceState
(no internal counters) so they stay safe to reuse across many sub-games, exactly
like a real DecisionStrategy would behave.
"""

from hw6_race.constants import GameOutcome, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.race.models import GameResult
from hw6_race.services.race.race_engine import default_start_positions, play_game, play_sub_game


def _fixed_policy(direction: MoveDirection):
    return lambda state: AgentAction(ActionType.MOVE, direction)


def _cop_bounce_policy(state) -> AgentAction:
    """Oscillates the Cop between column 0 and 1 forever — never approaches a
    Thief pinned to the far side of the grid."""
    col = state.cop_position[1]
    direction = MoveDirection.RIGHT if col == 0 else MoveDirection.LEFT
    return AgentAction(ActionType.MOVE, direction)


def _thief_bounce_policy(state) -> AgentAction:
    """Oscillates the Thief between the two rightmost columns forever."""
    col = state.thief_position[1]
    max_col = state.grid_size[1] - 1
    direction = MoveDirection.LEFT if col == max_col else MoveDirection.RIGHT
    return AgentAction(ActionType.MOVE, direction)


def test_default_start_positions_are_opposite_corners(sample_game_config) -> None:
    cop_start, thief_start = default_start_positions(sample_game_config)
    assert cop_start == (0, 0)
    assert thief_start == (4, 4)


def test_play_sub_game_reaches_cop_win_when_paths_cross(sample_game_config) -> None:
    result = play_sub_game(
        sample_game_config,
        thief_policy=_fixed_policy(MoveDirection.UP),
        cop_policy=_fixed_policy(MoveDirection.DOWN),
        cop_start=(0, 2),
        thief_start=(2, 2),
    )
    assert result.outcome == GameOutcome.COP_WIN
    assert result.move_count == 2
    assert result.cop_points == 20
    assert result.thief_points == 5


def test_play_sub_game_reaches_thief_win_when_paths_never_cross(sample_game_config) -> None:
    result = play_sub_game(
        sample_game_config,
        thief_policy=_thief_bounce_policy,
        cop_policy=_cop_bounce_policy,
        cop_start=(0, 0),
        thief_start=(4, 4),
    )
    assert result.outcome == GameOutcome.THIEF_WIN
    assert result.move_count == sample_game_config.max_moves
    assert result.cop_points == 5
    assert result.thief_points == 10


def test_play_game_runs_six_independent_thief_win_sub_games(sample_game_config) -> None:
    """Stateless bounce policies stay safe to reuse across all 6 sub-games."""
    result = play_game(
        sample_game_config,
        thief_policy=_thief_bounce_policy,
        cop_policy=_cop_bounce_policy,
    )
    assert len(result.sub_games) == 6
    assert all(sg.outcome == GameOutcome.THIEF_WIN for sg in result.sub_games)
    assert result.total_cop_points == 6 * 5
    assert result.total_thief_points == 6 * 10


def test_play_game_aggregates_exact_totals_across_six_sub_games(sample_game_config) -> None:
    """4 Cop wins + 2 Thief wins -> matches the HW PDF's example totals (90/40)."""
    sub_games = [
        play_sub_game(
            sample_game_config,
            thief_policy=_fixed_policy(MoveDirection.UP),
            cop_policy=_fixed_policy(MoveDirection.DOWN),
            cop_start=(0, 2),
            thief_start=(2, 2),
        )
        for _ in range(4)
    ] + [
        play_sub_game(
            sample_game_config,
            thief_policy=_thief_bounce_policy,
            cop_policy=_cop_bounce_policy,
            cop_start=(0, 0),
            thief_start=(4, 4),
        )
        for _ in range(2)
    ]

    result = GameResult(sub_games=sub_games)

    assert len(result.sub_games) == 6
    assert result.total_cop_points == 90
    assert result.total_thief_points == 40
