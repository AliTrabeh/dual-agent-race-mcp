"""Race-domain result dataclasses. Action types are reused from
services.agents.models — never redefined here (SG-C04).
"""

from dataclasses import dataclass, field

from hw6_race.constants import GameOutcome


@dataclass(frozen=True)
class SubGameResult:
    """The scored outcome of one completed sub-game (Output data)."""

    outcome: GameOutcome
    move_count: int
    cop_points: int
    thief_points: int


@dataclass
class GameResult:
    """The aggregated outcome of a full match (Output data: 6 SubGameResults)."""

    sub_games: list[SubGameResult] = field(default_factory=list)

    @property
    def total_cop_points(self) -> int:
        return sum(sub_game.cop_points for sub_game in self.sub_games)

    @property
    def total_thief_points(self) -> int:
        return sum(sub_game.thief_points for sub_game in self.sub_games)
