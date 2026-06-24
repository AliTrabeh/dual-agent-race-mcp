"""DecisionStrategy interface — pluggable Cop/Thief move-selection logic (ADR-003).

Swapping HeuristicStrategy for the optional QLearningStrategy (docs/PRD_q_learning.md)
must require no change to BaseAgent or either concrete agent class.
"""

from abc import ABC, abstractmethod

from hw6_race.services.agents.models import AgentAction, AgentObservation


class DecisionStrategy(ABC):
    """Chooses an AgentAction given the current AgentObservation.

    Input: AgentObservation (Setup data: strategy-specific hyperparameters,
    injected at construction). Output: a single AgentAction per call.
    """

    @abstractmethod
    def decide(self, observation: AgentObservation) -> AgentAction:
        """Return the action this strategy chooses for `observation`."""
