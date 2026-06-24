"""Integration tests for the MCP transport layer — in-process FastMCP, no real sockets.

Validates HW-F13 (independent servers, NL pass-through, no shared state) and
HW-F17 (token auth + revoke) end to end across server_base/server_a/server_b/client.
"""

import pytest
from fastmcp.exceptions import ToolError

from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.client import AgentMCPClient
from hw6_race.services.mcp.server_a import create_cop_server
from hw6_race.services.mcp.server_b import create_thief_server

COP_TOKEN = "cop-secret-token"
THIEF_TOKEN = "thief-secret-token"


@pytest.fixture
def auth_manager() -> TokenAuthManager:
    manager = TokenAuthManager()
    manager.register(COP_TOKEN, "cop")
    manager.register(THIEF_TOKEN, "thief")
    return manager


async def test_message_round_trips_unmodified_between_servers(auth_manager) -> None:
    cop_server = create_cop_server(auth_manager)
    thief_server = create_thief_server(auth_manager)

    async with AgentMCPClient(cop_server, COP_TOKEN) as cop_client:
        await cop_client.send_message("thief is near cell 12")

    async with AgentMCPClient(thief_server, THIEF_TOKEN) as thief_client:
        await thief_client.receive_message("thief is near cell 12")
        inbox = await thief_client.get_inbox()

    assert inbox == ["thief is near cell 12"]


async def test_servers_share_no_in_process_state(auth_manager) -> None:
    cop_server = create_cop_server(auth_manager)
    thief_server = create_thief_server(auth_manager)

    async with AgentMCPClient(cop_server, COP_TOKEN) as cop_client:
        await cop_client.receive_message("only cop should see this")

    async with AgentMCPClient(thief_server, THIEF_TOKEN) as thief_client:
        thief_inbox = await thief_client.get_inbox()

    assert thief_inbox == []


async def test_invalid_token_is_rejected(auth_manager) -> None:
    cop_server = create_cop_server(auth_manager)
    async with AgentMCPClient(cop_server, "not-a-real-token") as client:
        with pytest.raises(ToolError, match="Invalid or unknown token"):
            await client.send_message("hello")


async def test_revoked_token_is_rejected_immediately(auth_manager) -> None:
    auth_manager.revoke(COP_TOKEN)
    cop_server = create_cop_server(auth_manager)
    async with AgentMCPClient(cop_server, COP_TOKEN) as client:
        with pytest.raises(ToolError, match="revoked"):
            await client.send_message("hello")


async def test_wrong_role_token_is_rejected(auth_manager) -> None:
    cop_server = create_cop_server(auth_manager)
    async with AgentMCPClient(cop_server, THIEF_TOKEN) as client:
        with pytest.raises(ToolError, match="not authorized for role 'cop'"):
            await client.send_message("hello")


async def test_get_inbox_drains_messages_so_they_are_not_redelivered(auth_manager) -> None:
    thief_server = create_thief_server(auth_manager)
    async with AgentMCPClient(thief_server, THIEF_TOKEN) as client:
        await client.receive_message("once")
        first = await client.get_inbox()
        second = await client.get_inbox()

    assert first == ["once"]
    assert second == []
