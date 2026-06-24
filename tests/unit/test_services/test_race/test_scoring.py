from hw6_race.constants import GameOutcome
from hw6_race.services.race.scoring import score_sub_game


def test_cop_win_scores_from_default_config(sample_game_config) -> None:
    result = score_sub_game(GameOutcome.COP_WIN, move_count=10, config=sample_game_config)
    assert result.cop_points == 20
    assert result.thief_points == 5
    assert result.outcome == GameOutcome.COP_WIN
    assert result.move_count == 10


def test_thief_win_scores_from_default_config(sample_game_config) -> None:
    result = score_sub_game(GameOutcome.THIEF_WIN, move_count=25, config=sample_game_config)
    assert result.cop_points == 5
    assert result.thief_points == 10


def test_technical_loss_scores_zero_for_both(sample_game_config) -> None:
    result = score_sub_game(GameOutcome.TECHNICAL_LOSS, move_count=3, config=sample_game_config)
    assert result.cop_points == 0
    assert result.thief_points == 0


def test_scoring_respects_a_custom_config(sample_config_data, sample_game_config) -> None:
    from hw6_race.shared.config import GameConfig

    sample_config_data["scoring"] = {
        "cop_win": 100,
        "thief_win": 50,
        "cop_loss": 1,
        "thief_loss": 2,
    }
    custom_config = GameConfig(sample_config_data)

    cop_win_result = score_sub_game(GameOutcome.COP_WIN, move_count=1, config=custom_config)
    thief_win_result = score_sub_game(GameOutcome.THIEF_WIN, move_count=1, config=custom_config)

    assert (cop_win_result.cop_points, cop_win_result.thief_points) == (100, 2)
    assert (thief_win_result.cop_points, thief_win_result.thief_points) == (1, 50)
