"""Internal Game JSON schema (HW-F23) — exact field names from the HW PDF example.

`build_sub_games_payload` is shared with bonus_report.py so the per-sub-game
dict shape is defined exactly once (SG-C04).
"""

from dataclasses import dataclass, field
from typing import Any

from hw6_race.services.race.models import GameResult


def build_sub_games_payload(result: GameResult) -> list[dict[str, Any]]:
    """Build the `sub_games` array shared by both report types."""
    return [
        {
            "index": index,
            "outcome": sub_game.outcome.value,
            "move_count": sub_game.move_count,
            "cop_points": sub_game.cop_points,
            "thief_points": sub_game.thief_points,
        }
        for index, sub_game in enumerate(result.sub_games, start=1)
    ]


@dataclass
class InternalGameReport:
    """Per-group match report, emailed automatically after the 6th sub-game (HW-F21).

    Input: group/MCP metadata + a GameResult (Setup/Input data). Output: a dict
    matching the HW PDF's literal Internal Game JSON example field-for-field.
    """

    group_name: str
    students: list[str]
    github_repo: str
    cop_mcp_url: str
    thief_mcp_url: str
    timezone: str
    sub_games: list[dict[str, Any]] = field(default_factory=list)
    totals: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "group_name": self.group_name,
            "students": self.students,
            "github_repo": self.github_repo,
            "cop_mcp_url": self.cop_mcp_url,
            "thief_mcp_url": self.thief_mcp_url,
            "timezone": self.timezone,
            "sub_games": self.sub_games,
            "totals": self.totals,
        }

    @classmethod
    def from_game_result(
        cls,
        *,
        group_name: str,
        students: list[str],
        github_repo: str,
        cop_mcp_url: str,
        thief_mcp_url: str,
        timezone: str,
        result: GameResult,
    ) -> "InternalGameReport":
        return cls(
            group_name=group_name,
            students=students,
            github_repo=github_repo,
            cop_mcp_url=cop_mcp_url,
            thief_mcp_url=thief_mcp_url,
            timezone=timezone,
            sub_games=build_sub_games_payload(result),
            totals={"cop": result.total_cop_points, "thief": result.total_thief_points},
        )
