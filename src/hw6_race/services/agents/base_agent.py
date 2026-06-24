"""Shared Cop/Thief agent behavior (HW-F02, HW-F15). Concrete roles only override
`_role_specific_instructions` (Template Method) — no other logic is duplicated
between cop_agent.py and thief_agent.py (SG-C04).
"""

import logging
import re

from hw6_race.constants import AgentRole
from hw6_race.services.agents.llm_client import LLMClient
from hw6_race.services.agents.models import AgentObservation, Inference
from hw6_race.services.agents.strategies.base import DecisionStrategy

logger = logging.getLogger(__name__)

_POSITION_PATTERN = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*$")
_FALLBACK_MESSAGE = "no comment"


class BaseAgent:
    """Composes/interprets NL messages and decides actions for one agent role.

    Input: an AgentObservation per turn. Output: an AgentAction (decide_action),
    a text message (compose_message), or an Inference (interpret_message).
    Setup: role, LLMClient, and DecisionStrategy collaborators, injected once.

    `believed_opponent_position` is the agent's own running belief, updated
    only when interpret_message successfully parses a position — an
    ambiguous/empty/error turn preserves the last known good belief rather
    than discarding it (HW-F02: decode + infer must actually inform a move).
    """

    def __init__(
        self, role: AgentRole, llm_client: LLMClient, strategy: DecisionStrategy
    ) -> None:
        self.role = role
        self._llm_client = llm_client
        self._strategy = strategy
        self._believed_opponent_position: tuple[int, int] | None = None

    @property
    def believed_opponent_position(self) -> tuple[int, int] | None:
        return self._believed_opponent_position

    def decide_action(self, observation: AgentObservation):
        return self._strategy.decide(observation)

    def compose_message(self, observation: AgentObservation) -> str:
        prompt = self._build_compose_prompt(observation)
        try:
            text = self._llm_client.generate(prompt)
        except Exception:
            logger.exception("[%s] LLM failed while composing a message", self.role.value)
            return _FALLBACK_MESSAGE
        return text if text else _FALLBACK_MESSAGE

    def interpret_message(self, opponent_text: str) -> Inference:
        if not opponent_text:
            logger.warning("[%s] received an empty opponent message", self.role.value)
            return Inference(believed_position=None, confidence="empty", raw_text=opponent_text)

        prompt = self._build_interpret_prompt(opponent_text)
        try:
            response = self._llm_client.generate(prompt)
        except Exception:
            logger.exception("[%s] LLM failed while interpreting a message", self.role.value)
            return Inference(believed_position=None, confidence="error", raw_text=opponent_text)

        match = _POSITION_PATTERN.match(response or "")
        if not match:
            logger.warning(
                "[%s] could not parse a position from LLM response: %r", self.role.value, response
            )
            return Inference(
                believed_position=None, confidence="ambiguous", raw_text=opponent_text
            )

        position = (int(match.group(1)), int(match.group(2)))
        self._believed_opponent_position = position
        return Inference(believed_position=position, confidence="stated", raw_text=opponent_text)

    def _build_compose_prompt(self, observation: AgentObservation) -> str:
        base = (
            f"You are the {self.role.value} in a grid pursuit game. "
            f"Your position is {observation.own_position} on a {observation.grid_size} grid. "
        )
        instructions = self._role_specific_instructions(observation)
        return base + instructions + "Describe your situation or intent in one short sentence."

    def _role_specific_instructions(self, observation: AgentObservation) -> str:
        """Hook for subclasses to add role-specific prompt context. Default: none."""
        return ""

    def _build_interpret_prompt(self, opponent_text: str) -> str:
        return (
            f"The opponent said: {opponent_text!r}. "
            "If they revealed a believed grid position, reply with ONLY 'ROW,COL' "
            "(e.g. '2,3') and nothing else. If unclear, reply with ONLY 'UNKNOWN' "
            "and no explanation."
        )
