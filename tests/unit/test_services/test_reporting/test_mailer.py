import json
import sys
from unittest.mock import MagicMock

import pytest

from hw6_race.services.reporting.mailer import (
    MailerError,
    ReportMailer,
    build_gmail_send_fn,
    build_mailer_from_env,
)
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


@pytest.fixture
def gatekeeper(tmp_rate_limits_file, fake_clock) -> ApiGatekeeper:
    config = RateLimitConfig.from_file(tmp_rate_limits_file)
    return ApiGatekeeper(config, service="default", clock=fake_clock)


def test_send_report_sends_the_report_as_json_only_body(gatekeeper: ApiGatekeeper) -> None:
    sent = {}

    def send_fn(to: str, subject: str, body: str) -> None:
        sent["to"], sent["subject"], sent["body"] = to, subject, body

    mailer = ReportMailer(gatekeeper, send_fn, recipient="rmisegal+uoh26b@gmail.com")
    report = {"group_name": "Team-Alpha", "totals": {"cop": 90, "thief": 40}}

    mailer.send_report(report)

    assert sent["to"] == "rmisegal+uoh26b@gmail.com"
    assert json.loads(sent["body"]) == report


def test_send_report_body_contains_only_json_no_free_text(gatekeeper: ApiGatekeeper) -> None:
    captured_body = {}

    def send_fn(to: str, subject: str, body: str) -> None:
        captured_body["value"] = body

    mailer = ReportMailer(gatekeeper, send_fn, recipient="rmisegal+uoh26b@gmail.com")
    mailer.send_report({"a": 1})

    body = captured_body["value"]
    assert json.loads(body) == {"a": 1}
    assert body == json.dumps({"a": 1})


def test_send_report_wraps_send_fn_failures_in_mailer_error(gatekeeper: ApiGatekeeper) -> None:
    def failing_send_fn(to: str, subject: str, body: str) -> None:
        raise ConnectionError("smtp unavailable")

    mailer = ReportMailer(gatekeeper, failing_send_fn, recipient="rmisegal+uoh26b@gmail.com")

    with pytest.raises(MailerError, match="Failed to send report email"):
        mailer.send_report({"a": 1})


def test_send_report_surfaces_rate_limit_as_mailer_error(gatekeeper: ApiGatekeeper) -> None:
    mailer = ReportMailer(gatekeeper, lambda to, subject, body: None, recipient="x@example.com")
    for _ in range(30):
        mailer.send_report({"a": 1})

    with pytest.raises(MailerError):
        mailer.send_report({"a": 1})


def test_build_mailer_from_env_returns_none_without_credentials(
    gatekeeper: ApiGatekeeper, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GMAIL_OAUTH_CLIENT_SECRET_PATH", raising=False)
    monkeypatch.delenv("GMAIL_OAUTH_TOKEN_PATH", raising=False)
    assert build_mailer_from_env(gatekeeper) is None


def test_build_mailer_from_env_returns_mailer_when_both_paths_set(
    gatekeeper: ApiGatekeeper, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    secret = tmp_path / "secret.json"
    token = tmp_path / "token.json"
    secret.write_text("{}")
    token.write_text("{}")
    monkeypatch.setenv("GMAIL_OAUTH_CLIENT_SECRET_PATH", str(secret))
    monkeypatch.setenv("GMAIL_OAUTH_TOKEN_PATH", str(token))
    mailer = build_mailer_from_env(gatekeeper)
    assert isinstance(mailer, ReportMailer)


def test_build_mailer_from_env_returns_none_when_only_one_path_set(
    gatekeeper: ApiGatekeeper, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    secret = tmp_path / "secret.json"
    secret.write_text("{}")
    monkeypatch.setenv("GMAIL_OAUTH_CLIENT_SECRET_PATH", str(secret))
    monkeypatch.delenv("GMAIL_OAUTH_TOKEN_PATH", raising=False)
    assert build_mailer_from_env(gatekeeper) is None


def test_build_gmail_send_fn_raises_mailer_error_when_google_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.oauth2", None)
    monkeypatch.setitem(sys.modules, "google.oauth2.credentials", None)
    send_fn = build_gmail_send_fn("secret.json", "token.json")
    with pytest.raises(MailerError, match="Gmail deps not installed"):
        send_fn("to@example.com", "Subject", "body")


def test_build_gmail_send_fn_calls_gmail_api(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_creds = MagicMock()
    fake_creds_mod = MagicMock()
    fake_creds_mod.Credentials.from_authorized_user_file.return_value = fake_creds
    fake_service = MagicMock()
    fake_discovery_mod = MagicMock()
    fake_discovery_mod.build.return_value = fake_service

    monkeypatch.setitem(sys.modules, "google", MagicMock())
    monkeypatch.setitem(sys.modules, "google.oauth2", MagicMock())
    monkeypatch.setitem(sys.modules, "google.oauth2.credentials", fake_creds_mod)
    monkeypatch.setitem(sys.modules, "googleapiclient", MagicMock())
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", fake_discovery_mod)

    send_fn = build_gmail_send_fn("secret.json", "token.json")
    send_fn("grader@example.com", "HW6 Match Report", '{"a":1}')

    fake_creds_mod.Credentials.from_authorized_user_file.assert_called_once_with("token.json")
    fake_discovery_mod.build.assert_called_once_with("gmail", "v1", credentials=fake_creds)
    fake_service.users().messages().send.assert_called_once()
