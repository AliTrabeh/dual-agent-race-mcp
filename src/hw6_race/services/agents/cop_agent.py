"""Cop agent — overrides only the role-specific prompt hook (Template Method).

All decision/communication logic lives in BaseAgent; this class exists to make
the Cop's one genuine behavioral difference (barrier awareness) explicit and
testable without duplicating any of BaseAgent's logic (SG-C04).
"""

from hw6_race.constants import AgentRole
from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.agents.models import AgentObservation
from hw6_race.services.agents.strategies.base import DecisionStrategy


class CopAgent(BaseAgent):
    """The pursuing agent. May place barriers (HW-F10); moves second each turn."""

    def __init__(self, llm_client: LLMClient, strategy: DecisionStrategy) -> None:
        super().__init__(AgentRole.COP, llm_client, strategy)

    def _role_specific_instructions(self, observation: AgentObservation) -> str:
        return f"You have {observation.barriers_remaining} barrier placement(s) remaining. "
