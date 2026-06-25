"""Depth-limited minimax with alpha-beta pruning, move ordering, and a
transposition table. `minimax_decide` returns None if the time budget runs
out before any action could be scored — the caller (strategy.py) must treat
None as "use the heuristic fallback instead" (never silently return a bad
or illegal action).
"""

import time

from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import AgentAction
from hw6_race.services.agents.strategies.minimax.board_utils import clone_state, legal_actions
from hw6_race.services.agents.strategies.minimax.evaluation import (
    evaluate_for_cop,
    evaluate_for_thief,
)
from hw6_race.services.agents.strategies.minimax.move_ordering import (
    order_cop_actions,
    order_thief_actions,
)
from hw6_race.services.agents.strategies.minimax.transposition import TranspositionTable
from hw6_race.services.race.race_state import RaceState

_NEG_INF = float("-inf")
_POS_INF = float("inf")


def _opponent_of(role: AgentRole) -> AgentRole:
    return AgentRole.THIEF if role == AgentRole.COP else AgentRole.COP


def _ordered_actions(state: RaceState, role: AgentRole) -> list[AgentAction]:
    actions = legal_actions(state, role)
    order = order_cop_actions if role == AgentRole.COP else order_thief_actions
    return order(state, actions)


def minimax_decide(
    state: RaceState,
    role: AgentRole,
    depth: int,
    deadline: float,
    table: TranspositionTable | None = None,
) -> AgentAction | None:
    """Best action for `role` from `state`, searching `depth` plies ahead.
    Returns None only if no action could be scored before `deadline`.
    """
    table = table if table is not None else TranspositionTable()
    evaluate = evaluate_for_cop if role == AgentRole.COP else evaluate_for_thief
    actions = _ordered_actions(state, role)
    if not actions:
        return None

    best_action, best_score, alpha = actions[0], _NEG_INF, _NEG_INF
    found_any = False
    for action in actions:
        if time.monotonic() > deadline:
            break
        child = clone_state(state)
        child.apply_action(role, action)
        score = _search(child, _opponent_of(role), role, depth - 1, alpha, _POS_INF, deadline, table, evaluate)
        if score is None:
            break
        found_any = True
        if score > best_score:
            best_action, best_score = action, score
        alpha = max(alpha, best_score)

    return best_action if found_any else None


def _search(
    state: RaceState,
    mover: AgentRole,
    root_role: AgentRole,
    depth: int,
    alpha: float,
    beta: float,
    deadline: float,
    table: TranspositionTable,
    evaluate,
) -> float | None:
    if time.monotonic() > deadline:
        return None
    if state.check_outcome() is not None or depth <= 0:
        return evaluate(state)

    cached = table.lookup(state, depth)
    if cached is not None:
        return cached

    actions = _ordered_actions(state, mover)
    if not actions:
        return evaluate(state)

    maximizing = mover == root_role
    best = _NEG_INF if maximizing else _POS_INF
    for action in actions:
        child = clone_state(state)
        child.apply_action(mover, action)
        score = _search(
            child, _opponent_of(mover), root_role, depth - 1, alpha, beta, deadline, table, evaluate
        )
        if score is None:
            return None
        if maximizing:
            best = max(best, score)
            alpha = max(alpha, best)
        else:
            best = min(best, score)
            beta = min(beta, best)
        if alpha >= beta:
            break

    table.store(state, depth, best)
    return best
