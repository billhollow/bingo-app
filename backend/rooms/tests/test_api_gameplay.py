from rest_framework import status
from rest_framework.test import APITestCase


def make_goals(n):
    return [f"goal {i}" for i in range(n)]


class GameplayApiTestsBase(APITestCase):
    lockout_mode = "non_lockout"

    def setUp(self):
        creator = self.client.post(
            "/api/rooms/",
            {
                "name": "Room",
                "passphrase": "hunter2",
                "creator_name": "Alice",
                "goals": make_goals(25),
                "lockout_mode": self.lockout_mode,
            },
            format="json",
        )
        self.room_id = creator.data["room"]["id"]
        self.alice_token = creator.data["token"]

        joiner = self.client.post(
            f"/api/rooms/{self.room_id}/join/",
            {"passphrase": "hunter2", "player_name": "Bob"},
            format="json",
        )
        self.bob_token = joiner.data["token"]

    def as_alice(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

    def as_bob(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")


class LockoutMarkSquareApiTests(GameplayApiTestsBase):
    lockout_mode = "lockout"

    def test_mark_square(self):
        self.as_alice()
        response = self.client.post(
            f"/api/rooms/{self.room_id}/goal/", {"row": 0, "col": 0, "color": "red"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["payload"]["colors"], ["red"])

    def test_second_player_blocked_from_claimed_square(self):
        self.as_alice()
        self.client.post(f"/api/rooms/{self.room_id}/goal/", {"row": 0, "col": 0, "color": "red"}, format="json")

        self.as_bob()
        response = self.client.post(
            f"/api/rooms/{self.room_id}/goal/", {"row": 0, "col": 0, "color": "blue"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cannot_clear_someone_elses_claim(self):
        self.as_alice()
        self.client.post(f"/api/rooms/{self.room_id}/goal/", {"row": 0, "col": 0, "color": "red"}, format="json")

        self.as_bob()
        response = self.client.post(
            f"/api/rooms/{self.room_id}/goal/",
            {"row": 0, "col": 0, "color": "blue", "remove": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_owner_can_clear_their_own_claim(self):
        self.as_alice()
        self.client.post(f"/api/rooms/{self.room_id}/goal/", {"row": 0, "col": 0, "color": "red"}, format="json")
        response = self.client.post(
            f"/api/rooms/{self.room_id}/goal/",
            {"row": 0, "col": 0, "color": "red", "remove": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["payload"]["colors"], [])


class NonLockoutMarkSquareApiTests(GameplayApiTestsBase):
    lockout_mode = "non_lockout"

    def test_two_players_can_share_a_square(self):
        self.as_alice()
        self.client.post(f"/api/rooms/{self.room_id}/goal/", {"row": 1, "col": 1, "color": "red"}, format="json")

        self.as_bob()
        response = self.client.post(
            f"/api/rooms/{self.room_id}/goal/", {"row": 1, "col": 1, "color": "blue"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data["payload"]["colors"], ["red", "blue"])


class ColorChatRevealFeedApiTests(GameplayApiTestsBase):
    def test_change_color(self):
        self.as_alice()
        response = self.client.post(f"/api/rooms/{self.room_id}/color/", {"color": "blue"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["payload"]["color"], "blue")

    def test_chat_message(self):
        self.as_alice()
        response = self.client.post(f"/api/rooms/{self.room_id}/chat/", {"text": "gl hf"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["payload"]["text"], "gl hf")

    def test_reveal_card(self):
        self.as_alice()
        response = self.client.post(f"/api/rooms/{self.room_id}/reveal/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"], "revealed")

    def test_feed_includes_events_in_order(self):
        self.as_alice()
        self.client.post(f"/api/rooms/{self.room_id}/chat/", {"text": "first"}, format="json")
        self.client.post(f"/api/rooms/{self.room_id}/chat/", {"text": "second"}, format="json")

        response = self.client.get(f"/api/rooms/{self.room_id}/feed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        texts = [event["payload"].get("text") for event in response.data if event["type"] == "chat"]
        self.assertEqual(texts, ["first", "second"])
