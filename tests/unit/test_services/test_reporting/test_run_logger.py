from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import SubGameResult
from hw6_race.services.reporting.run_logger import RunLogger


def _logger() -> RunLogger:
    return RunLogger(
        group_name="Team-Alpha",
        students=["s1"],
        github_repo="https://github.com/team-alpha/repo",
        cop_mcp_url="https://cop.example.com",
        thief_mcp_url="https://thief.example.com",
        timezone="Asia/Jerusalem",
    )


def test_record_increments_recorded_count() -> None:
    logger = _logger()
    sub_game = SubGameResult(outcome=GameOutcome.COP_WIN, move_count=10, cop_points=20, thief_points=5)
    logger.record(sub_game)
    logger.record(sub_game)
    assert logger.recorded_count == 2


def test_build_report_reflects_everything_recorded_so_far() -> None:
    logger = _logger()
    logger.record(SubGameResult(GameOutcome.COP_WIN, 10, 20, 5))
    logger.record(SubGameResult(GameOutcome.THIEF_WIN, 25, 5, 10))

    report = logger.build_report()

    assert report.group_name == "Team-Alpha"
    assert report.totals == {"cop": 25, "thief": 15}
    assert len(report.sub_games) == 2


def test_build_report_with_nothing_recorded_yet_has_zero_totals() -> None:
    report = _logger().build_report()
    assert report.totals == {"cop": 0, "thief": 0}
    assert report.sub_games == []
