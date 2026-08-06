from django.db.models import TextChoices


class BoardType(TextChoices):
    """How a game's goal list turns into a board.

    Mirrors bingosync's "Custom (Advanced)" modes: FIXED is the goal list
    used as-is (must be exactly rows*cols goals); RANDOMIZED draws rows*cols
    goals from a larger pool.
    """

    FIXED = "fixed", "Fixed Board"
    RANDOMIZED = "randomized", "Randomized"


class LockoutMode(TextChoices):
    NON_LOCKOUT = "non_lockout", "Non-Lockout"
    LOCKOUT = "lockout", "Lockout"
