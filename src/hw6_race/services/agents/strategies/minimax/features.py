"""Raw board features shared by both roles' evaluation functions (evaluation.py)
and the heuristic fallback (fallback.py) — computed once here so neither
duplicates the other's feature math (SG-C04).
"""

from dataclasses import dataclass

from hw6_race.constants import AgentRole
from hw6_race.services.agents.strategies.minimax.search_metrics import (
    distance_for_role,
    mobility_for_role,
    reachable_area_for_role,
)
from hw6_race.services.race.race_state import RaceState

_UNREACHABLE_DISTANCE_PENALTY = 999


@dataclass(frozen=True)
class BoardFeatures:
    """Setup: none. Input: a RaceState. Output: the numbers every evaluation
    function/heuristic needs, computed exactly once per state."""

    cop_thief_distance: int
    cop_mobility: int
    thief_mobility: int
    cop_reachable_area: int
    thief_reachable_area: int
    barriers_used: int
    barriers_remaining: int


def compute_features(state: RaceState) -> BoardFeatures:
    distance = distance_for_role(state, AgentRole.COP)
    return BoardFeatures(
        cop_thief_distance=distance if distance is not None else _UNREACHABLE_DISTANCE_PENALTY,
        cop_mobility=mobility_for_role(state, AgentRole.COP),
        thief_mobility=mobility_for_role(state, AgentRole.THIEF),
        cop_reachable_area=reachable_area_for_role(state, AgentRole.COP),
        thief_reachable_area=reachable_area_for_role(state, AgentRole.THIEF),
        barriers_used=state.barriers_placed,
        barriers_remaining=state.max_barriers - state.barriers_placed,
    )
