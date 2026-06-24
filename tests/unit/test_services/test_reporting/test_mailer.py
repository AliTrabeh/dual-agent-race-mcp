import json

import pytest

from hw6_race.services.reporting.mailer import MailerError, ReportMailer
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
