from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.reporting.technical_loss import is_technical_loss, resolve_technical_losses

_COP_WIN = SubGameResult(outcome=GameOutcome.COP_WIN, move_count=10, cop_points=20, thief_points=5)
_TECH_LOSS = SubGameResult(outcome=GameOutcome.TECHNICAL_LOSS, move_count=0, cop_points=0, thief_points=0)
_THIEF_WIN = SubGameResult(outcome=GameOutcome.THIEF_WIN, move_count=25, cop_points=5, thief_points=10)


def test_is_technical_loss_true_for_technical_loss_outcome() -> None:
    assert is_technical_loss(_TECH_LOSS) is True


def test_is_technical_loss_false_for_completed_outcomes() -> None:
    assert is_technical_loss(_COP_WIN) is False
    assert is_technical_loss(_THIEF_WIN) is False


async def test_resolve_technical_losses_leaves_completed_sub_games_untouched() -> None:
    result = GameResult(sub_games=[_COP_WIN, _THIEF_WIN])

    async def rerun_one() -> SubGameResult:
        raise AssertionError("rerun_one should never be called when there is nothing to resolve")

    resolved = await resolve_technical_losses(result, rerun_one)
    assert resolved.sub_games == [_COP_WIN, _THIEF_WIN]


async def test_resolve_technical_losses_replaces_a_failed_sub_game_with_a_successful_rerun() -> None:
    result = GameResult(sub_games=[_COP_WIN, _TECH_LOSS])

    async def rerun_one() -> SubGameResult:
        return _THIEF_WIN

    resolved = await resolve_technical_losses(result, rerun_one)
    assert resolved.sub_games == [_COP_WIN, _THIEF_WIN]


async def test_resolve_technical_losses_stops_after_max_attempts() -> None:
    result = GameResult(sub_games=[_TECH_LOSS])
    call_count = 0

    async def always_fails() -> SubGameResult:
        nonlocal call_count
        call_count += 1
        return _TECH_LOSS

    resolved = await resolve_technical_losses(result, always_fails, max_attempts=2)

    assert call_count == 2
    assert resolved.sub_games == [_TECH_LOSS]
