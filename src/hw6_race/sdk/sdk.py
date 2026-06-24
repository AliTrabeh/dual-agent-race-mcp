"""Single public entry point for all hw6_race business logic (SG-C03).

CLI/GUI/tests must only ever call methods on Hw6RaceSDK, never reach into
`services/` directly. Bridges the synchronous public API to the async
MCP/orchestration layer (sdk/orchestrator.py, sdk/wiring.py) via asyncio.run().
"""

import asyncio

from hw6_race.constants import DEFAULT_RATE_LIMITS_PATH
from hw6_race.sdk import orchestrator, wiring
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.race.models import GameResult
from hw6_race.shared.config import GameConfig, load_config
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


class Hw6RaceSDK:
    """Facade over the race engine, MCP layer, agents, and reporting.

    Input: a GameConfig and an optional LLMClient (Setup data — defaults to a
    safe, no-network stub if omitted, never a real API call). Output: a
    GameResult from run_local_match(). Single Responsibility: orchestration
    only — no rule logic, transport logic, or reporting logic is duplicated
    here; all of it is delegated to services/ and sdk/orchestrator.py.
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
            self._llm_client = wiring.build_default_llm_client(gatekeeper)

    @property
    def config(self) -> GameConfig:
        return self._config

    def run_local_match(self) -> GameResult:
        """Run a full local 6-sub-game match and return the aggregated GameResult."""
        return asyncio.run(self._run_local_match_async())

    async def _run_local_match_async(self) -> GameResult:
        cop_agent, thief_agent = wiring.build_agents(self._llm_client)
        auth_manager = wiring.build_auth_manager()
        cop_client, thief_client = wiring.build_clients(auth_manager)
        return await orchestrator.play_game_async(
            self._config, thief_agent, cop_agent, thief_client, cop_client
        )
