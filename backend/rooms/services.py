from dataclasses import dataclass

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from rooms.board_generator import generate_board
from rooms.choices import BoardType, LockoutMode
from rooms.colors import Color
from rooms.models import Event, Game, Player, Room, Square
from rooms.tokens import issue_player_token

# Domain errors subclass APIException so they carry their own HTTP status
# (see the note in board_generator.py) - views never translate exceptions.


class WrongPassphraseError(APIException):
    status_code = status.HTTP_403_FORBIDDEN


class LockoutViolationError(APIException):
    status_code = status.HTTP_409_CONFLICT


class SquareNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND


class NoCurrentGameError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This room has no board yet."


@dataclass(frozen=True)
class PlayerSession:
    player: Player
    token: str


def _build_squares(game: Game, goal_strings: list[str]) -> None:
    squares = []
    for index, goal in enumerate(goal_strings):
        row, col = divmod(index, game.cols)
        squares.append(Square(game=game, row=row, col=col, goal=goal))
    Square.objects.bulk_create(squares)


def _create_game(
    *,
    room: Room,
    goals: list[str],
    board_type: str,
    rows: int,
    cols: int,
    lockout_mode: str,
    seed: str,
) -> Game:
    """Build a room's board. Shared by create_room and start_new_game.

    Raises InvalidBoardError (from generate_board) if `goals` doesn't fit
    board_type/rows/cols; callers are transactional, so nothing is written.
    """
    goal_strings = generate_board(goals=goals, rows=rows, cols=cols, board_type=board_type, seed=seed)
    game = Game.objects.create(
        room=room,
        rows=rows,
        cols=cols,
        board_type=board_type,
        lockout_mode=lockout_mode,
        seed=seed,
    )
    _build_squares(game, goal_strings)
    return game


def emit_event(*, room: Room, player: Player, event_type: str, payload: dict) -> Event:
    return Event.objects.create(
        room=room,
        player=player,
        type=event_type,
        player_color=int(player.color),
        payload=payload,
    )


@transaction.atomic
def create_room(
    *,
    name: str,
    passphrase: str,
    creator_name: str,
    goals: list[str],
    board_type: str = BoardType.FIXED,
    rows: int = 5,
    cols: int = 5,
    lockout_mode: str = LockoutMode.NON_LOCKOUT,
    seed: str = "",
    hide_card: bool = False,
    is_spectator: bool = False,
) -> tuple[Room, PlayerSession]:
    """Create a room, its first game/board, and the creator's player+token.

    Raises InvalidBoardError if `goals` doesn't fit board_type/rows/cols; the
    whole transaction rolls back in that case.
    """
    room = Room(name=name, hide_card=hide_card)
    room.set_passphrase(passphrase)
    room.save()

    _create_game(
        room=room,
        goals=goals,
        board_type=board_type,
        rows=rows,
        cols=cols,
        lockout_mode=lockout_mode,
        seed=seed,
    )

    creator = Player.objects.create(room=room, name=creator_name, is_spectator=is_spectator)
    session = PlayerSession(player=creator, token=issue_player_token(creator))
    return room, session


@transaction.atomic
def join_room(*, room: Room, passphrase: str, player_name: str, is_spectator: bool = False) -> PlayerSession:
    if not room.check_passphrase(passphrase):
        raise WrongPassphraseError("Incorrect passphrase.")

    player = Player.objects.create(room=room, name=player_name, is_spectator=is_spectator)
    return PlayerSession(player=player, token=issue_player_token(player))


@transaction.atomic
def start_new_game(
    *,
    room: Room,
    player: Player,
    goals: list[str],
    board_type: str = BoardType.FIXED,
    rows: int = 5,
    cols: int = 5,
    lockout_mode: str = LockoutMode.NON_LOCKOUT,
    seed: str = "",
    hide_card: bool = False,
) -> tuple[Game, Event]:
    """Generate a new board for a room (bingosync's "new card" action)."""
    game = _create_game(
        room=room,
        goals=goals,
        board_type=board_type,
        rows=rows,
        cols=cols,
        lockout_mode=lockout_mode,
        seed=seed,
    )

    if hide_card != room.hide_card:
        room.hide_card = hide_card
        room.save(update_fields=["hide_card"])

    event = emit_event(
        room=room,
        player=player,
        event_type=Event.Type.NEW_CARD,
        payload={"game_id": game.id, "seed": seed, "hide_card": hide_card},
    )
    return game, event


@transaction.atomic
def mark_square(*, game: Game, player: Player, row: int, col: int, color: Color, remove: bool) -> Event:
    """Mark or clear a square, enforcing lockout-mode rules.

    In lockout mode, a square can only ever hold one color at a time: you
    can't claim an already-claimed square, and you can't clear a claim that
    isn't yours. Non-lockout mode allows any player to freely add/remove
    their own color regardless of what's already there.
    """
    try:
        square = Square.objects.select_for_update().get(game=game, row=row, col=col)
    except Square.DoesNotExist:
        raise SquareNotFoundError(f"No square at row {row}, column {col}.") from None

    if game.lockout_mode == LockoutMode.LOCKOUT:
        if not remove and square.color != Color.BLANK:
            raise LockoutViolationError("This square is already claimed.")
        if remove and square.color != color:
            raise LockoutViolationError("You can only clear your own claim.")

    if remove:
        square.remove_color(color)
    else:
        square.add_color(color)
    square.save(update_fields=["colors"])

    return emit_event(
        room=game.room,
        player=player,
        event_type=Event.Type.GOAL,
        payload={
            "row": row,
            "col": col,
            "goal": square.goal,
            "colors": square.color.names,
            "color": color.name.lower(),
            "remove": remove,
        },
    )


@transaction.atomic
def change_player_color(*, player: Player, color: Color) -> Event:
    player.color = color
    player.save(update_fields=["color_value"])
    return emit_event(
        room=player.room,
        player=player,
        event_type=Event.Type.COLOR,
        payload={"color": color.name.lower()},
    )


def send_chat_message(*, room: Room, player: Player, text: str) -> Event:
    return emit_event(room=room, player=player, event_type=Event.Type.CHAT, payload={"text": text})


def reveal_card(*, room: Room, player: Player) -> Event:
    return emit_event(room=room, player=player, event_type=Event.Type.REVEALED, payload={})


def mark_connection(*, player: Player, connected: bool) -> Event:
    return emit_event(
        room=player.room,
        player=player,
        event_type=Event.Type.CONNECTION,
        payload={"connected": connected},
    )
