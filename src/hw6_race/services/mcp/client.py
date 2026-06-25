"""Thin async MCP client wrapper used by the orchestrator (Chunk 6) to call tools.

Input: a FastMCP server instance or URL, plus a bearer token (Setup data).
Output: tool-call results, returned exactly as received — no transformation,
preserving HW-F13's "no rigid protocol, pass-through only" property.
"""

from types import TracebackType

from fastmcp import Client, FastMCP

from hw6_race.constants import AgentRole


class AgentMCPClient:
    """Wraps fastmcp.Client, bound to one agent's server and auth token."""

    def __init__(self, server: FastMCP | str, token: str) -> None:
        http_auth = token if isinstance(server, str) else None
        self._client = Client(server, auth=http_auth)
        self._token = token

    async def __aenter__(self) -> "AgentMCPClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc, tb)

    async def send_message(self, text: str) -> str:
        """Call this agent's own send_message tool (audit-log only)."""
        result = await self._client.call_tool(
            "send_message", {"token": self._token, "text": text}
        )
        return result.data

    async def receive_message(self, text: str) -> dict:
        """Deliver `text` into this agent's inbox via its receive_message tool."""
        result = await self._client.call_tool(
            "receive_message", {"token": self._token, "text": text}
        )
        return result.data

    async def get_inbox(self) -> list[str]:
        """Fetch and clear this agent's pending inbox."""
        result = await self._client.call_tool("get_inbox", {"token": self._token})
        return result.data

    async def set_bonus_position(self, pos: tuple[int, int]) -> None:
        """Track our current position on our own server (for opponent's report_location)."""
        await self._client.call_tool(
            "_set_position", {"token": self._token, "row": pos[0], "col": pos[1]}
        )

    async def init_bonus_subgame(self, position: tuple[int, int]) -> None:
        """Initialise the sub-game position tracker on our own server."""
        await self._client.call_tool("start_subgame", {"position": list(position)})

    async def choose_action(self, action: dict) -> dict:
        """Notify the other server of our last action."""
        result = await self._client.call_tool("choose_action", {"action": action})
        return result.data

    async def start_subgame(self, position: tuple[int, int]) -> dict:
        """Tell the other server our starting position for this sub-game."""
        result = await self._client.call_tool("start_subgame", {"position": list(position)})
        return result.data


class BonusOpponentClient(AgentMCPClient):
    """AgentMCPClient adapted for the other group's receive_message convention.

    Their server expects receive_message(from_agent, text) without a token arg;
    all other tool calls are inherited unchanged from AgentMCPClient.
    """

    def __init__(self, server: str, token: str, our_role: AgentRole) -> None:
        super().__init__(server, token)
        self._our_role = our_role

    async def receive_message(self, text: str) -> dict:
        """Send our NL message using from_agent/text rather than token/text."""
        result = await self._client.call_tool(
            "receive_message", {"from_agent": self._our_role.value, "text": text}
        )
        return result.data
