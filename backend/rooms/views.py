from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rooms.models import Event, Game, Room
from rooms.permissions import IsRoomMember
from rooms.realtime import broadcast_event
from rooms.serializers import (
    ChangeColorSerializer,
    ChatMessageSerializer,
    EventSerializer,
    GameSerializer,
    MarkSquareSerializer,
    NewCardSerializer,
    PlayerSerializer,
    RoomCreateSerializer,
    RoomJoinSerializer,
    RoomSerializer,
    SquareSerializer,
)
from rooms.services import (
    NoCurrentGameError,
    change_player_color,
    create_room,
    join_room,
    mark_square,
    reveal_card,
    send_chat_message,
    start_new_game,
)


def _validated(serializer_class, request) -> dict:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _session_response(room, session, status_code=status.HTTP_201_CREATED):
    return Response(
        {
            "room": RoomSerializer(room).data,
            "player": PlayerSerializer(session.player).data,
            "token": session.token,
        },
        status=status_code,
    )


def _event_response(event: Event) -> Response:
    """Broadcast a state change, then echo it to the actor over HTTP.

    The actor's own socket is in the channel group too, so the frontend
    ignores this body and waits for the broadcast - but returning the event
    keeps every mutating endpoint's response shape identical.
    """
    broadcast_event(event)
    return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


def connection_map(players) -> dict:
    """Latest connection state per player, in one query instead of N.

    Player.is_connected hits the database per player, and PlayerSerializer is
    nested inside EventSerializer - so rendering a feed without this would
    cost one query per event. Absent any connection event a player counts as
    connected, matching Player.is_connected.
    """
    disconnected = set()
    seen = set()
    events = (
        Event.objects.filter(player__in=players, type=Event.Type.CONNECTION)
        .order_by("player_id", "-created_at")
        .values_list("player_id", "payload")
    )
    for player_id, payload in events:
        if player_id in seen:
            continue
        seen.add(player_id)
        if not payload.get("connected", True):
            disconnected.add(player_id)
    return {player.id: player.id not in disconnected for player in players}


class RoomMemberView(APIView):
    """Base for every view under /api/rooms/<room_id>/.

    IsRoomMember has already proved request.user.room_id == room_id, so the
    acting player's own FK *is* the room - looking it up again would be a
    second query for an object we're holding. IsAuthenticated is likewise
    redundant: IsRoomMember rejects anonymous requests itself, and DRF still
    turns that into a 401 (not 403) when no authenticator succeeded.
    """

    permission_classes = [IsRoomMember]

    @property
    def room(self) -> Room:
        return self.request.user.room

    @property
    def current_game(self) -> Game:
        game = self.room.current_game
        if game is None:
            raise NoCurrentGameError()
        return game


class RoomCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        room, session = create_room(**_validated(RoomCreateSerializer, request))
        return _session_response(room, session)


class RoomJoinView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        session = join_room(room=room, **_validated(RoomJoinSerializer, request))
        return _session_response(room, session)


class RoomBoardView(RoomMemberView):
    def get(self, request, room_id):
        return Response(SquareSerializer(self.current_game.squares.all(), many=True).data)


class RoomSettingsView(RoomMemberView):
    def get(self, request, room_id):
        return Response(
            {
                "room": RoomSerializer(self.room).data,
                "game": GameSerializer(self.current_game).data,
            }
        )


class NewCardView(RoomMemberView):
    def post(self, request, room_id):
        game, event = start_new_game(
            room=self.room,
            player=request.user,
            **_validated(NewCardSerializer, request),
        )
        broadcast_event(event)
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)


class RoomPlayersView(RoomMemberView):
    def get(self, request, room_id):
        players = list(self.room.players.all())
        return Response(
            PlayerSerializer(
                players,
                many=True,
                context={"connection_map": connection_map(players)},
            ).data
        )


class RoomFeedView(RoomMemberView):
    def get(self, request, room_id):
        events = list(self.room.events.select_related("player").all())
        players = {event.player for event in events}
        return Response(
            EventSerializer(
                events,
                many=True,
                context={"connection_map": connection_map(players)},
            ).data
        )


class MarkSquareView(RoomMemberView):
    def post(self, request, room_id):
        event = mark_square(
            game=self.current_game,
            player=request.user,
            **_validated(MarkSquareSerializer, request),
        )
        return _event_response(event)


class ChangeColorView(RoomMemberView):
    def post(self, request, room_id):
        return _event_response(
            change_player_color(player=request.user, **_validated(ChangeColorSerializer, request))
        )


class ChatMessageView(RoomMemberView):
    def post(self, request, room_id):
        return _event_response(
            send_chat_message(room=self.room, player=request.user, **_validated(ChatMessageSerializer, request))
        )


class RevealCardView(RoomMemberView):
    def post(self, request, room_id):
        return _event_response(reveal_card(room=self.room, player=request.user))
