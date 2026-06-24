"""Accumulates per-sub-game results into the Internal Game JSON structure as a
match progresses (HW-F23) — independent of how/when sub-games are produced,
so a future orchestrator integration can call `record()` after each sub-game.
"""

from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.reporting.schemas import InternalGameReport


class RunLogger:
    """Setup: group/MCP metadata (Setup data). Input: SubGameResults via
    record(). Output: a finalized InternalGameReport via build_report().
    """

    def __init__(
        self,
        *,
        group_name: str,
        students: list[str],
        github_repo: str,
        cop_mcp_url: str,
        thief_mcp_url: str,
        timezone: str,
    ) -> None:
        self._group_name = group_name
        self._students = students
        self._github_repo = github_repo
        self._cop_mcp_url = cop_mcp_url
        self._thief_mcp_url = thief_mcp_url
        self._timezone = timezone
        self._sub_games: list[SubGameResult] = []

    def record(self, sub_game: SubGameResult) -> None:
        """Append one completed sub-game's result to the running log."""
        self._sub_games.append(sub_game)

    @property
    def recorded_count(self) -> int:
        return len(self._sub_games)

    def build_report(self) -> InternalGameReport:
        """Build the Internal Game JSON report from everything recorded so far."""
        result = GameResult(sub_games=list(self._sub_games))
        return InternalGameReport.from_game_result(
            group_name=self._group_name,
            students=self._students,
            github_repo=self._github_repo,
            cop_mcp_url=self._cop_mcp_url,
            thief_mcp_url=self._thief_mcp_url,
            timezone=self._timezone,
            result=result,
        )
