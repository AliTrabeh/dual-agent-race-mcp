from pathlib import Path

import pytest

from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig, RateLimitExceededError


@pytest.fixture
def gatekeeper(tmp_rate_limits_file: Path, fake_clock) -> ApiGatekeeper:
    config = RateLimitConfig.from_file(tmp_rate_limits_file)
    return ApiGatekeeper(config, service="default", clock=fake_clock, max_queue_depth=2)


def test_execute_calls_api_when_under_limit(gatekeeper: ApiGatekeeper) -> None:
    result = gatekeeper.execute(lambda x: x * 2, 21)
    assert result == 42


def test_execute_raises_when_rate_limit_reached(gatekeeper: ApiGatekeeper) -> None:
    for _ in range(30):
        gatekeeper.execute(lambda: "ok")
    with pytest.raises(RateLimitExceededError, match="rate limit reached"):
        gatekeeper.execute(lambda: "blocked")


def test_queue_backpressure_raises_when_queue_full(gatekeeper: ApiGatekeeper) -> None:
    for _ in range(30):
        gatekeeper.execute(lambda: "ok")
    for _ in range(2):
        with pytest.raises(RateLimitExceededError, match="rate limit reached"):
            gatekeeper.execute(lambda: "queued")
    with pytest.raises(RateLimitExceededError, match="queue is full"):
        gatekeeper.execute(lambda: "overflow")


def test_rate_limit_resets_after_window_passes(gatekeeper: ApiGatekeeper, fake_clock) -> None:
    for _ in range(30):
        gatekeeper.execute(lambda: "ok")
    fake_clock.advance(61.0)
    result = gatekeeper.execute(lambda: "ok again")
    assert result == "ok again"


def test_get_queue_status_reports_depth_and_limit(gatekeeper: ApiGatekeeper) -> None:
    status = gatekeeper.get_queue_status()
    assert status.service == "default"
    assert status.depth == 0
    assert status.requests_per_minute == 30
