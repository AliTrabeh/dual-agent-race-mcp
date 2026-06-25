"""Single public entry point for all hw6_race business logic (SG-C03).

CLI/GUI/tests must only ever call methods on Hw6RaceSDK, never reach into
`services/` directly. Bridges the synchronous public API to the async
MCP/orchestration layer (sdk/orchestrator.py, sdk/wiring.py) via asyncio.run().
"""

import asyncio
import logging
import os

from hw6_race.constants import DEFAULT_RATE_LIMITS_PATH
from hw6_race.sdk import orchestrator, wiring
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.race.models import GameResult
from hw6_race.shared.config import GameConfig, load_config
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

logger = logging.getLogger(__name__)


class Hw6RaceSDK:
    """Facade over the race engine, MCP layer, agents, and reporting.

    Input: a GameConfig and an optional LLMClient (Setup data — defaults to a
    real provider client if `LLM_PROVIDER`/`LLM_API_KEY` are set in the
    environment, else a safe no-network stub; never an unauthorized API
    call). Output: a GameResult from run_local_match(). Single
    Responsibility: orchestration only — no rule logic, transport logic, or
    reporting logic is duplicated here; all of it is delegated to services/
    and sdk/orchestrator.py.
    """

    def __init__(
        self,
        config: GameConfig | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self._config = config or load_config()
        if llm_client is not None:
            self._llm_client = llm_client
        else:
            rate_limits = RateLimitConfig.from_file(DEFAULT_RATE_LIMITS_PATH)
            gatekeeper = ApiGatekeeper(rate_limits, service="llm")
            self._llm_client = wiring.build_llm_client_from_env(gatekeeper)

    @property
    def config(self) -> GameConfig:
        return self._config

    def run_local_match(self) -> GameResult:
        """Run a full 6-sub-game match against in-process MCP servers
        (Deployment Stage 1) and return the aggregated GameResult. Always
        local, regardless of `MCP_COP_URL`/`MCP_THIEF_URL` — use
        `run_match()` for the env-driven Stage 1/Stage 2 behavior.
        """
        return asyncio.run(self._run_match_async(wiring.build_clients))

    def run_match(self) -> GameResult:
        """Run a full 6-sub-game match, against real deployed MCP servers if
        `MCP_COP_URL`/`MCP_THIEF_URL` are set (Deployment Stage 2), otherwise
        against in-process servers (Stage 1) — a pure config change, never a
        code change (mirrors how the LLM backend is selected).
        """
        return asyncio.run(self._run_match_async(wiring.build_clients_from_env))

    def send_match_report(self, result: GameResult) -> None:
        """Email the Internal Game JSON report if Gmail OAuth credentials are configured.

        A no-op (with a log message) when credentials are absent — never raises.
        Group metadata is read from GROUP_NAME / STUDENTS / GITHUB_REPO / TIMEZONE env vars.
        """
        from hw6_race.services.reporting.mailer import MailerError, build_mailer_from_env
        from hw6_race.services.reporting.schemas import InternalGameReport

        rate_limits = RateLimitConfig.from_file(DEFAULT_RATE_LIMITS_PATH)
        gatekeeper = ApiGatekeeper(rate_limits, service="email")
        mailer = build_mailer_from_env(gatekeeper)
        if mailer is None:
            return
        students_raw = os.environ.get("STUDENTS", "Ali Trabeh")
        report = InternalGameReport.from_game_result(
            group_name=os.environ.get("GROUP_NAME", "hw6-group"),
            students=[s.strip() for s in students_raw.split(",")],
            github_repo=os.environ.get("GITHUB_REPO", "github.com/AliTrabeh/dual-agent-race-mcp"),
            cop_mcp_url=os.environ.get("MCP_COP_URL", "local"),
            thief_mcp_url=os.environ.get("MCP_THIEF_URL", "local"),
            timezone=os.environ.get("TIMEZONE", "UTC"),
            result=result,
        )
        try:
            mailer.send_report(report.to_json())
            logger.info("Match report emailed successfully")
        except MailerError:
            logger.exception("Failed to email match report — check Gmail OAuth credentials")

    async def _run_match_async(self, build_clients) -> GameResult:
        cop_agent, thief_agent = wiring.build_agents(self._config, self._llm_client)
        auth_manager = wiring.build_auth_manager()
        cop_client, thief_client = build_clients(auth_manager)
        return await orchestrator.play_game_async(
            self._config, thief_agent, cop_agent, thief_client, cop_client
        )
