"""Agent abstraction layer (Cop/Thief) — see PRD-004."""

from hw6_race.services.agents.base_agent import BaseAgent
from hw6_race.services.agents.cop_agent import CopAgent
from hw6_race.services.agents.llm_client import GatekeptLLMClient, LLMClient
from hw6_race.services.agents.llm_providers import AnthropicCompleteFn
from hw6_race.services.agents.models import (
    ActionType,
    AgentAction,
    AgentObservation,
    Inference,
)
from hw6_race.services.agents.thief_agent import ThiefAgent

__all__ = [
    "ActionType",
    "AgentAction",
    "AgentObservation",
    "AnthropicCompleteFn",
    "BaseAgent",
    "CopAgent",
    "GatekeptLLMClient",
    "Inference",
    "LLMClient",
    "ThiefAgent",
]
