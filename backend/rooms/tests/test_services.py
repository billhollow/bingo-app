from django.test import TestCase

from rooms.board_generator import InvalidBoardError
from rooms.choices import BoardType
from rooms.colors import Color
from rooms.models import Room, Square
from rooms.services import WrongPassphraseError, create_room, join_room
from rooms.tokens import resolve_player_token


def make_goals(n):
    return [f"goal {i}" for i in range(n)]


class CreateRoomTests(TestCase):
    def test_creates_room_game_squares_and_creator(self):
        room, session = create_room(
            name="Speedrun Bingo", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )

        self.assertEqual(Room.objects.count(), 1)
        game = room.current_game
        self.assertEqual(game.rows, 5)
        self.assertEqual(game.cols, 5)
        self.assertEqual(Square.objects.filter(game=game).count(), 25)
        self.assertEqual(session.player.name, "Alice")
        self.assertEqual(room.players.count(), 1)

    def test_passphrase_is_hashed_not_stored_raw(self):
        room, _session = create_room(
            name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )
        self.assertNotEqual(room.passphrase_hash, "hunter2")
        self.assertTrue(room.check_passphrase("hunter2"))
        self.assertFalse(room.check_passphrase("wrong"))

    def test_token_resolves_to_creator(self):
        _room, session = create_room(
            name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )
        resolved = resolve_player_token(session.token)
        self.assertEqual(resolved.id, session.player.id)

    def test_invalid_board_rolls_back_room_creation(self):
        with self.assertRaises(InvalidBoardError):
            create_room(name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(10))
        self.assertEqual(Room.objects.count(), 0)

    def test_configurable_board_size(self):
        room, _session = create_room(
            name="Room",
            passphrase="hunter2",
            creator_name="Alice",
            goals=make_goals(12),
            rows=3,
            cols=4,
        )
        game = room.current_game
        self.assertEqual(Square.objects.filter(game=game).count(), 12)
        self.assertEqual(
            {(square.row, square.col) for square in Square.objects.filter(game=game)},
            {(row, col) for row in range(3) for col in range(4)},
        )

    def test_randomized_board_type(self):
        room, _session = create_room(
            name="Room",
            passphrase="hunter2",
            creator_name="Alice",
            goals=make_goals(40),
            board_type=BoardType.RANDOMIZED,
            seed="42",
        )
        game = room.current_game
        self.assertEqual(game.board_type, BoardType.RANDOMIZED)
        self.assertEqual(Square.objects.filter(game=game).count(), 25)


class JoinRoomTests(TestCase):
    def setUp(self):
        self.room, self.creator_session = create_room(
            name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )

    def test_correct_passphrase_creates_player(self):
        session = join_room(room=self.room, passphrase="hunter2", player_name="Bob")
        self.assertEqual(session.player.name, "Bob")
        self.assertEqual(self.room.players.count(), 2)

    def test_wrong_passphrase_rejected(self):
        with self.assertRaises(WrongPassphraseError):
            join_room(room=self.room, passphrase="wrong", player_name="Bob")
        self.assertEqual(self.room.players.count(), 1)

    def test_spectator_flag(self):
        session = join_room(
            room=self.room, passphrase="hunter2", player_name="Casey", is_spectator=True
        )
        self.assertTrue(session.player.is_spectator)
        self.assertEqual(session.player.color, Color.BLANK)
