from django.test import TestCase

from rooms.models import Player, Room
from rooms.tokens import InvalidTokenError, issue_player_token, resolve_player_token


class PlayerTokenTests(TestCase):
    def setUp(self):
        room = Room(name="Test Room")
        room.set_passphrase("hunter2")
        room.save()
        self.player = Player.objects.create(room=room, name="Alice")

    def test_round_trip(self):
        token = issue_player_token(self.player)
        resolved = resolve_player_token(token)
        self.assertEqual(resolved.id, self.player.id)

    def test_tampered_token_rejected(self):
        token = issue_player_token(self.player)
        last_char = token[-1]
        tampered = token[:-1] + ("a" if last_char != "a" else "b")
        with self.assertRaises(InvalidTokenError):
            resolve_player_token(tampered)

    def test_unknown_player_rejected(self):
        token = issue_player_token(self.player)
        self.player.delete()
        with self.assertRaises(InvalidTokenError):
            resolve_player_token(token)
