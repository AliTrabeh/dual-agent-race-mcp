"""Thief agent — uses BaseAgent's behavior unchanged (no barrier awareness needed).

Kept as an explicit class (rather than instantiating BaseAgent directly) so the
agent layer's public API names both roles symmetrically, matching cop_agent.py.
"""

from hw6_race.constants import AgentRole
from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.agents.strategies.base import DecisionStrategy


class ThiefAgent(BaseAgent):
    """The evading agent. Moves first each turn; may never place barriers (HW-F10)."""

    def __init__(self, llm_client: LLMClient, strategy: DecisionStrategy) -> None:
        super().__init__(AgentRole.THIEF, llm_client, strategy)
