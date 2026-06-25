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
    """Build a FastMCP server exposing tools for one agent role.

    Includes the original 3 token-auth tools plus 6 bonus-round tools
    (no token required — auth is handled at HTTP bearer level for remote calls).
    """
    store = message_store or MessageStore()
    app = FastMCP(name=f"hw6-race-{role.value}-server")
    _pos: list[int] = [0, 0]   # our agent's tracked position (for report_location)
    _turn: list[int] = [0]     # sub-game turn counter

    def _require_token(token: str) -> None:
        try:
            auth_manager.verify(token, role.value)
        except AuthError as exc:
            logger.warning("Auth rejected for %s server: %s", role.value, exc)
            raise ToolError(str(exc)) from exc

    @app.tool
    def send_message(token: str, text: str) -> str:
        """Record an outgoing message from this agent (audit log + read_message queue)."""
        _require_token(token)
        store.send(text)
        logger.debug("[%s] send_message: %s", role.value, text)
        return "recorded"

    @app.tool
    def receive_message(text: str, token: str = "", from_agent: str = "") -> dict:
        """Deliver an incoming NL message into this agent's inbox.

        Accepts two conventions:
        - Internal (own group): receive_message(token=our_token, text=msg)
        - External (bonus, HTTP bearer): receive_message(from_agent=name, text=msg)
        """
        if token:
            _require_token(token)
        store.receive(text)
        logger.debug("[%s] receive_message: %s", role.value, text)
        return {"ok": True, "turn": _turn[0]}

    @app.tool
    def get_inbox(token: str) -> list[str]:
        """Return and clear all pending inbox messages for this agent."""
        _require_token(token)
        messages = store.drain_inbox()
        logger.debug("[%s] get_inbox: %d message(s)", role.value, len(messages))
        return messages

    # --- Bonus-round tools (HW §12.1 inter-group protocol) ---

    @app.tool
    def start_subgame(position: list) -> dict:
        """Initialise a sub-game; `position` is our agent's starting cell."""
        _pos[:] = [int(position[0]), int(position[1])]
        _turn[0] = 0
        return {"ok": True}

    @app.tool
    def report_location() -> dict:
        """Return our agent's current cell (kept current by _set_position)."""
        return {"agent": role.value, "position": list(_pos)}

    @app.tool
    def choose_action(action: dict) -> dict:
        """Opponent notifies us of their action; acknowledged without inbox side-effect."""
        return {"accepted": True, "moves_remaining": max(0, 50 - _turn[0])}

    @app.tool
    def sync_barriers(barriers: list) -> dict:
        """Opponent syncs barrier placements; we track the count for reference."""
        return {"ok": True, "barrier_count": len(barriers)}

    @app.tool
    def read_message() -> dict | None:
        """Return and dequeue the oldest outgoing NL message from this agent."""
        text = store.drain_outbox_one()
        return {"from_agent": role.value, "text": text, "turn": _turn[0]} if text else None

    @app.tool
    def _set_position(token: str, row: int, col: int) -> None:
        """Internal: update our tracked position after each move (requires auth token)."""
        _require_token(token)
        _pos[:] = [row, col]
        _turn[0] += 1

    return app
