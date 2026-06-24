"""In-memory message mailbox backing one agent's MCP server tools (HW-F13).

Input: NL text strings via send()/receive(). Output: the same text, unmodified,
via drain_inbox() — this store never interprets or transforms message content,
preserving the "free natural language, no rigid protocol" property (HW-N01).
"""

from dataclasses import dataclass, field


@dataclass
class MessageStore:
    """Holds one agent server's outbox audit log and pending inbox.

    Setup: none — starts empty. Single Responsibility: storage and ordering
    only, never auth or transport (those live in auth.py / server_base.py).
    """

    _inbox: list[str] = field(default_factory=list)
    _outbox_log: list[str] = field(default_factory=list)

    def send(self, text: str) -> None:
        """Record an outgoing message for audit/logging purposes."""
        self._outbox_log.append(text)

    def receive(self, text: str) -> None:
        """Deliver an incoming message into this server's inbox, unmodified."""
        self._inbox.append(text)

    def drain_inbox(self) -> list[str]:
        """Return all pending inbox messages in order, then clear the inbox."""
        messages, self._inbox = self._inbox, []
        return messages

    def outbox_log(self) -> list[str]:
        """Return a copy of every message ever sent, for audit purposes."""
        return list(self._outbox_log)
