"""Token-based MCP auth with revoke (HW-F17). Independent of FastMCP for testability.

Input: tokens registered via `register()` (Setup data: token string, role, optional
expiry). Output: `verify()` raises AuthError or returns silently. No I/O performed.
"""

import time
from collections.abc import Callable


class AuthError(Exception):
    """Raised when a token is missing, unknown, revoked, expired, or wrong-role."""


class TokenAuthManager:
    """Issues, verifies, and revokes MCP auth tokens for one or more agent roles.

    Single Responsibility: this class only decides whether a token is currently
    valid for a given role — it never touches message content or transport.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._tokens: dict[str, tuple[str, float | None]] = {}
        self._revoked: set[str] = set()

    def register(self, token: str, role: str, expires_at: float | None = None) -> None:
        """Register a token as valid for `role`, optionally until `expires_at`."""
        self._tokens[token] = (role, expires_at)
        self._revoked.discard(token)

    def revoke(self, token: str) -> None:
        """Immediately invalidate a previously registered token."""
        self._revoked.add(token)

    def verify(self, token: str, expected_role: str) -> None:
        """Raise AuthError unless `token` is currently valid for `expected_role`."""
        if not token or token not in self._tokens:
            raise AuthError("Invalid or unknown token")
        if token in self._revoked:
            raise AuthError("Token has been revoked")
        role, expires_at = self._tokens[token]
        if expires_at is not None and self._clock() >= expires_at:
            raise AuthError("Token has expired")
        if role != expected_role:
            raise AuthError(f"Token is not authorized for role '{expected_role}'")
