import pytest

from hw6_race.services.reporting.bonus_report import InterGroupBonusReport, compute_bonus_claim


def test_compute_bonus_claim_winner_gets_ten_loser_gets_seven() -> None:
    claim = compute_bonus_claim({"Team-Alpha": 90, "Team-Beta": 60})
    assert claim == {"Team-Alpha": 10, "Team-Beta": 7}


def test_compute_bonus_claim_handles_either_order() -> None:
    claim = compute_bonus_claim({"Team-Beta": 60, "Team-Alpha": 90})
    assert claim == {"Team-Alpha": 10, "Team-Beta": 7}


def test_compute_bonus_claim_exact_tie_splits_five_each() -> None:
    claim = compute_bonus_claim({"Team-Alpha": 75, "Team-Beta": 75})
    assert claim == {"Team-Alpha": 5, "Team-Beta": 5}


def test_compute_bonus_claim_rejects_other_than_two_groups() -> None:
    with pytest.raises(ValueError, match="exactly 2 groups"):
        compute_bonus_claim({"Team-Alpha": 90})


def test_inter_group_bonus_report_to_json_matches_the_hw_pdf_example_field_names() -> None:
    """Field names must match docs/00_source_analysis.md HW-F24's literal example."""
    report = InterGroupBonusReport(
        group_1_name="Team-Alpha",
        group_2_name="Team-Beta",
        github_repo_group_1="https://github.com/team-alpha/marl-cop-thief",
        github_repo_group_2="https://github.com/team-beta/marl-cop-thief",
        mcp_url_group_1_cop="https://cop-mcp-alpha.prefect.run",
        mcp_url_group_1_thief="https://thief-mcp-alpha.prefect.run",
        mcp_url_group_2_cop="https://cop-mcp-beta.prefect.run",
        mcp_url_group_2_thief="https://thief-mcp-beta.prefect.run",
        timezone="Asia/Jerusalem",
        students_group_1=[],
        students_group_2=[],
        sub_games=[],
        totals_by_group={"Team-Alpha": 60, "Team-Beta": 80},
        mutual_agreement=True,
    )
    payload = report.to_json()
    assert payload["report_type"] == "bonus_game"
    assert payload["groups"] == {"group_1": "Team-Alpha", "group_2": "Team-Beta"}
    assert payload["github_repo_group_1"] == "https://github.com/team-alpha/marl-cop-thief"
    assert payload["mcp_url_group_2_thief"] == "https://thief-mcp-beta.prefect.run"
    assert payload["totals_by_group"] == {"Team-Alpha": 60, "Team-Beta": 80}
    assert payload["bonus_claim"] == {"Team-Beta": 10, "Team-Alpha": 7}
    assert payload["mutual_agreement"] is True
