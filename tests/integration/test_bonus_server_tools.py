"""Integration tests for bonus-round tools added to server_base (HW §12.1)."""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from hw6_race.constants import AgentRole
from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.client import AgentMCPClient, BonusOpponentClient
from hw6_race.services.mcp.server_base import build_agent_server

COP_TOKEN = "cop-tok-bonus"


@pytest.fixture
def auth() -> TokenAuthManager:
    mgr = TokenAuthManager()
    mgr.register(COP_TOKEN, "cop")
    return mgr


@pytest.fixture
def cop_server(auth):
    return build_agent_server(AgentRole.COP, auth)


async def test_start_subgame_sets_position_and_resets_turn(cop_server) -> None:
    async with Client(cop_server) as c:
        await c.call_tool("start_subgame", {"position": [2, 3]})
        result = await c.call_tool("report_location", {})
    assert result.data["position"] == [2, 3]
    assert result.data["agent"] == "cop"


async def test_report_location_defaults_to_origin(cop_server) -> None:
    async with Client(cop_server) as c:
        result = await c.call_tool("report_location", {})
    assert result.data["position"] == [0, 0]


async def test_choose_action_acknowledges_with_accepted_true(cop_server) -> None:
    async with Client(cop_server) as c:
        result = await c.call_tool("choose_action", {"action": {"type": "move", "direction": "up"}})
    assert result.data["accepted"] is True


async def test_choose_action_does_not_pollute_inbox(cop_server, auth) -> None:
    async with Client(cop_server) as c:
        await c.call_tool("choose_action", {"action": {"type": "move"}})
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        inbox = await client.get_inbox()
    assert inbox == []


async def test_sync_barriers_returns_barrier_count(cop_server) -> None:
    async with Client(cop_server) as c:
        result = await c.call_tool("sync_barriers", {"barriers": [[0, 1], [2, 2]]})
    assert result.data["barrier_count"] == 2


async def test_read_message_returns_none_when_outbox_empty(cop_server) -> None:
    async with Client(cop_server) as c:
        result = await c.call_tool("read_message", {})
    assert result.data is None


async def test_read_message_drains_outbox_fifo(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        await client.send_message("first")
        await client.send_message("second")
    async with Client(cop_server) as c:
        r1 = await c.call_tool("read_message", {})
        r2 = await c.call_tool("read_message", {})
        r3 = await c.call_tool("read_message", {})
    assert r1.data["text"] == "first"
    assert r2.data["text"] == "second"
    assert r3.data is None


async def test_set_position_updates_report_location(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        await client.set_bonus_position((3, 4))
    async with Client(cop_server) as c:
        result = await c.call_tool("report_location", {})
    assert result.data["position"] == [3, 4]


async def test_set_position_rejects_invalid_token(cop_server) -> None:
    async with Client(cop_server) as c:
        with pytest.raises(ToolError):
            await c.call_tool("_set_position", {"token": "wrong", "row": 1, "col": 1})


async def test_receive_message_without_token_stores_in_inbox(cop_server, auth) -> None:
    async with Client(cop_server) as c:
        result = await c.call_tool("receive_message", {"from_agent": "thief", "text": "hi"})
    assert result.data["ok"] is True
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        inbox = await client.get_inbox()
    assert inbox == ["hi"]


async def test_bonus_opponent_client_receive_message_uses_from_agent(cop_server) -> None:
    async with BonusOpponentClient(cop_server, COP_TOKEN, AgentRole.THIEF) as opp:
        result = await opp.receive_message("moving right")
    assert result["ok"] is True
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        inbox = await client.get_inbox()
    assert inbox == ["moving right"]


async def test_agent_mcp_client_receive_message_returns_ok_dict(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        result = await client.receive_message("test msg")
    assert result["ok"] is True


async def test_agent_mcp_client_choose_action_returns_accepted(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        result = await client.choose_action({"type": "move", "direction": "down"})
    assert result["accepted"] is True


async def test_agent_mcp_client_init_bonus_subgame_sets_position(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        await client.init_bonus_subgame((1, 2))
    async with Client(cop_server) as c:
        result = await c.call_tool("report_location", {})
    assert result.data["position"] == [1, 2]


async def test_agent_mcp_client_start_subgame_sets_position(cop_server) -> None:
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        result = await client.start_subgame((4, 0))
    assert result["ok"] is True
    async with Client(cop_server) as c:
        r = await c.call_tool("report_location", {})
    assert r.data["position"] == [4, 0]
