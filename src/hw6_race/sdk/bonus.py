"""Inter-group bonus round runner (HW §12.1 / F27-F28)."""

import asyncio
import logging
import os
import random
from typing import Any

from fastmcp import Client

from hw6_race.constants import DEFAULT_RATE_LIMITS_PATH
from hw6_race.sdk import wiring
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.reporting.bonus_report import InterGroupBonusReport
from hw6_race.shared.config import GameConfig
from hw6_race.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 2.0
_MAX_WAIT = 300.0
_DIRECTIONS = ["up", "down", "left", "right"]


def _mcp_client(url: str, token: str) -> Client:
    return Client(url, auth=token)


async def _barrier_sync(
    my_role: str,
    my_url: str, my_token: str,
    partner_url: str, partner_token: str,
    half_index: int, sub_game_index: int,
) -> None:
    """Exchange 'ready' signals before sub-game N (N > 1) to ensure both sides
    enter the game loop at the same time. Call BEFORE start_subgame so the
    inbox reset in start_subgame clears the barrier messages automatically."""
    ready_text = f"READY:half:{half_index}:subgame:{sub_game_index}"
    async with _mcp_client(my_url, my_token) as my_c, _mcp_client(partner_url, partner_token) as partner_c:
        # Deliver our ready signal to partner's server (no token arg needed on their server)
        await partner_c.call_tool("receive_message", {"from_agent": my_role, "text": ready_text})
        waited = 0.0
        while waited < 60.0:
            try:
                # read_message on OUR server needs the token arg
                msg = (await asyncio.wait_for(
                    my_c.call_tool("read_message", {"token": my_token}), timeout=10.0
                )).data
            except asyncio.TimeoutError:
                msg = None
            if msg and msg.get("text") == ready_text:
                return
            print(f"  Barrier: waiting for partner ready signal... {int(waited)}s", end="\r", flush=True)
            await asyncio.sleep(2.0)
            waited += 2.0
    raise RuntimeError(f"Barrier timeout: partner not ready for half {half_index} sub-game {sub_game_index}")


async def _wait_for_new_message(c: Client, my_token: str, last_seen: dict | None) -> dict:
    waited = 0.0
    while waited < _MAX_WAIT:
        try:
            msg = (await asyncio.wait_for(
                c.call_tool("read_message", {"token": my_token}), timeout=10.0
            )).data
        except asyncio.TimeoutError:
            msg = None
        if msg and msg != last_seen:
            return msg
        print(f"    Waiting for opponent... {int(waited)}s elapsed", end="\r", flush=True)
        await asyncio.sleep(_POLL_INTERVAL)
        waited += _POLL_INTERVAL
    raise RuntimeError("Timed out waiting for opponent move (>300s)")


async def _get_positions(my_c: Client, my_token: str, partner_c: Client) -> tuple[tuple, tuple]:
    my_pos = tuple((await my_c.call_tool("report_location", {"token": my_token})).data["position"])
    opp_pos = tuple((await partner_c.call_tool("report_location")).data["position"])
    return my_pos, opp_pos


async def _run_subgame(
    my_role: str,
    my_c: Client, partner_c: Client,
    my_token: str,
    my_start: tuple[int, int],
    max_moves: int, max_barriers: int,
    scoring: dict, rng: random.Random,
) -> dict[str, Any]:
    await my_c.call_tool("start_subgame", {"token": my_token, "position": list(my_start)})

    barriers_remaining = max_barriers if my_role == "cop" else 0
    my_barriers: list[list[int]] = []
    last_seen: dict | None = None
    captured = False
    moves_taken = max_moves

    for round_num in range(1, max_moves + 1):
        if my_role == "cop":
            last_seen = await _wait_for_new_message(my_c, my_token, last_seen)
            my_pos, opp_pos = await _get_positions(my_c, my_token, partner_c)
            if my_pos == opp_pos:
                captured, moves_taken = True, round_num
                break

        dirs = _DIRECTIONS[:]
        rng.shuffle(dirs)
        moved = False
        for d in dirs:
            res = (await my_c.call_tool("choose_action", {"token": my_token, "action": {"type": "move", "direction": d}})).data
            if res.get("accepted"):
                moved = True
                break
        if not moved and my_role == "cop" and barriers_remaining > 0:
            res = (await my_c.call_tool("choose_action", {"token": my_token, "action": {"type": "place_barrier"}})).data
            if res.get("accepted"):
                my_pos, _ = await _get_positions(my_c, my_token, partner_c)
                my_barriers.append(list(my_pos))
                await partner_c.call_tool("sync_barriers", {"barriers": my_barriers})
                barriers_remaining -= 1

        msg_text = f"{my_role} moved (round {round_num})"
        await my_c.call_tool("send_message", {"token": my_token, "text": msg_text})
        await partner_c.call_tool("receive_message", {"from_agent": my_role, "text": msg_text})

        my_pos, opp_pos = await _get_positions(my_c, my_token, partner_c)
        if my_pos == opp_pos:
            captured, moves_taken = True, round_num
            break

        if my_role == "thief":
            last_seen = await _wait_for_new_message(my_c, my_token, last_seen)
            my_pos, opp_pos = await _get_positions(my_c, my_token, partner_c)
            if my_pos == opp_pos:
                captured, moves_taken = True, round_num
                break

    cop_pts = scoring["cop_win"] if captured else scoring["cop_loss"]
    thief_pts = scoring["thief_loss"] if captured else scoring["thief_win"]
    return {
        "outcome": "cop_wins" if captured else "thief_wins",
        "move_count": moves_taken,
        "cop_points": cop_pts,
        "thief_points": thief_pts,
    }


