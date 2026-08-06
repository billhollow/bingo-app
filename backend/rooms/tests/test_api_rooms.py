from rest_framework import status
from rest_framework.test import APITestCase

from rooms.models import Room


def make_goals(n):
    return [f"goal {i}" for i in range(n)]


class RoomCreateApiTests(APITestCase):
    def test_create_room_returns_room_player_and_token(self):
        response = self.client.post(
            "/api/rooms/",
            {
                "name": "Speedrun Bingo",
                "passphrase": "hunter2",
                "creator_name": "Alice",
                "goals": make_goals(25),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Room.objects.count(), 1)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["player"]["name"], "Alice")

    def test_invalid_board_returns_400_and_creates_nothing(self):
        response = self.client.post(
            "/api/rooms/",
            {"name": "Room", "passphrase": "hunter2", "creator_name": "Alice", "goals": make_goals(10)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Room.objects.count(), 0)


class RoomJoinApiTests(APITestCase):
    def setUp(self):
        response = self.client.post(
            "/api/rooms/",
            {"name": "Room", "passphrase": "hunter2", "creator_name": "Alice", "goals": make_goals(25)},
            format="json",
        )
        self.room_id = response.data["room"]["id"]

    def test_join_with_correct_passphrase(self):
        response = self.client.post(
            f"/api/rooms/{self.room_id}/join/",
            {"passphrase": "hunter2", "player_name": "Bob"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["player"]["name"], "Bob")

    def test_join_with_wrong_passphrase(self):
        response = self.client.post(
            f"/api/rooms/{self.room_id}/join/",
            {"passphrase": "wrong", "player_name": "Bob"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuthenticatedRoomApiTests(APITestCase):
    def setUp(self):
        response = self.client.post(
            "/api/rooms/",
            {"name": "Room", "passphrase": "hunter2", "creator_name": "Alice", "goals": make_goals(25)},
            format="json",
        )
        self.room_id = response.data["room"]["id"]
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_board_returns_25_squares(self):
        response = self.client.get(f"/api/rooms/{self.room_id}/board/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 25)

    def test_settings_returns_room_and_game(self):
        response = self.client.get(f"/api/rooms/{self.room_id}/settings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["game"]["rows"], 5)

    def test_players_returns_creator_as_connected_by_default(self):
        response = self.client.get(f"/api/rooms/{self.room_id}/players/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Alice")
        self.assertTrue(response.data[0]["connected"])

    def test_board_requires_auth(self):
        self.client.credentials()
        response = self.client.get(f"/api/rooms/{self.room_id}/board/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_act_in_another_room(self):
        other = self.client.post(
            "/api/rooms/",
            {"name": "Other", "passphrase": "x", "creator_name": "Zed", "goals": make_goals(25)},
            format="json",
        )
        other_room_id = other.data["room"]["id"]
        # still authenticated as Alice, creator of the *first* room
        response = self.client.get(f"/api/rooms/{other_room_id}/board/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_card_replaces_board_with_a_different_size(self):
        response = self.client.post(
            f"/api/rooms/{self.room_id}/new-card/",
            {"goals": make_goals(9), "rows": 3, "cols": 3},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        board = self.client.get(f"/api/rooms/{self.room_id}/board/")
        self.assertEqual(len(board.data), 9)
