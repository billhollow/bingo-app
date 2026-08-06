import json
from urllib.parse import quote

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from config.asgi import application
from rooms.services import create_room, send_chat_message


def make_goals(n):
    return [f"goal {i}" for i in range(n)]


class RoomConsumerTests(TransactionTestCase):
    async def test_invalid_token_is_rejected(self):
        communicator = WebsocketCommunicator(
            application, "/ws/rooms/00000000-0000-0000-0000-000000000000/?token=garbage"
        )
        connected, _close_code = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_connect_then_receive_broadcast_chat_event(self):
        room, session = await database_sync_to_async(create_room)(
            name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )

        communicator = WebsocketCommunicator(application, f"/ws/rooms/{room.id}/?token={session.token}")
        connected, _close_code = await communicator.connect()
        self.assertTrue(connected)

        # connecting itself records+broadcasts a "connection" event first
        first_message = json.loads(await communicator.receive_from(timeout=1))
        self.assertEqual(first_message["type"], "connection")
        self.assertTrue(first_message["payload"]["connected"])

        event = await database_sync_to_async(send_chat_message)(room=room, player=session.player, text="hi")
        from rooms.realtime import broadcast_event

        await database_sync_to_async(broadcast_event)(event)

        second_message = json.loads(await communicator.receive_from(timeout=1))
        self.assertEqual(second_message["type"], "chat")
        self.assertEqual(second_message["payload"]["text"], "hi")

        await communicator.disconnect()

    async def test_connect_with_url_encoded_token(self):
        # Real clients percent-encode the token (it contains ':' separators
        # from django.core.signing) via encodeURIComponent - this caught a
        # real bug where the consumer used the still-encoded value as-is.
        room, session = await database_sync_to_async(create_room)(
            name="Room", passphrase="hunter2", creator_name="Alice", goals=make_goals(25)
        )
        self.assertIn(":", session.token)

        encoded_token = quote(session.token, safe="")
        communicator = WebsocketCommunicator(
            application, f"/ws/rooms/{room.id}/?token={encoded_token}"
        )
        connected, _close_code = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()
