"""RandomDecisionStrategy: a baseline opponent with no reasoning at all, used
to benchmark the minimax strategy against (tools/simulate_strategies.py).
Never returned by build_agents — purely a benchmarking baseline.
"""

import random

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy
from hw6_race.services.agents.strategies.grid_utils import stays_in_bounds


class RandomDecisionStrategy(DecisionStrategy):
    """Setup: an optional random.Random for determinism in tests. Input: an
    AgentObservation. Output: a uniformly random legal move."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()

    def decide(self, observation: AgentObservation) -> AgentAction:
        legal_directions = [d for d in MoveDirection if stays_in_bounds(observation, d)]
        return AgentAction(ActionType.MOVE, self._rng.choice(legal_directions))
