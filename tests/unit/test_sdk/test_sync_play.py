"""Tests for sdk/sync_play.py — synchronized single-role game loops (HW §12.1)."""

import asyncio as _asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from _orchestrator_doubles import FakeAgent, FakeMCPClient

from hw6_race.constants import AgentRole, GameOutcome, MoveDirection
from hw6_race.sdk import sync_play as sp_mod
from hw6_race.sdk.sync_play import (
    _play_one_role_sub_game,
    _update_opponent_position,
    play_cop_only_game_async,
    play_thief_only_game_async,
    wait_for_opponent_message,
)
from hw6_race.services.agents.models import ActionType, AgentAction, Inference
from hw6_race.services.race.models import SubGameResult
from hw6_race.services.race.race_state import RaceState
from hw6_race.shared.config import GameConfig


def _cfg(max_moves: int = 25, num_games: int = 2) -> GameConfig:
    return GameConfig({
        "version": "1.00", "grid_size": [5, 5], "max_moves": max_moves,
        "num_games": num_games, "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    })


_ACT = AgentAction(ActionType.MOVE, MoveDirection.RIGHT)


async def test_wait_returns_last_message_when_inbox_is_non_empty() -> None:
    assert await wait_for_opponent_message(FakeMCPClient(inbox=["hello"]), timeout=30.0) == "hello"


async def test_wait_returns_none_after_one_poll_when_deadline_passes() -> None:
    client = AsyncMock()
    client.get_inbox.return_value = []
    times = iter([0.0, 0.0, 100.0])
    fake_loop = MagicMock()
    fake_loop.time.side_effect = lambda: next(times)
    with (
        patch.object(_asyncio, "get_running_loop", return_value=fake_loop),
        patch.object(_asyncio, "sleep", new=AsyncMock()),
    ):
        result = await wait_for_opponent_message(client, timeout=0.5)
    assert result is None
    assert client.get_inbox.call_count == 1


def _state() -> RaceState:
    return RaceState(grid_size=(5, 5), max_moves=25, max_barriers=5,
                     cop_position=(0, 0), thief_position=(4, 4))


class _Stated:
    def __init__(self, pos: tuple[int, int]) -> None:
        self._pos = pos

    def interpret_message(self, text: str) -> Inference:
        return Inference(believed_position=self._pos, confidence="stated", raw_text=text)


def test_update_sets_thief_position_when_stated() -> None:
    state = _state()
    _update_opponent_position(state, AgentRole.THIEF, _Stated((2, 3)), "msg")
    assert state.thief_position == (2, 3)


def test_update_sets_cop_position_when_stated() -> None:
    state = _state()
    _update_opponent_position(state, AgentRole.COP, _Stated((1, 1)), "msg")
    assert state.cop_position == (1, 1)


def test_update_does_not_change_position_when_ambiguous() -> None:
    state = _state()
    _update_opponent_position(state, AgentRole.THIEF, FakeAgent(_ACT), "?")
    assert state.thief_position == (4, 4)


async def test_play_one_role_returns_cop_win_when_positions_start_equal() -> None:
    result = await _play_one_role_sub_game(
        _cfg(), FakeAgent(_ACT), AgentRole.COP,
        FakeMCPClient(), FakeMCPClient(), (2, 2), (2, 2), 30.0,
    )
    assert result.outcome == GameOutcome.COP_WIN


async def test_play_one_role_cop_technical_loss_on_timeout() -> None:
    result = await _play_one_role_sub_game(
        _cfg(), FakeAgent(_ACT), AgentRole.COP,
        FakeMCPClient(), FakeMCPClient(), (0, 0), (4, 4), -1.0,
    )
    assert result.outcome == GameOutcome.TECHNICAL_LOSS


async def test_play_one_role_thief_calls_take_turn_then_times_out_for_cop() -> None:
    with patch("hw6_race.sdk.sync_play.orchestrator.take_turn", new=AsyncMock()):
        result = await _play_one_role_sub_game(
            _cfg(), FakeAgent(_ACT), AgentRole.THIEF,
            FakeMCPClient(), FakeMCPClient(), (0, 0), (4, 4), -1.0,
        )
    assert result.outcome == GameOutcome.TECHNICAL_LOSS


async def test_play_one_role_processes_opponent_message_and_ends_game() -> None:
    result = await _play_one_role_sub_game(
        _cfg(max_moves=1), FakeAgent(_ACT), AgentRole.COP,
        FakeMCPClient(inbox=["Thief at 2,3"]), FakeMCPClient(), (0, 0), (4, 4), 30.0,
    )
    assert result.outcome == GameOutcome.THIEF_WIN


@pytest.mark.parametrize("runner,outcome", [
    (play_cop_only_game_async, GameOutcome.COP_WIN),
    (play_thief_only_game_async, GameOutcome.THIEF_WIN),
])
async def test_single_role_runners_call_sub_game_n_times(monkeypatch, runner, outcome) -> None:
    fake_sg = SubGameResult(outcome=outcome, move_count=5, cop_points=20, thief_points=5)

    async def _fake_sub(*_a, **_kw) -> SubGameResult:
        return fake_sg

    monkeypatch.setattr(sp_mod, "_play_one_role_sub_game", _fake_sub)
    result = await runner(_cfg(num_games=2), FakeAgent(_ACT), FakeMCPClient(), FakeMCPClient())
    assert len(result.sub_games) == 2
    assert all(sg is fake_sg for sg in result.sub_games)