async def _run_half_async(
    my_role: str,
    my_url: str, my_token: str,
    partner_url: str, partner_token: str,
    num_sub_games: int,
    max_moves: int, max_barriers: int,
    scoring: dict, grid_size: list[int],
    seed, half_index: int,
) -> list[dict[str, Any]]:
    rng = random.Random(str(seed))
    results = []
    for i in range(num_sub_games):
        sub_game_index = i + 1
        if sub_game_index > 1:
            await _barrier_sync(
                my_role, my_url, my_token, partner_url, partner_token,
                half_index, sub_game_index,
            )
        cop_start = (rng.randint(0, grid_size[0] - 1), rng.randint(0, grid_size[1] - 1))
        thief_start = (rng.randint(0, grid_size[0] - 1), rng.randint(0, grid_size[1] - 1))
        my_start = cop_start if my_role == "cop" else thief_start
        print(f"  Sub-game {sub_game_index}/{num_sub_games} | my start: {my_start} | cop: {cop_start} | thief: {thief_start}")
        async with _mcp_client(my_url, my_token) as my_c, _mcp_client(partner_url, partner_token) as partner_c:
            sg = await _run_subgame(my_role, my_c, partner_c, my_token, my_start,
                                    max_moves, max_barriers, scoring, rng)
        sg["index"] = sub_game_index
        results.append(sg)
        print(f"  Sub-game {sub_game_index} done | winner: {sg['outcome']} | moves: {sg['move_count']} | cop +{sg['cop_points']} thief +{sg['thief_points']}")
    return results


def build_bonus_sub_games(
    cop_half: list[dict[str, Any]], thief_half: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, int]:
    sub_games: list[dict[str, Any]] = []
    our_total = their_total = 0
    for sg in cop_half:
        sub_games.append({**sg, "role_group_1": "cop"})
        our_total += sg["cop_points"]
        their_total += sg["thief_points"]
    for i, sg in enumerate(thief_half):
        sub_games.append({**sg, "index": i + 4, "role_group_1": "thief"})
        their_total += sg["cop_points"]
        our_total += sg["thief_points"]
    return sub_games, our_total, their_total


def run_bonus_match(config: GameConfig, llm_client: LLMClient = None) -> None:
    """Run the 6-sub-game inter-group bonus round (§12.1) and email the result."""
    from hw6_race.services.reporting.mailer import MailerError, build_mailer_from_env

    other_cop_url = os.environ.get("BONUS_OTHER_MCP_COP_URL", "").strip()
    other_thief_url = os.environ.get("BONUS_OTHER_MCP_THIEF_URL", "").strip()
    if not (other_cop_url and other_thief_url):
        logger.error("Bonus round requires BONUS_OTHER_MCP_COP_URL and BONUS_OTHER_MCP_THIEF_URL in .env")
        return

    our_cop_url = os.environ.get("MCP_COP_URL", "local")
    our_cop_token = os.environ.get("MCP_COP_AUTH_TOKEN", wiring.LOCAL_COP_TOKEN)
    our_thief_url = os.environ.get("MCP_THIEF_URL", "local")
    our_thief_token = os.environ.get("MCP_THIEF_AUTH_TOKEN", wiring.LOCAL_THIEF_TOKEN)
    other_cop_token = os.environ.get("BONUS_OTHER_MCP_COP_TOKEN", "").strip()
    other_thief_token = os.environ.get("BONUS_OTHER_MCP_THIEF_TOKEN", "").strip()
    series_seed = os.environ.get("BONUS_SERIES_SEED", "bonus-2026")

    raw = config.raw
    max_moves = raw.get("max_moves", 25)
    max_barriers = raw.get("max_barriers", 5)
    grid_size = raw.get("grid_size", [5, 5])
    scoring = raw.get("scoring", {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5})

    # Half 1: we play Thief (their Cop MCP + our Thief MCP)
    logger.info("Bonus — Half 1: 3 games as Thief (their Cop MCP + our Thief MCP)")
    thief_half = asyncio.run(_run_half_async(
        "thief",
        our_thief_url, our_thief_token,
        other_cop_url, other_cop_token,
        3, max_moves, max_barriers, scoring, grid_size,
        (series_seed, 1), half_index=1,
    ))

    # Half 2: we play Cop (our Cop MCP + their Thief MCP)
    logger.info("Bonus — Half 2: 3 games as Cop (our Cop MCP + their Thief MCP)")
    cop_half = asyncio.run(_run_half_async(
        "cop",
        our_cop_url, our_cop_token,
        other_thief_url, other_thief_token,
        3, max_moves, max_barriers, scoring, grid_size,
        (series_seed, 2), half_index=2,
    ))

    sub_games, our_total, their_total = build_bonus_sub_games(cop_half, thief_half)
    our_group = os.environ.get("GROUP_NAME", "ali-ahm1")
    other_group = os.environ.get("BONUS_OTHER_GROUP_NAME", "rstabcde")
    report = InterGroupBonusReport(
        group_1_name=our_group, group_2_name=other_group,
        github_repo_group_1=os.environ.get("GITHUB_REPO", ""),
        github_repo_group_2=os.environ.get("BONUS_OTHER_GITHUB_REPO", ""),
        mcp_url_group_1_cop=our_cop_url, mcp_url_group_1_thief=our_thief_url,
        mcp_url_group_2_cop=other_cop_url, mcp_url_group_2_thief=other_thief_url,
        timezone=os.environ.get("TIMEZONE", "UTC"),
        students_group_1=[s.strip() for s in os.environ.get("STUDENTS", "Ali Trabeh,Ahmad Kais").split(",")],
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
