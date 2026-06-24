"""Central API Gatekeeper (SG-C05/C06/C07): all outbound external calls route through here."""

import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hw6_race.constants import DEFAULT_RATE_LIMIT_SERVICE, DEFAULT_RATE_LIMITS_PATH


@dataclass(frozen=True)
class ServiceLimits:
    """Rate-limit settings for one named external service (Setup data)."""

    requests_per_minute: int
    requests_per_hour: int
    concurrent_max: int
    retry_after_seconds: int
    max_retries: int


@dataclass(frozen=True)
class QueueStatus:
    """Current queue depth and configured limits for a service (Output data)."""

    service: str
    depth: int
    requests_per_minute: int


class RateLimitConfig:
    """Loaded view of `config/rate_limits.json` (Input data: a JSON file path)."""

    def __init__(self, services: dict[str, ServiceLimits]) -> None:
        self._services = services

    def for_service(self, service: str) -> ServiceLimits:
        return self._services.get(service, self._services[DEFAULT_RATE_LIMIT_SERVICE])

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_RATE_LIMITS_PATH) -> "RateLimitConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        services = {
            name: ServiceLimits(**limits) for name, limits in data["services"].items()
        }
        return cls(services)


class RateLimitExceededError(Exception):
    """Raised when a call would exceed the configured rate limit and cannot be queued."""


class ApiGatekeeper:
    """Centralized manager for all external API calls.

    Input: a RateLimitConfig and a service name. Output: the wrapped call's result,
    or a queued/retried outcome. Setup: an optional injectable clock for deterministic tests.
    Enforces Single Responsibility: this class only gatekeeps calls, it never interprets them.
    """

    def __init__(
        self,
        config: RateLimitConfig,
        service: str = DEFAULT_RATE_LIMIT_SERVICE,
        clock: Callable[[], float] = time.monotonic,
        max_queue_depth: int = 50,
    ) -> None:
        self._limits = config.for_service(service)
        self._service = service
        self._clock = clock
        self._max_queue_depth = max_queue_depth
        self._call_timestamps: deque[float] = deque()
        self._queue: deque[Any] = deque()

    def _prune_old_timestamps(self) -> None:
        cutoff = self._clock() - 60.0
        while self._call_timestamps and self._call_timestamps[0] < cutoff:
            self._call_timestamps.popleft()

    def _within_rate_limit(self) -> bool:
        self._prune_old_timestamps()
        return len(self._call_timestamps) < self._limits.requests_per_minute

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute `api_call(*args, **kwargs)` if under the rate limit, else queue it.

        Raises RateLimitExceededError if the FIFO queue is already at max depth (backpressure).
        """
        if not self._within_rate_limit():
            if len(self._queue) >= self._max_queue_depth:
                raise RateLimitExceededError(
                    f"Service '{self._service}' queue is full (depth={len(self._queue)})"
                )
            self._queue.append((api_call, args, kwargs))
            raise RateLimitExceededError(
                f"Service '{self._service}' rate limit reached; call queued "
                f"(retry after {self._limits.retry_after_seconds}s)"
            )

        self._call_timestamps.append(self._clock())
        return api_call(*args, **kwargs)

    def get_queue_status(self) -> QueueStatus:
        """Return queue depth and stats for observability."""
        return QueueStatus(
            service=self._service,
            depth=len(self._queue),
            requests_per_minute=self._limits.requests_per_minute,
        )
