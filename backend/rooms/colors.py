from enum import IntFlag, auto


class Color(IntFlag):
    """A player color, or (for a square) any combination of player colors.

    Using IntFlag gives us bitmask composition (`Color.RED | Color.BLUE`),
    membership tests (`Color.RED in square.color`), and removal
    (`square.color & ~Color.RED`) for free, in place of bingosync's
    hand-rolled CompositeColor class.
    """

    BLANK = 0
    RED = auto()
    BLUE = auto()
    GREEN = auto()
    ORANGE = auto()
    PURPLE = auto()
    NAVY = auto()
    TEAL = auto()
    PINK = auto()
    BROWN = auto()
    YELLOW = auto()

    @property
    def names(self) -> list[str]:
        """The individual color names making up this (possibly composite) value."""
        if self is Color.BLANK:
            return []
        return [color.name.lower() for color in Color if color is not Color.BLANK and color in self]


# Choices for fields that hold a single, non-composite color (e.g. a player's
# chosen color). Squares use the raw bitmask instead, since enumerating every
# 2^10 combination as admin choices isn't useful.
PLAYER_COLOR_CHOICES = [(color.value, color.name.title()) for color in Color if color is not Color.BLANK]

# Lowercase names, for the API layer (matches Color.names' lowercase convention).
PLAYER_COLOR_NAMES = [color.name.lower() for color in Color if color is not Color.BLANK]


def color_from_name(name: str) -> Color:
    try:
        return Color[name.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown color: {name!r}") from exc
