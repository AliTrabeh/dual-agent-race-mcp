"""Reuses services.race.race_state.RaceState as the search substrate — no
game rule (legality/capture/scoring) is ever reimplemented here, only read or
copied. `make_belief_state` builds a RaceState from one agent's own
legitimate knowledge (its true position, the real barriers, and its current
best *estimate* of the opponent) — search never touches engine ground truth.
"""

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation
from hw6_race.services.race.race_state import RaceState


def clone_state(state: RaceState) -> RaceState:
    """Return an independent copy — search must never mutate a shared state."""
    return RaceState(
        grid_size=state.grid_size,
        max_moves=state.max_moves,
        max_barriers=state.max_barriers,
        cop_position=state.cop_position,
        thief_position=state.thief_position,
        move_count=state.move_count,
        barriers=set(state.barriers),
        barriers_placed=state.barriers_placed,
    )


def legal_actions(state: RaceState, role: AgentRole) -> list[AgentAction]:
    """Enumerate every legal action for `role`, using RaceState's own checks."""
    actions = [
        AgentAction(ActionType.MOVE, direction)
        for direction in MoveDirection
        if state.is_legal_move(role, direction)
    ]
    if role == AgentRole.COP and state.barriers_placed < state.max_barriers:
        actions.append(AgentAction(ActionType.PLACE_BARRIER))
    return actions


def state_hash(state: RaceState) -> tuple:
    """A hashable key identifying this state, for the transposition table."""
    return (
        state.cop_position,
        state.thief_position,
        frozenset(state.barriers),
        state.barriers_placed,
        state.move_count,
    )


def make_belief_state(observation: AgentObservation, opponent_position: tuple[int, int]) -> RaceState:
    """Build a RaceState representing this agent's best estimate of the true
    game state, for local search ONLY — `opponent_position` is always a
    belief/estimate, never read from the real engine state.
    """
    if observation.role == AgentRole.COP:
        cop_position, thief_position = observation.own_position, opponent_position
        barriers_placed = observation.max_barriers - observation.barriers_remaining
    else:
        cop_position, thief_position = opponent_position, observation.own_position
        barriers_placed = len(observation.barriers)

    return RaceState(
        grid_size=observation.grid_size,
        max_moves=observation.max_moves,
        max_barriers=observation.max_barriers,
        cop_position=cop_position,
        thief_position=thief_position,
        move_count=observation.move_count,
        barriers=set(observation.barriers),
        barriers_placed=barriers_placed,
    )
