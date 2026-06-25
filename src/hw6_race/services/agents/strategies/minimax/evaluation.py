"""Leaf evaluation functions for minimax — evaluate_for_cop/evaluate_for_thief.

Terminal states are scored first, using the SAME RaceState.check_outcome()
the real engine uses (no rule reimplementation); non-terminal states are
scored from BoardFeatures via tunable weights. An immediate winning action
always scores WIN_SCORE, which already satisfies "check for immediate win
first" without any separate explicit check.
"""

from hw6_race.constants import GameOutcome
from hw6_race.services.agents.strategies.minimax.features import compute_features
from hw6_race.services.race.race_state import RaceState

WIN_SCORE = 10_000.0

# Tunable weights — see tools/simulate_strategies.py for matchup-based tuning.
COP_DISTANCE_WEIGHT = 10.0
COP_THIEF_MOBILITY_WEIGHT = 5.0
COP_THIEF_AREA_WEIGHT = 2.0

THIEF_DISTANCE_WEIGHT = 10.0
THIEF_OWN_MOBILITY_WEIGHT = 5.0
THIEF_OWN_AREA_WEIGHT = 2.0


def evaluate_for_cop(state: RaceState) -> float:
    """Higher is better for the Cop: close to the Thief, Thief boxed in."""
    outcome = state.check_outcome()
    if outcome == GameOutcome.COP_WIN:
        return WIN_SCORE
    if outcome == GameOutcome.THIEF_WIN:
        return -WIN_SCORE

    features = compute_features(state)
    return (
        -COP_DISTANCE_WEIGHT * features.cop_thief_distance
        - COP_THIEF_MOBILITY_WEIGHT * features.thief_mobility
        - COP_THIEF_AREA_WEIGHT * features.thief_reachable_area
    )


def evaluate_for_thief(state: RaceState) -> float:
    """Higher is better for the Thief: far from the Cop, room to maneuver."""
    outcome = state.check_outcome()
    if outcome == GameOutcome.THIEF_WIN:
        return WIN_SCORE
    if outcome == GameOutcome.COP_WIN:
        return -WIN_SCORE

    features = compute_features(state)
    return (
        THIEF_DISTANCE_WEIGHT * features.cop_thief_distance
        + THIEF_OWN_MOBILITY_WEIGHT * features.thief_mobility
        + THIEF_OWN_AREA_WEIGHT * features.thief_reachable_area
    )
