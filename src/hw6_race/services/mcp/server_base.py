"""Shared FastMCP scaffold: the ONE place auth + tool registration is implemented.

Both the Cop and Thief servers are built by calling build_agent_server() with a
different AgentRole — no auth-check or tool-registration logic is duplicated
between them (SG-C04). Game-legality logic is deliberately absent here: this
layer only passes natural-language text through (HW-F13), per PRD-002 scope.
"""

import logging

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from hw6_race.constants import AgentRole
from hw6_race.services.mcp.auth import AuthError, TokenAuthManager
from hw6_race.services.mcp.message_store import MessageStore

logger = logging.getLogger(__name__)


def build_agent_server(
    role: AgentRole,
    auth_manager: TokenAuthManager,
    message_store: MessageStore | None = None,
) -> FastMCP:
    """Build a FastMCP server exposing the 3 message tools for one agent role.

    Input: the agent's role and its TokenAuthManager (Setup data: an optional
    pre-existing MessageStore, mainly for tests). Output: a ready-to-run FastMCP
    app, usable directly by fastmcp.Client for in-process testing (no sockets).
    """
    store = message_store or MessageStore()
    app = FastMCP(name=f"hw6-race-{role.value}-server")

    def _require_token(token: str) -> None:
        try:
            auth_manager.verify(token, role.value)
        except AuthError as exc:
            logger.warning("Auth rejected for %s server: %s", role.value, exc)
            raise ToolError(str(exc)) from exc

    @app.tool
    def send_message(token: str, text: str) -> str:
        """Record an outgoing message from this agent (audit log only)."""
        _require_token(token)
        store.send(text)
        logger.debug("[%s] send_message: %s", role.value, text)
        return "recorded"

    @app.tool
    def receive_message(token: str, text: str) -> str:
        """Deliver an incoming natural-language message into this agent's inbox."""
        _require_token(token)
        store.receive(text)
        logger.debug("[%s] receive_message: %s", role.value, text)
        return "delivered"

    @app.tool
    def get_inbox(token: str) -> list[str]:
        """Return and clear all pending inbox messages for this agent."""
        _require_token(token)
        messages = store.drain_inbox()
        logger.debug("[%s] get_inbox: %d message(s)", role.value, len(messages))
        return messages

    return app
