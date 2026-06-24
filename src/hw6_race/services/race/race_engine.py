"""Sub-game and 6-sub-game game loop (HW-F04/F05). Turn order: Thief moves
first, then Cop, repeating, per HW-F04 — implemented literally below.

Policies are plain callables `(RaceState) -> AgentAction`, decoupled from the
agent/strategy classes in services.agents — this engine has no knowledge of
LLMs or DecisionStrategy, only of legal-action callables (testable with stubs).
"""

from collections.abc import Callable

from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import AgentAction
from hw6_race.services.race.models import GameResult, SubGameResult
from hw6_race.services.race.race_state import RaceState
from hw6_race.services.race.scoring import score_sub_game
from hw6_race.shared.config import GameConfig

Policy = Callable[[RaceState], AgentAction]


def default_start_positions(config: GameConfig) -> tuple[tuple[int, int], tuple[int, int]]:
    """Deterministic default: Cop at the top-left corner, Thief at the bottom-right."""
    rows, cols = config.grid_size
    return (0, 0), (rows - 1, cols - 1)


def play_sub_game(
    config: GameConfig,
    thief_policy: Policy,
    cop_policy: Policy,
    cop_start: tuple[int, int],
    thief_start: tuple[int, int],
) -> SubGameResult:
    """Run one sub-game to a terminal outcome and return its scored result."""
    state = RaceState(
        grid_size=config.grid_size,
        max_moves=config.max_moves,
        max_barriers=config.max_barriers,
        cop_position=cop_start,
        thief_position=thief_start,
    )
    outcome = state.check_outcome()
    while outcome is None:
        state.apply_action(AgentRole.THIEF, thief_policy(state))
        outcome = state.check_outcome()
        if outcome is not None:
            break
        state.apply_action(AgentRole.COP, cop_policy(state))
        outcome = state.check_outcome()
    return score_sub_game(outcome, state.move_count, config)


def play_game(
    config: GameConfig,
    thief_policy: Policy,
    cop_policy: Policy,
    start_positions: list[tuple[tuple[int, int], tuple[int, int]]] | None = None,
) -> GameResult:
    """Run `config.num_games` sub-games back to back and aggregate the result."""
    positions = start_positions or [
        default_start_positions(config) for _ in range(config.num_games)
    ]
    result = GameResult()
    for cop_start, thief_start in positions:
        sub_game = play_sub_game(config, thief_policy, cop_policy, cop_start, thief_start)
        result.sub_games.append(sub_game)
    return result
