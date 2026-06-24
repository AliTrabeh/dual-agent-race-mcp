"""Grid state: positions, barriers, move count, legality, win-condition checks.

Documented interpretations (see docs/prds/PRD-003-dual-agent-race-logic.md):
- A same-cell start is treated as an immediate Cop capture (move_count stays 0).
- Capture is checked after every individual move, whichever agent caused it —
  the HW PDF only describes the Cop "reaching" the Thief, but a Thief moving
  onto the Cop's cell is physically the same state and is treated identically.
- "25 moves" is a TOTAL move count shared by both agents, not per-agent.
"""

from dataclasses import dataclass, field

from hw6_race.constants import AgentRole, GameOutcome, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.services.race.exceptions import IllegalActionError, IllegalMoveError

_DELTAS: dict[MoveDirection, tuple[int, int]] = {
    MoveDirection.UP: (-1, 0),
    MoveDirection.DOWN: (1, 0),
    MoveDirection.LEFT: (0, -1),
    MoveDirection.RIGHT: (0, 1),
}


@dataclass
class RaceState:
    """Setup: grid_size, max_moves, max_barriers, starting positions.
    Input: one AgentAction per apply_action() call. Output: the mutated state,
    queried via check_outcome() for the terminal result (None while ongoing).
    """

    grid_size: tuple[int, int]
    max_moves: int
    max_barriers: int
    cop_position: tuple[int, int]
    thief_position: tuple[int, int]
    move_count: int = 0
    barriers: set[tuple[int, int]] = field(default_factory=set)
    barriers_placed: int = 0

    def in_bounds(self, position: tuple[int, int]) -> bool:
        rows, cols = self.grid_size
        return 0 <= position[0] < rows and 0 <= position[1] < cols

    def _position_of(self, role: AgentRole) -> tuple[int, int]:
        return self.cop_position if role == AgentRole.COP else self.thief_position

    def _destination(
        self, position: tuple[int, int], direction: MoveDirection
    ) -> tuple[int, int]:
        d_row, d_col = _DELTAS[direction]
        return position[0] + d_row, position[1] + d_col

    def is_legal_move(self, role: AgentRole, direction: MoveDirection) -> bool:
        destination = self._destination(self._position_of(role), direction)
        if not self.in_bounds(destination):
            return False
        return not (role == AgentRole.COP and destination in self.barriers)

    def apply_action(self, role: AgentRole, action: AgentAction) -> None:
        """Mutate state per `action`; raises IllegalMoveError/IllegalActionError."""
        if action.action_type == ActionType.PLACE_BARRIER:
            self._place_barrier(role)
        else:
            self._move(role, action.direction)
        self.move_count += 1

    def _move(self, role: AgentRole, direction: MoveDirection) -> None:
        if not self.is_legal_move(role, direction):
            raise IllegalMoveError(f"{role.value} cannot move {direction.value} right now")
        destination = self._destination(self._position_of(role), direction)
        if role == AgentRole.COP:
            self.cop_position = destination
        else:
            self.thief_position = destination

    def _place_barrier(self, role: AgentRole) -> None:
        if role != AgentRole.COP:
            raise IllegalActionError("Only the Cop may place a barrier")
        if self.barriers_placed >= self.max_barriers:
            raise IllegalActionError(f"Cop already placed the max of {self.max_barriers} barriers")
        self.barriers.add(self.cop_position)
        self.barriers_placed += 1

    def check_outcome(self) -> GameOutcome | None:
        if self.cop_position == self.thief_position:
            return GameOutcome.COP_WIN
        if self.move_count >= self.max_moves:
            return GameOutcome.THIEF_WIN
        return None
