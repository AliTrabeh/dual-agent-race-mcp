from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.minimax.board_utils import (
    clone_state,
    legal_actions,
    make_belief_state,
    state_hash,
)
from hw6_race.services.race.race_state import RaceState


def _state(**overrides) -> RaceState:
    defaults = {
        "grid_size": (5, 5),
        "max_moves": 25,
        "max_barriers": 5,
        "cop_position": (0, 0),
        "thief_position": (4, 4),
    }
    defaults.update(overrides)
    return RaceState(**defaults)


def test_clone_state_is_independent_of_the_original() -> None:
    state = _state()
    clone = clone_state(state)

    clone.barriers.add((1, 1))
    clone.cop_position = (2, 2)

    assert state.barriers == set()
    assert state.cop_position == (0, 0)


def test_legal_actions_for_cop_includes_barrier_when_under_the_cap() -> None:
    state = _state(cop_position=(2, 2))
    actions = legal_actions(state, AgentRole.COP)
    assert any(a.action_type == ActionType.PLACE_BARRIER for a in actions)


def test_legal_actions_for_cop_excludes_barrier_once_cap_reached() -> None:
    state = _state(cop_position=(2, 2), max_barriers=1, barriers_placed=1)
    actions = legal_actions(state, AgentRole.COP)
    assert all(a.action_type != ActionType.PLACE_BARRIER for a in actions)


def test_legal_actions_for_thief_never_includes_barrier() -> None:
    state = _state(thief_position=(2, 2))
    actions = legal_actions(state, AgentRole.THIEF)
    assert all(a.action_type != ActionType.PLACE_BARRIER for a in actions)


def test_state_hash_distinguishes_different_states() -> None:
    state_a = _state(cop_position=(0, 0))
    state_b = _state(cop_position=(1, 0))
    assert state_hash(state_a) != state_hash(state_b)


def test_state_hash_is_identical_for_equivalent_states() -> None:
    state_a = _state(barriers={(1, 1)})
    state_b = _state(barriers={(1, 1)})
    assert state_hash(state_a) == state_hash(state_b)


def test_make_belief_state_for_cop_places_self_correctly() -> None:
    observation = AgentObservation(
        own_position=(0, 0),
        grid_size=(5, 5),
        barriers_remaining=3,
        role=AgentRole.COP,
        max_moves=25,
        max_barriers=5,
    )
    belief = make_belief_state(observation, opponent_position=(4, 4))

    assert belief.cop_position == (0, 0)
    assert belief.thief_position == (4, 4)
    assert belief.barriers_placed == 2  # 5 max - 3 remaining


def test_make_belief_state_for_thief_places_self_correctly() -> None:
    observation = AgentObservation(
        own_position=(4, 4),
        grid_size=(5, 5),
        barriers_remaining=0,
        role=AgentRole.THIEF,
        barriers=frozenset({(1, 1), (2, 2)}),
        max_moves=25,
        max_barriers=5,
    )
    belief = make_belief_state(observation, opponent_position=(0, 0))

    assert belief.cop_position == (0, 0)
    assert belief.thief_position == (4, 4)
    assert belief.barriers_placed == 2  # len(observation.barriers)
