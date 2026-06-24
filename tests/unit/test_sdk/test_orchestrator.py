from _orchestrator_doubles import FakeAgent, FakeMCPClient

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.sdk.orchestrator import observation_for, take_turn
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.race.race_state import RaceState


def _state() -> RaceState:
    return RaceState(
        grid_size=(5, 5), max_moves=25, max_barriers=5, cop_position=(0, 0), thief_position=(4, 4)
    )


def test_observation_for_cop_reports_remaining_barriers() -> None:
    state = _state()
    state.barriers_placed = 2
    observation = observation_for(state, AgentRole.COP)
    assert observation.own_position == (0, 0)
    assert observation.barriers_remaining == 3


def test_observation_for_thief_always_reports_zero_barriers() -> None:
    state = _state()
    observation = observation_for(state, AgentRole.THIEF)
    assert observation.own_position == (4, 4)
    assert observation.barriers_remaining == 0


async def test_take_turn_interprets_every_inbox_message() -> None:
    state = _state()
    agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.RIGHT))
    own_client = FakeMCPClient(inbox=["msg one", "msg two"])
    opponent_client = FakeMCPClient()

    await take_turn(state, AgentRole.COP, agent, own_client, opponent_client)

    assert agent.interpreted == ["msg one", "msg two"]


async def test_take_turn_relays_the_composed_message_to_the_opponent() -> None:
    state = _state()
    agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.RIGHT))
    own_client = FakeMCPClient()
    opponent_client = FakeMCPClient()

    await take_turn(state, AgentRole.COP, agent, own_client, opponent_client)

    assert own_client.sent == ["a message"]
    assert opponent_client.received == ["a message"]


async def test_take_turn_applies_the_decided_action_to_state() -> None:
    state = _state()
    agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.LEFT))
    own_client = FakeMCPClient()
    opponent_client = FakeMCPClient()

    await take_turn(state, AgentRole.THIEF, agent, own_client, opponent_client)

    assert state.thief_position == (4, 3)
    assert state.move_count == 1
