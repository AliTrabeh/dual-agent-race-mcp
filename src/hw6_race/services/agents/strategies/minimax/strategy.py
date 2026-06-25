"""MinimaxDecisionStrategy: depth-limited minimax + alpha-beta over the
agent's own belief state (never the real engine's ground truth — see
board_utils.make_belief_state). Falls back to the heuristic scorer whenever
search times out, finds nothing, or raises — never crashes, never lets an
illegal action through.

Maintains its own running estimate of the opponent's position, refined from
`observation.believed_opponent_position` whenever NL inference succeeds, and
defaulting to the grid's opposite corner on the very first call (a neutral
prior — the search is active from move 1, not only once inference happens).
"""

import logging
import time

from hw6_race.services.agents.models import AgentAction, AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy
from hw6_race.services.agents.strategies.minimax.board_utils import make_belief_state
from hw6_race.services.agents.strategies.minimax.fallback import fallback_action
from hw6_race.services.agents.strategies.minimax.search import minimax_decide

logger = logging.getLogger(__name__)

DEFAULT_DEPTH = 6
DEFAULT_TIME_BUDGET_SECONDS = 2.0


class MinimaxDecisionStrategy(DecisionStrategy):
    """Setup: search depth and a per-decision time budget. Input: an
    AgentObservation. Output: the action minimax (or, on failure, the
    heuristic fallback) judges best.
    """

    def __init__(
        self, depth: int = DEFAULT_DEPTH, time_budget_seconds: float = DEFAULT_TIME_BUDGET_SECONDS
    ) -> None:
        self._depth = depth
        self._time_budget_seconds = time_budget_seconds
        self._estimated_opponent_position: tuple[int, int] | None = None

    def decide(self, observation: AgentObservation) -> AgentAction:
        opponent_position = self._update_estimate(observation)
        state = make_belief_state(observation, opponent_position)

        try:
            deadline = time.monotonic() + self._time_budget_seconds
            action = minimax_decide(state, observation.role, self._depth, deadline)
        except Exception:
            logger.exception("Minimax search failed; using the heuristic fallback")
            action = None

        if action is None:
            logger.info("Minimax found no result in time; using the heuristic fallback")
            action = fallback_action(state, observation.role)
        return action

    def _update_estimate(self, observation: AgentObservation) -> tuple[int, int]:
        if observation.believed_opponent_position is not None:
            self._estimated_opponent_position = observation.believed_opponent_position
        elif self._estimated_opponent_position is None:
            self._estimated_opponent_position = self._default_prior(observation)
        return self._estimated_opponent_position

    @staticmethod
    def _default_prior(observation: AgentObservation) -> tuple[int, int]:
        """Neutral first guess: the corner diagonally opposite this agent."""
        rows, cols = observation.grid_size
        row, col = observation.own_position
        return (rows - 1 - row, cols - 1 - col)
