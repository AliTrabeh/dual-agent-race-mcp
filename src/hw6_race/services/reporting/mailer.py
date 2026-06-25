"""Gmail OAuth dispatch through the ApiGatekeeper (HW-F21/F22, SG-C09).

The email body is ALWAYS exactly `json.dumps(report)` — no free text — and
this is the only module in the codebase allowed to construct an outbound
email, so that rule has exactly one place to audit (HW-F22).
"""

import json
import logging
import os
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


def build_gmail_send_fn(client_secret_path: str, token_path: str) -> SendFn:
    """Build a Gmail API send_fn backed by OAuth credentials (SG-C09: OAuth only, never a password)."""
    def _send(to: str, subject: str, body: str) -> None:
        try:
            import base64
            import email as _email

            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build as _build_svc
        except ImportError as exc:
            raise MailerError(
                "Gmail deps not installed; run: uv add google-auth-oauthlib google-api-python-client"
            ) from exc
        creds = Credentials.from_authorized_user_file(token_path)
        service = _build_svc("gmail", "v1", credentials=creds)
        msg = _email.message.EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return _send


def build_mailer_from_env(gatekeeper: ApiGatekeeper) -> "ReportMailer | None":
    """Return a ReportMailer wired to Gmail if OAuth credentials are in the environment; else None."""
    secret = os.environ.get("GMAIL_OAUTH_CLIENT_SECRET_PATH", "").strip()
    token = os.environ.get("GMAIL_OAUTH_TOKEN_PATH", "").strip()
    recipient = os.environ.get("REPORT_RECIPIENT_EMAIL", "rmisegal+uoh26b@gmail.com")
    if not (secret and token):
        logger.info("Gmail credentials not configured; report email will not be sent")
        return None
    return ReportMailer(gatekeeper, build_gmail_send_fn(secret, token), recipient)
