from hw6_race.constants import AgentRole
from hw6_race.services.agents.cop_agent import CopAgent
from hw6_race.services.agents.models import AgentObservation
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy


def test_cop_agent_role_is_cop(fake_llm_client_factory) -> None:
    agent = CopAgent(fake_llm_client_factory(), HeuristicStrategy())
    assert agent.role == AgentRole.COP


def test_cop_agent_prompt_mentions_barriers_remaining(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["ok"])
    agent = CopAgent(llm, HeuristicStrategy())
    observation = AgentObservation(own_position=(0, 0), grid_size=(5, 5), barriers_remaining=3)

    agent.compose_message(observation)

    assert "3 barrier" in llm.prompts_seen[0]
