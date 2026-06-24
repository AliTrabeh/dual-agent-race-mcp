from hw6_race.constants import AgentRole
from hw6_race.services.agents.models import AgentObservation
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy
from hw6_race.services.agents.thief_agent import ThiefAgent


def test_thief_agent_role_is_thief(fake_llm_client_factory) -> None:
    agent = ThiefAgent(fake_llm_client_factory(), HeuristicStrategy())
    assert agent.role == AgentRole.THIEF


def test_thief_agent_prompt_does_not_mention_barriers(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["ok"])
    agent = ThiefAgent(llm, HeuristicStrategy())
    observation = AgentObservation(own_position=(0, 0), grid_size=(5, 5), barriers_remaining=0)

    agent.compose_message(observation)

    assert "barrier" not in llm.prompts_seen[0]
