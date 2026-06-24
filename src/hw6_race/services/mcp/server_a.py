"""Cop MCP server — a thin instantiation of the shared scaffold (HW-F13/F14).

No Cop-specific logic lives here on purpose: at this transport layer, Cop and
Thief are symmetric. Role-specific decision-making belongs to Chunk 4's
services/agents/cop_agent.py, not to the MCP transport layer.
"""

from fastmcp import FastMCP

from hw6_race.constants import AgentRole
from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.server_base import build_agent_server


def create_cop_server(auth_manager: TokenAuthManager) -> FastMCP:
    """Build the Cop agent's MCP server."""
    return build_agent_server(AgentRole.COP, auth_manager)
