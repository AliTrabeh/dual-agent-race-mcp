"""Race-domain exceptions (PRD-003 edge cases)."""


class IllegalMoveError(Exception):
    """Raised when an agent attempts to move off the grid or through a barrier."""


class IllegalActionError(Exception):
    """Raised when an agent attempts an action it is not allowed to take —
    e.g. the Thief placing a barrier, or the Cop exceeding its barrier limit.
    """
