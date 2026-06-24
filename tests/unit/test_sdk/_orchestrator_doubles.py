"""Shared test doubles for sdk/orchestrator.py tests (kept out of the test files
themselves to stay under the project's 150-physical-line cap)."""

from hw6_race.services.agents.models import AgentAction, AgentObservation, Inference


class FakeAgent:
    """Test double for BaseAgent — records calls and returns canned values."""

    def __init__(self, action: AgentAction) -> None:
        self._action = action
        self.interpreted: list[str] = []
        self.composed_for: list[AgentObservation] = []

    def interpret_message(self, text: str) -> Inference:
        self.interpreted.append(text)
        return Inference(believed_position=None, confidence="ambiguous", raw_text=text)

    def compose_message(self, observation: AgentObservation) -> str:
        self.composed_for.append(observation)
        return "a message"

    def decide_action(self, observation: AgentObservation) -> AgentAction:
        return self._action


class RaisingAgent(FakeAgent):
    """Test double that always fails to decide — simulates an MCP/LLM failure."""

    def decide_action(self, observation: AgentObservation) -> AgentAction:
        raise RuntimeError("simulated MCP/LLM failure")


class FakeMCPClient:
    """Test double for AgentMCPClient — records calls, returns a canned inbox."""

    def __init__(self, inbox: list[str] | None = None) -> None:
        self._inbox = list(inbox or [])
        self.sent: list[str] = []
        self.received: list[str] = []

    async def get_inbox(self) -> list[str]:
        inbox, self._inbox = self._inbox, []
        return inbox

    async def send_message(self, text: str) -> str:
        self.sent.append(text)
        return "recorded"

    async def receive_message(self, text: str) -> str:
        self.received.append(text)
        return "delivered"

    async def __aenter__(self) -> "FakeMCPClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None
