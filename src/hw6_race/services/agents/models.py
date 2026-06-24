"""Shared agent-layer data contracts: actions, observations, inferences.

Defined once here — never redefined per role or per strategy — so every
DecisionStrategy and every concrete agent stays interoperable (SG-C04).
"""

from dataclasses import dataclass
from enum import StrEnum

from hw6_race.constants import MoveDirection


class ActionType(StrEnum):
    """The two kinds of action an agent may choose for one turn."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


@dataclass(frozen=True)
class AgentAction:
    """An agent's chosen action for one turn. `direction` is set only for MOVE."""

    action_type: ActionType
    direction: MoveDirection | None = None


@dataclass(frozen=True)
class AgentObservation:
    """What one agent can see when asked to decide an action or compose a message.

    `barriers_remaining` is meaningful for the Cop only; Thief observations should
    pass 0. `inbox` holds whatever NL messages have arrived since the last turn.
    """

    own_position: tuple[int, int]
    grid_size: tuple[int, int]
    barriers_remaining: int
    inbox: tuple[str, ...] = ()


@dataclass(frozen=True)
class Inference:
    """The result of interpreting an opponent's natural-language message.

    `confidence` is one of: "stated" (a position was parsed), "ambiguous"
    (LLM responded but no position was extractable), "empty" (no text received),
    or "error" (the LLM backend itself failed).
    """

    believed_position: tuple[int, int] | None
    confidence: str
    raw_text: str
