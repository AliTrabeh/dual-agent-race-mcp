"""Transposition table: caches a state's evaluated score at a given search
depth so the same state reached via a different move order isn't re-searched.
Scoped to a single decide() call — not persisted across turns, since the
board genuinely changes every turn anyway.
"""

from hw6_race.services.agents.strategies.minimax.board_utils import state_hash
from hw6_race.services.race.race_state import RaceState


class TranspositionTable:
    """Setup: none. Input: (state, depth) lookups/stores. Output: a cached
    score, or a cache miss signaled by `lookup` returning None."""

    def __init__(self) -> None:
        self._table: dict[tuple, float] = {}

    def _key(self, state: RaceState, depth: int) -> tuple:
        return (*state_hash(state), depth)

    def lookup(self, state: RaceState, depth: int) -> float | None:
        return self._table.get(self._key(state, depth))

    def store(self, state: RaceState, depth: int, score: float) -> None:
        self._table[self._key(state, depth)] = score

    def __len__(self) -> int:
        return len(self._table)
