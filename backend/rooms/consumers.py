import json
from urllib.parse import unquote

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from rooms.realtime import broadcast_event, room_group_name
from rooms.tokens import InvalidTokenError, resolve_player_token


class RoomConsumer(AsyncWebsocketConsumer):
    """One websocket connection per browser tab, joined to a room's group.

    All game actions go through the REST API (M2/M3); this consumer is
    purely a broadcast receiver plus connect/disconnect tracking. The
    player authenticates via a `?token=` query param, since browsers can't
    set custom headers on a WebSocket handshake.
    """

    async def connect(self):
        room_id = self.scope["url_route"]["kwargs"]["room_id"]
        token = self._token_from_query_string()
        player = await self._authenticate(token)

        if player is None or str(player.room_id) != str(room_id):
            await self.close(code=4401)
            return

        self.player = player
        self.group_name = room_group_name(room_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._mark_connection(connected=True)

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self._mark_connection(connected=False)

    async def receive(self, text_data=None, bytes_data=None):
        # Clients don't send anything meaningful over the socket - every
        # mutation goes through the REST API and is fanned out via room_event.
        pass

    async def room_event(self, message):
        await self.send(text_data=json.dumps(message["event"]))

    def _token_from_query_string(self) -> str | None:
        # ASGI's query_string is the raw, still-percent-encoded bytes -
        # a real client (correctly) encodeURIComponent()s the token, since
        # django's signing tokens contain ':' separators.
        query_string = self.scope["query_string"].decode()
        params = dict(pair.split("=", 1) for pair in query_string.split("&") if "=" in pair)
        token = params.get("token")
        return unquote(token) if token is not None else None

    @database_sync_to_async
    def _authenticate(self, token):
        if not token:
            return None
        try:
            return resolve_player_token(token)
        except InvalidTokenError:
            return None

    @database_sync_to_async
    def _mark_connection(self, connected: bool) -> None:
        from rooms.services import mark_connection

        event = mark_connection(player=self.player, connected=connected)
        broadcast_event(event)
