import pytest

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation


class _FixedActionStrategy:
    """Test double for DecisionStrategy — always returns the same configured action."""

    def __init__(self, action: AgentAction) -> None:
        self._action = action

    def decide(self, observation: AgentObservation) -> AgentAction:
        return self._action


@pytest.fixture
def observation() -> AgentObservation:
    return AgentObservation(own_position=(1, 1), grid_size=(5, 5), barriers_remaining=2)


def test_decide_action_delegates_to_the_strategy(
    fake_llm_client_factory, observation: AgentObservation
) -> None:
    sentinel = AgentAction(action_type=ActionType.MOVE, direction=MoveDirection.UP)
    agent = BaseAgent(AgentRole.COP, fake_llm_client_factory(), _FixedActionStrategy(sentinel))

    assert agent.decide_action(observation) is sentinel


def test_compose_message_returns_the_llm_text(
    fake_llm_client_factory, observation: AgentObservation
) -> None:
    llm = fake_llm_client_factory(responses=["thief is nearby"])
    agent = BaseAgent(AgentRole.COP, llm, _FixedActionStrategy(None))

    assert agent.compose_message(observation) == "thief is nearby"


def test_compose_message_falls_back_when_llm_raises(
    fake_llm_client_factory, observation: AgentObservation
) -> None:
    llm = fake_llm_client_factory(raises=RuntimeError("backend down"))
    agent = BaseAgent(AgentRole.COP, llm, _FixedActionStrategy(None))

    assert agent.compose_message(observation) == "no comment"


def test_compose_message_falls_back_when_llm_returns_empty(
    fake_llm_client_factory, observation: AgentObservation
) -> None:
    llm = fake_llm_client_factory(responses=[""])
    agent = BaseAgent(AgentRole.COP, llm, _FixedActionStrategy(None))

    assert agent.compose_message(observation) == "no comment"


def test_interpret_message_parses_a_well_formed_position(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["2,3"])
    agent = BaseAgent(AgentRole.THIEF, llm, _FixedActionStrategy(None))

    inference = agent.interpret_message("I think you're near the middle")

    assert inference.believed_position == (2, 3)
    assert inference.confidence == "stated"


def test_interpret_message_handles_an_ambiguous_response(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["UNKNOWN"])
    agent = BaseAgent(AgentRole.THIEF, llm, _FixedActionStrategy(None))

    inference = agent.interpret_message("not sure where you are")

    assert inference.believed_position is None
    assert inference.confidence == "ambiguous"


def test_interpret_message_handles_empty_opponent_text_without_calling_the_llm(
    fake_llm_client_factory,
) -> None:
    llm = fake_llm_client_factory(responses=["should not be used"])
    agent = BaseAgent(AgentRole.THIEF, llm, _FixedActionStrategy(None))

    inference = agent.interpret_message("")

    assert inference.confidence == "empty"
    assert llm.prompts_seen == []


def test_interpret_message_handles_llm_error(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(raises=RuntimeError("backend down"))
    agent = BaseAgent(AgentRole.THIEF, llm, _FixedActionStrategy(None))

    inference = agent.interpret_message("hello")

    assert inference.believed_position is None
    assert inference.confidence == "error"
