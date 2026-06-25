"""Heuristic one-ply fallback, used when minimax search times out or is
otherwise unavailable. Scores every legal action by simulating it on a
cloned state (never the real one) and evaluating the result with the SAME
evaluation functions minimax itself uses, so fallback and search stay
consistent with each other.
"""

from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.agents.strategies.minimax.board_utils import clone_state, legal_actions
from hw6_race.services.agents.strategies.minimax.evaluation import (
    evaluate_for_cop,
    evaluate_for_thief,
)
from hw6_race.services.agents.strategies.minimax.search_metrics import is_safe_for_thief
from hw6_race.services.race.race_state import RaceState

_THIEF_SAFETY_BONUS = 50.0


def fallback_action(state: RaceState, role: AgentRole) -> AgentAction:
    """Pick the legal action whose resulting position scores best for `role`."""
    candidates = legal_actions(state, role)
    evaluate = evaluate_for_cop if role == AgentRole.COP else evaluate_for_thief

    best_action, best_score = candidates[0], float("-inf")
    for action in candidates:
        score = _score_action(state, role, action, evaluate)
        if score > best_score:
            best_action, best_score = action, score
    return best_action


def _score_action(state: RaceState, role: AgentRole, action: AgentAction, evaluate) -> float:
    next_state = clone_state(state)
    next_state.apply_action(role, action)

    safety_bonus = 0.0
    if role == AgentRole.THIEF and action.action_type == ActionType.MOVE:
        safety_bonus = _THIEF_SAFETY_BONUS if is_safe_for_thief(state, next_state.thief_position) else 0.0

    return evaluate(next_state) + safety_bonus
