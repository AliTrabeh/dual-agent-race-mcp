"""Inter-group bonus round runner (HW §12.1 / F27-F28)."""

import asyncio
import logging
import os
from typing import Any

from hw6_race.constants import DEFAULT_RATE_LIMITS_PATH
from hw6_race.sdk import wiring
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.race.models import GameResult
from hw6_race.services.reporting.bonus_report import InterGroupBonusReport
from hw6_race.shared.config import GameConfig
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

logger = logging.getLogger(__name__)


def build_bonus_sub_games(
    cop_half: GameResult, thief_half: GameResult
) -> tuple[list[dict[str, Any]], int, int]:
    """Combine two 3-game halves into sub_games list + (our_total, their_total).

    cop_half: we played Cop — cop_points are ours, thief_points are theirs.
    thief_half: we played Thief — thief_points are ours, cop_points are theirs.
    """
    sub_games: list[dict[str, Any]] = []
    our_total = their_total = 0
    for i, sg in enumerate(cop_half.sub_games):
        sub_games.append({
            "index": i + 1, "role_group_1": "cop", "outcome": sg.outcome.value,
            "move_count": sg.move_count, "cop_points": sg.cop_points,
            "thief_points": sg.thief_points,
        })
        our_total += sg.cop_points
        their_total += sg.thief_points
    for i, sg in enumerate(thief_half.sub_games):
        sub_games.append({
            "index": i + 4, "role_group_1": "thief", "outcome": sg.outcome.value,
            "move_count": sg.move_count, "cop_points": sg.cop_points,
            "thief_points": sg.thief_points,
        })
        their_total += sg.cop_points
        our_total += sg.thief_points
    return sub_games, our_total, their_total


def run_bonus_match(config: GameConfig, llm_client: LLMClient) -> None:
    """Run the 6-sub-game inter-group bonus round (§12.1) and email the result."""
    from hw6_race.sdk.sync_play import play_cop_only_game_async, play_thief_only_game_async
    from hw6_race.services.reporting.mailer import MailerError, build_mailer_from_env

    other_cop_url = os.environ.get("BONUS_OTHER_MCP_COP_URL", "").strip()
    other_thief_url = os.environ.get("BONUS_OTHER_MCP_THIEF_URL", "").strip()
    if not (other_cop_url and other_thief_url):
        logger.error(
            "Bonus round requires BONUS_OTHER_MCP_COP_URL and BONUS_OTHER_MCP_THIEF_URL in .env"
        )
        return

    our_cop_url = os.environ.get("MCP_COP_URL", "local")
    our_cop_token = os.environ.get("MCP_COP_AUTH_TOKEN", wiring.LOCAL_COP_TOKEN)
    our_thief_url = os.environ.get("MCP_THIEF_URL", "local")
    our_thief_token = os.environ.get("MCP_THIEF_AUTH_TOKEN", wiring.LOCAL_THIEF_TOKEN)
    other_cop_token = os.environ.get("BONUS_OTHER_MCP_COP_TOKEN", "").strip()
    other_thief_token = os.environ.get("BONUS_OTHER_MCP_THIEF_TOKEN", "").strip()
    three_game_config = GameConfig({**config.raw, "num_games": 3})
    cop_agent, thief_agent = wiring.build_agents(three_game_config, llm_client)

    logger.info("Bonus — 3 games as Cop (our Cop MCP + their Thief MCP)")
    our_cop_client, their_thief_client = wiring.build_explicit_remote_clients(
        our_cop_url, our_cop_token, other_thief_url, other_thief_token
    )
    cop_half = asyncio.run(
        play_cop_only_game_async(three_game_config, cop_agent, our_cop_client, their_thief_client)
    )

    logger.info("Bonus — 3 games as Thief (their Cop MCP + our Thief MCP)")
    their_cop_client, our_thief_client = wiring.build_explicit_remote_clients(
        other_cop_url, other_cop_token, our_thief_url, our_thief_token
    )
    thief_half = asyncio.run(
        play_thief_only_game_async(three_game_config, thief_agent, our_thief_client, their_cop_client)
    )

    sub_games, our_total, their_total = build_bonus_sub_games(cop_half, thief_half)
    our_group = os.environ.get("GROUP_NAME", "hw6-group")
    other_group = os.environ.get("BONUS_OTHER_GROUP_NAME", "other-group")
    report = InterGroupBonusReport(
        group_1_name=our_group, group_2_name=other_group,
        github_repo_group_1=os.environ.get("GITHUB_REPO", ""),
        github_repo_group_2=os.environ.get("BONUS_OTHER_GITHUB_REPO", ""),
        mcp_url_group_1_cop=our_cop_url, mcp_url_group_1_thief=our_thief_url,
        mcp_url_group_2_cop=other_cop_url, mcp_url_group_2_thief=other_thief_url,
        timezone=os.environ.get("TIMEZONE", "UTC"),
        students_group_1=[s.strip() for s in os.environ.get("STUDENTS", "Ali Trabeh").split(",")],
        students_group_2=[s.strip() for s in os.environ.get("BONUS_OTHER_STUDENTS", "").split(",") if s.strip()],
        sub_games=sub_games,
        totals_by_group={our_group: our_total, other_group: their_total},
        mutual_agreement=True,
    )

    rate_limits = RateLimitConfig.from_file(DEFAULT_RATE_LIMITS_PATH)
    gatekeeper = ApiGatekeeper(rate_limits, service="email")
    mailer = build_mailer_from_env(gatekeeper)
    if mailer is None:
        logger.warning("Gmail not configured — bonus report not emailed")
        return
    try:
        mailer.send_report(report.to_json(), subject="HW6 Bonus Match Report")
        logger.info("Bonus match report emailed")
    except MailerError:
        logger.exception("Failed to email bonus match report")
