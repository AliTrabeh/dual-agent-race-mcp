"""Scoring table lookups from config (HW-F11). No hard-coded point values.

`GameOutcome.TECHNICAL_LOSS` scores 0/0 here — Chunk 7's reporting layer owns
the rerun bookkeeping that keeps a Technical Loss out of the final totals.
"""

from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import SubGameResult
from hw6_race.shared.config import GameConfig


def score_sub_game(outcome: GameOutcome, move_count: int, config: GameConfig) -> SubGameResult:
    """Return a SubGameResult with points looked up from `config.scoring`."""
    scoring = config.scoring
    if outcome == GameOutcome.COP_WIN:
        cop_points, thief_points = scoring["cop_win"], scoring["thief_loss"]
    elif outcome == GameOutcome.THIEF_WIN:
        cop_points, thief_points = scoring["cop_loss"], scoring["thief_win"]
    else:
        cop_points, thief_points = 0, 0
    return SubGameResult(
        outcome=outcome,
        move_count=move_count,
        cop_points=cop_points,
        thief_points=thief_points,
    )
