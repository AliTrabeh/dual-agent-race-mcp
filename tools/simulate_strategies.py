"""Benchmark: pits decision strategies against each other directly on
RaceState, bypassing MCP/LLM/NL-inference — this isolates the search
algorithm's quality from natural-language inference noise (that pipeline is
already verified separately by tests/integration/test_staged_sanity_checks.py).

Each strategy is fed the GROUND-TRUTH opponent position as its belief, since
this script measures decision-making quality, not inference quality.

Usage: uv run python tools/simulate_strategies.py [--games 30] [--grid 5]
"""

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hw6_race.constants import AgentRole, GameOutcome  # noqa: E402
from hw6_race.services.agents.models import AgentObservation  # noqa: E402
from hw6_race.services.agents.strategies.base import DecisionStrategy  # noqa: E402
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy  # noqa: E402
from hw6_race.services.agents.strategies.minimax.strategy import (
    MinimaxDecisionStrategy,  # noqa: E402
)
from hw6_race.services.agents.strategies.random_strategy import RandomDecisionStrategy  # noqa: E402
from hw6_race.services.race.exceptions import IllegalActionError, IllegalMoveError  # noqa: E402
from hw6_race.services.race.race_state import RaceState  # noqa: E402

MAX_BARRIERS = 5


def _observation(state: RaceState, role: AgentRole) -> AgentObservation:
    own = state.cop_position if role == AgentRole.COP else state.thief_position
    opponent = state.thief_position if role == AgentRole.COP else state.cop_position
    return AgentObservation(
        own_position=own,
        grid_size=state.grid_size,
        barriers_remaining=state.max_barriers - state.barriers_placed,
        role=role,
        believed_opponent_position=opponent,
        barriers=frozenset(state.barriers),
        move_count=state.move_count,
        max_moves=state.max_moves,
        max_barriers=state.max_barriers,
    )


def play_one_game(cop: DecisionStrategy, thief: DecisionStrategy, grid_size: int, max_moves: int) -> dict:
    state = RaceState(
        grid_size=(grid_size, grid_size),
        max_moves=max_moves,
        max_barriers=MAX_BARRIERS,
        cop_position=(0, 0),
        thief_position=(grid_size - 1, grid_size - 1),
    )
    illegal_actions = 0
    while state.check_outcome() is None:
        for role, strategy in ((AgentRole.THIEF, thief), (AgentRole.COP, cop)):
            if state.check_outcome() is not None:
                break
            action = strategy.decide(_observation(state, role))
            try:
                state.apply_action(role, action)
            except (IllegalMoveError, IllegalActionError):
                illegal_actions += 1

    outcome = state.check_outcome()
    return {
        "outcome": outcome,
        "capture_turn": state.move_count if outcome == GameOutcome.COP_WIN else None,
        "barriers_used": state.barriers_placed,
        "illegal_actions": illegal_actions,
    }


def run_matchup(name: str, cop_factory, thief_factory, games: int, grid_size: int, max_moves: int) -> None:
    results = [play_one_game(cop_factory(), thief_factory(), grid_size, max_moves) for _ in range(games)]
    cop_wins = sum(1 for r in results if r["outcome"] == GameOutcome.COP_WIN)
    capture_turns = [r["capture_turn"] for r in results if r["capture_turn"] is not None]
    illegal_total = sum(r["illegal_actions"] for r in results)
    barriers_avg = statistics.mean(r["barriers_used"] for r in results)

    print(f"\n=== {name} ({games} games on {grid_size}x{grid_size}) ===")
    print(f"Cop win rate:      {cop_wins / games:.0%}")
    print(f"Thief survival:    {1 - cop_wins / games:.0%}")
    if capture_turns:
        print(f"Avg capture turn:  {statistics.mean(capture_turns):.1f}")
    print(f"Avg barriers used: {barriers_avg:.1f}")
    print(f"Illegal actions:   {illegal_total}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--grid", type=int, default=5)
    parser.add_argument("--max-moves", type=int, default=None)
    args = parser.parse_args()
    max_moves = args.max_moves or args.grid * args.grid

    rng = random.Random(0)
    matchups = [
        ("Minimax Cop vs Heuristic Thief", lambda: MinimaxDecisionStrategy(depth=6), HeuristicStrategy),
        (
            "Minimax Cop vs Random Thief",
            lambda: MinimaxDecisionStrategy(depth=6),
            lambda: RandomDecisionStrategy(rng),
        ),
        ("Heuristic Cop vs Minimax Thief", HeuristicStrategy, lambda: MinimaxDecisionStrategy(depth=6)),
        (
            "Random Cop vs Minimax Thief",
            lambda: RandomDecisionStrategy(rng),
            lambda: MinimaxDecisionStrategy(depth=6),
        ),
        (
            "Minimax Cop vs Minimax Thief",
            lambda: MinimaxDecisionStrategy(depth=6),
            lambda: MinimaxDecisionStrategy(depth=6),
        ),
    ]

    start = time.monotonic()
    for name, cop_factory, thief_factory in matchups:
        run_matchup(name, cop_factory, thief_factory, args.games, args.grid, max_moves)
    print(f"\nTotal benchmark time: {time.monotonic() - start:.1f}s")


if __name__ == "__main__":
    main()
