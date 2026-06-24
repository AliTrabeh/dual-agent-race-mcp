"""Project-wide named constants. No magic values belong in any other module (SG-C08)."""

from enum import StrEnum

DEFAULT_CONFIG_PATH = "config/setup.json"
DEFAULT_RATE_LIMITS_PATH = "config/rate_limits.json"

DEFAULT_GRID_SIZE = (5, 5)
DEFAULT_MAX_MOVES = 25
DEFAULT_NUM_SUB_GAMES = 6
DEFAULT_MAX_BARRIERS = 5

DEFAULT_RATE_LIMIT_SERVICE = "default"


class GameOutcome(StrEnum):
    """Possible terminal outcomes of a single sub-game."""

    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"
    TECHNICAL_LOSS = "technical_loss"


class MoveDirection(StrEnum):
    """The 4 legal movement directions (no diagonals, HW-F07)."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class AgentRole(StrEnum):
    """The two agent roles in the pursuit game."""

    COP = "cop"
    THIEF = "thief"
