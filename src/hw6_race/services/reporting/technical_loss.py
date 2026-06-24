"""Technical Loss detection + rerun bookkeeping (HW-F22): a final report must
contain exactly `num_games` completed (non-technical-loss) sub-games, never
fewer — never silently reported with gaps.

Implemented as a standalone, fully tested algorithm operating on an already-
produced GameResult plus a caller-supplied async rerun callable. Wiring this
into a single live match's MCP-client-connection scope is an explicitly
flagged follow-up — see docs/07_risks_and_open_questions.md and
docs/prds/PRD-005-logging-protocol-and-observability.md.
"""

import logging
from collections.abc import Awaitable, Callable

from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import GameResult, SubGameResult

logger = logging.getLogger(__name__)

DEFAULT_MAX_RERUN_ATTEMPTS = 3

RerunFn = Callable[[], Awaitable[SubGameResult]]


def is_technical_loss(sub_game: SubGameResult) -> bool:
    """Return True if `sub_game` did not complete normally (HW-F22)."""
    return sub_game.outcome == GameOutcome.TECHNICAL_LOSS


async def resolve_technical_losses(
    result: GameResult,
    rerun_one: RerunFn,
    max_attempts: int = DEFAULT_MAX_RERUN_ATTEMPTS,
) -> GameResult:
    """Replace each Technical Loss entry with a fresh sub-game, retrying up to
    `max_attempts` times each. A sub-game that keeps failing after exhausting
    its attempts stays recorded as a Technical Loss rather than retrying forever.
    """
    resolved: list[SubGameResult] = []
    for sub_game in result.sub_games:
        current = sub_game
        attempts = 0
        while is_technical_loss(current) and attempts < max_attempts:
            logger.info("Rerunning a Technical Loss sub-game (attempt %d)", attempts + 1)
            current = await rerun_one()
            attempts += 1
        resolved.append(current)
    return GameResult(sub_games=resolved)
