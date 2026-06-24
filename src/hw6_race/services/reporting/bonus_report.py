"""Inter-Group Bonus Game JSON schema (HW-F24) and scoring (HW-F28)."""

from dataclasses import dataclass
from typing import Any


def compute_bonus_claim(totals_by_group: dict[str, int]) -> dict[str, int]:
    """Apply HW-F28's per-pairing rule: winner gets 10, loser gets 7, exact tie 5 each."""
    if len(totals_by_group) != 2:
        raise ValueError("Bonus scoring requires exactly 2 groups")
    (name_a, score_a), (name_b, score_b) = totals_by_group.items()
    if score_a == score_b:
        return {name_a: 5, name_b: 5}
    winner, loser = (name_a, name_b) if score_a > score_b else (name_b, name_a)
    return {winner: 10, loser: 7}


@dataclass
class InterGroupBonusReport:
    """Cross-group bonus-round report; both groups must send matching data (HW-F28).

    Input: both groups' metadata + agreed sub_games/totals (Setup/Input data).
    Output: a dict matching the HW PDF's literal bonus JSON example field-for-field.
    """

    group_1_name: str
    group_2_name: str
    github_repo_group_1: str
    github_repo_group_2: str
    mcp_url_group_1_cop: str
    mcp_url_group_1_thief: str
    mcp_url_group_2_cop: str
    mcp_url_group_2_thief: str
    timezone: str
    students_group_1: list[str]
    students_group_2: list[str]
    sub_games: list[dict[str, Any]]
    totals_by_group: dict[str, int]
    mutual_agreement: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "report_type": "bonus_game",
            "groups": {"group_1": self.group_1_name, "group_2": self.group_2_name},
            "github_repo_group_1": self.github_repo_group_1,
            "github_repo_group_2": self.github_repo_group_2,
            "mcp_url_group_1_cop": self.mcp_url_group_1_cop,
            "mcp_url_group_1_thief": self.mcp_url_group_1_thief,
            "mcp_url_group_2_cop": self.mcp_url_group_2_cop,
            "mcp_url_group_2_thief": self.mcp_url_group_2_thief,
            "timezone": self.timezone,
            "students_group_1": self.students_group_1,
            "students_group_2": self.students_group_2,
            "sub_games": self.sub_games,
            "totals_by_group": self.totals_by_group,
            "bonus_claim": compute_bonus_claim(self.totals_by_group),
            "mutual_agreement": self.mutual_agreement,
        }
