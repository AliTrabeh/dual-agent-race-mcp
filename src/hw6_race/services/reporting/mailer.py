"""Gmail OAuth dispatch through the ApiGatekeeper (HW-F21/F22, SG-C09).

The email body is ALWAYS exactly `json.dumps(report)` — no free text — and
this is the only module in the codebase allowed to construct an outbound
email, so that rule has exactly one place to audit (HW-F22).
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from hw6_race.shared.gatekeeper import ApiGatekeeper

logger = logging.getLogger(__name__)

SendFn = Callable[[str, str, str], None]


class MailerError(Exception):
    """Raised when sending the report email fails after the Gatekeeper's policy."""


class ReportMailer:
    """Setup: an ApiGatekeeper, a `send_fn(to, subject, body)` callable (e.g. a
    Gmail API client call, OAuth-authenticated — never a stored password, see
    SG-C09), and the fixed recipient address. Input: a report dict. Output:
    None on success, MailerError on failure.
    """

    def __init__(self, gatekeeper: ApiGatekeeper, send_fn: SendFn, recipient: str) -> None:
        self._gatekeeper = gatekeeper
        self._send_fn = send_fn
        self._recipient = recipient

    def send_report(self, report: dict[str, Any], subject: str = "HW6 Match Report") -> None:
        """Send `report` as the entire email body — JSON only, no free text (HW-F22)."""
        body = json.dumps(report)
        try:
            self._gatekeeper.execute(self._send_fn, self._recipient, subject, body)
        except Exception as exc:
            logger.exception("Failed to send report email")
            raise MailerError(f"Failed to send report email: {exc}") from exc
