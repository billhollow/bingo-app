import random

from rest_framework import status
from rest_framework.exceptions import APIException

from rooms.choices import BoardType


class InvalidBoardError(APIException):
    """Domain errors carry their own HTTP status so views don't translate them.

    DRF's default handler already renders APIException as {"detail": "..."},
    which is the shape this API returns everywhere - so subclassing here lets
    every view drop its try/except and just let the exception propagate.
    """

    status_code = status.HTTP_400_BAD_REQUEST


def generate_board(*, goals: list[str], rows: int, cols: int, board_type: str, seed: str) -> list[str]:
    """Turn a submitted goal list into a flat, row-major board of rows*cols goals.

    Reimplements bingosync's generator behavior in pure Python - no more
    shelling out to `node` to eval a per-game JS file. Only the two "Custom
    (Advanced)" modes are supported (see project decision to not port
    bingosync's built-in per-game goal-list catalog).
    """
    size = rows * cols

    cleaned = [goal.strip() for goal in goals]
    if any(not goal for goal in cleaned):
        raise InvalidBoardError("Goals cannot be blank.")

    if board_type == BoardType.FIXED:
        if len(cleaned) != size:
            raise InvalidBoardError(f"A fixed board needs exactly {size} goals (got {len(cleaned)}).")
        return cleaned

    if board_type == BoardType.RANDOMIZED:
        if len(cleaned) < size:
            raise InvalidBoardError(
                f"A randomized board needs at least {size} goals (got {len(cleaned)})."
            )
        rng = random.Random(seed)
        return rng.sample(cleaned, size)

    raise InvalidBoardError(f"Unknown board type: {board_type!r}")
