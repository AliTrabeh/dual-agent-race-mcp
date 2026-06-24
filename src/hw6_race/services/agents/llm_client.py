"""LLMClient interface + a Gatekeeper-routed implementation (HW-F19, SG-C05).

Provider choice (OpenAI/Anthropic/Gemini/Ollama) is a Setup-time decision made
by whichever `complete_fn` callable is injected — never hard-coded here, so
swapping the configured LLM architecture requires no change to this module.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from hw6_race.shared.gatekeeper import ApiGatekeeper


class LLMClient(ABC):
    """Produces natural-language text given a prompt."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the backend's text response to `prompt`."""


class GatekeptLLMClient(LLMClient):
    """Wraps any provider callable, routing every call through the ApiGatekeeper.

    Input: a prompt string. Output: the backend's raw text response, unmodified.
    Setup: an ApiGatekeeper instance and a `complete_fn(prompt) -> str` callable.
    """

    def __init__(self, gatekeeper: ApiGatekeeper, complete_fn: Callable[[str], str]) -> None:
        self._gatekeeper = gatekeeper
        self._complete_fn = complete_fn

    def generate(self, prompt: str) -> str:
        return self._gatekeeper.execute(self._complete_fn, prompt)
