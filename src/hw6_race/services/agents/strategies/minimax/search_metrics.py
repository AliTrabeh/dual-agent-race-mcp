"""BFS-based board metrics for heuristic evaluation: shortest-path distance,
reachable area, mobility, and Thief-safety — all role-aware, since barriers
block only the Cop (HW-F10, one-way). Pure functions, no RaceState mutation.
"""

from collections import deque

from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.strategies.grid_utils import MOVE_DELTAS
from hw6_race.services.race.race_state import RaceState

Position = tuple[int, int]


def _neighbors(position: Position, grid_size: tuple[int, int], blocked: frozenset[Position]):
    rows, cols = grid_size
    for d_row, d_col in MOVE_DELTAS.values():
        candidate = (position[0] + d_row, position[1] + d_col)
        if 0 <= candidate[0] < rows and 0 <= candidate[1] < cols and candidate not in blocked:
            yield candidate


def bfs_distance(
    grid_size: tuple[int, int], blocked: frozenset[Position], start: Position, goal: Position
) -> int | None:
    """Shortest legal-move distance from `start` to `goal`, or None if unreachable."""
    if start == goal:
        return 0
    visited = {start}
    queue = deque([(start, 0)])
    while queue:
        position, distance = queue.popleft()
        for neighbor in _neighbors(position, grid_size, blocked):
            if neighbor in visited:
                continue
            if neighbor == goal:
                return distance + 1
            visited.add(neighbor)
            queue.append((neighbor, distance + 1))
    return None


def reachable_area(grid_size: tuple[int, int], blocked: frozenset[Position], start: Position) -> int:
    """Count of cells reachable from `start` (including itself)."""
    visited = {start}
    queue = deque([start])
    while queue:
        position = queue.popleft()
        for neighbor in _neighbors(position, grid_size, blocked):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return len(visited)


def _blocked_for(state: RaceState, role: AgentRole) -> frozenset[Position]:
    return frozenset(state.barriers) if role == AgentRole.COP else frozenset()


def distance_for_role(state: RaceState, role: AgentRole) -> int | None:
    own = state.cop_position if role == AgentRole.COP else state.thief_position
    other = state.thief_position if role == AgentRole.COP else state.cop_position
    return bfs_distance(state.grid_size, _blocked_for(state, role), own, other)


def reachable_area_for_role(state: RaceState, role: AgentRole) -> int:
    own = state.cop_position if role == AgentRole.COP else state.thief_position
    return reachable_area(state.grid_size, _blocked_for(state, role), own)


def mobility_for_role(state: RaceState, role: AgentRole) -> int:
    """Count of legal MOVE directions (barrier placement is not mobility)."""
    return sum(1 for direction in MoveDirection if state.is_legal_move(role, direction))


def cop_threat_positions(state: RaceState) -> frozenset[Position]:
    """Cells the Cop could occupy after its very next action (incl. staying put)."""
    destinations = {state.cop_position}
    for direction in MoveDirection:
        if state.is_legal_move(AgentRole.COP, direction):
            d_row, d_col = MOVE_DELTAS[direction]
            destinations.add((state.cop_position[0] + d_row, state.cop_position[1] + d_col))
    return frozenset(destinations)


def is_safe_for_thief(state: RaceState, candidate_thief_position: Position) -> bool:
    """Would `candidate_thief_position` survive the Cop's immediate next action?"""
    return candidate_thief_position not in cop_threat_positions(state)
