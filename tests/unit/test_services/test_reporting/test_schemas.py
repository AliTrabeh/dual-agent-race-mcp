from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.reporting.schemas import InternalGameReport, build_sub_games_payload


def _game_result() -> GameResult:
    return GameResult(
        sub_games=[
            SubGameResult(outcome=GameOutcome.COP_WIN, move_count=16, cop_points=20, thief_points=5),
            SubGameResult(outcome=GameOutcome.THIEF_WIN, move_count=25, cop_points=5, thief_points=10),
        ]
    )


def test_build_sub_games_payload_preserves_order_and_fields() -> None:
    payload = build_sub_games_payload(_game_result())
    assert payload == [
        {"index": 1, "outcome": "cop_win", "move_count": 16, "cop_points": 20, "thief_points": 5},
        {"index": 2, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10},
    ]


def test_internal_game_report_to_json_matches_the_hw_pdf_example_field_names() -> None:
    """Field names must match docs/00_source_analysis.md HW-F23's literal example."""
    report = InternalGameReport(
        group_name="Team-Alpha",
        students=[],
        github_repo="https://github.com/team-alpha/marl-cop-thief",
        cop_mcp_url="https://cop-mcp-alpha.prefect.run",
        thief_mcp_url="https://thief-mcp-alpha.prefect.run",
        timezone="Asia/Jerusalem",
        sub_games=[],
        totals={"cop": 90, "thief": 40},
    )
    assert report.to_json() == {
        "group_name": "Team-Alpha",
        "students": [],
        "github_repo": "https://github.com/team-alpha/marl-cop-thief",
        "cop_mcp_url": "https://cop-mcp-alpha.prefect.run",
        "thief_mcp_url": "https://thief-mcp-alpha.prefect.run",
        "timezone": "Asia/Jerusalem",
        "sub_games": [],
        "totals": {"cop": 90, "thief": 40},
    }


def test_internal_game_report_from_game_result_computes_totals() -> None:
    report = InternalGameReport.from_game_result(
        group_name="Team-Alpha",
        students=["s1"],
        github_repo="https://github.com/team-alpha/repo",
        cop_mcp_url="https://cop.example.com",
        thief_mcp_url="https://thief.example.com",
        timezone="Asia/Jerusalem",
        result=_game_result(),
    )
    assert report.totals == {"cop": 25, "thief": 15}
    assert len(report.sub_games) == 2
