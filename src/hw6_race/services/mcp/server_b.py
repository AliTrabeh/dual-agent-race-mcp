"""Thief MCP server — a thin instantiation of the shared scaffold (HW-F13/F14).

No Thief-specific logic lives here on purpose: at this transport layer, Cop and
Thief are symmetric. Role-specific decision-making belongs to Chunk 4's
services/agents/thief_agent.py, not to the MCP transport layer.
"""

from fastmcp import FastMCP

from hw6_race.constants import AgentRole
from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.server_base import build_agent_server


def create_thief_server(auth_manager: TokenAuthManager) -> FastMCP:
    """Build the Thief agent's MCP server."""
    return build_agent_server(AgentRole.THIEF, auth_manager)
