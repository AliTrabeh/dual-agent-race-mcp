from hw6_race.services.agents.strategies.minimax.transposition import TranspositionTable
from hw6_race.services.race.race_state import RaceState


def _state(**overrides) -> RaceState:
    defaults = {
        "grid_size": (5, 5),
        "max_moves": 25,
        "max_barriers": 5,
        "cop_position": (0, 0),
        "thief_position": (4, 4),
    }
    defaults.update(overrides)
    return RaceState(**defaults)


def test_lookup_misses_on_an_empty_table() -> None:
    table = TranspositionTable()
    assert table.lookup(_state(), depth=4) is None


def test_store_then_lookup_returns_the_stored_score() -> None:
    table = TranspositionTable()
    state = _state()
    table.store(state, depth=4, score=12.5)
    assert table.lookup(state, depth=4) == 12.5
    assert len(table) == 1


def test_lookup_is_specific_to_depth() -> None:
    table = TranspositionTable()
    state = _state()
    table.store(state, depth=4, score=12.5)
    assert table.lookup(state, depth=3) is None
