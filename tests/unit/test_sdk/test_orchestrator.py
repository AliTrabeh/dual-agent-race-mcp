from _orchestrator_doubles import FakeAgent, FakeMCPClient, RaisingAgent

from hw6_race.constants import AgentRole, GameOutcome, MoveDirection
from hw6_race.sdk.orchestrator import observation_for, play_game_async, take_turn
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.race.race_state import RaceState
from hw6_race.shared.config import GameConfig


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


async def test_play_game_async_records_technical_loss_and_retries_when_agent_always_raises() -> None:
    config = GameConfig({
        "version": "1.00",
        "grid_size": [3, 3],
        "max_moves": 6,
        "num_games": 1,
        "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    })
    action = AgentAction(ActionType.MOVE, MoveDirection.RIGHT)
    cop_agent = RaisingAgent(action)
    thief_agent = RaisingAgent(action)
    cop_client = FakeMCPClient()
    thief_client = FakeMCPClient()

    result = await play_game_async(config, thief_agent, cop_agent, thief_client, cop_client)

    assert len(result.sub_games) == 1
    assert result.sub_games[0].outcome == GameOutcome.TECHNICAL_LOSS
