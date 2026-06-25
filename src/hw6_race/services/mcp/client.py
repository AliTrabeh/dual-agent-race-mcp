"""Thin async MCP client wrapper used by the orchestrator (Chunk 6) to call tools.

Input: a FastMCP server instance or URL, plus a bearer token (Setup data).
Output: tool-call results, returned exactly as received — no transformation,
preserving HW-F13's "no rigid protocol, pass-through only" property.
"""

from types import TracebackType

from fastmcp import Client, FastMCP


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

    async def receive_message(self, text: str) -> str:
        """Deliver `text` into this agent's inbox via its receive_message tool."""
        result = await self._client.call_tool(
            "receive_message", {"token": self._token, "text": text}
        )
        return result.data

    async def get_inbox(self) -> list[str]:
        """Fetch and clear this agent's pending inbox."""
        result = await self._client.call_tool("get_inbox", {"token": self._token})
        return result.data
