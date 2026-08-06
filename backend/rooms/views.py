from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rooms.board_generator import InvalidBoardError
from rooms.colors import color_from_name
from rooms.models import Room, Square
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
    LockoutViolationError,
    WrongPassphraseError,
    change_player_color,
    create_room,
    join_room,
    mark_square,
    reveal_card,
    send_chat_message,
    start_new_game,
)


def _session_response(room, session, status_code=status.HTTP_201_CREATED):
    return Response(
        {
            "room": RoomSerializer(room).data,
            "player": PlayerSerializer(session.player).data,
            "token": session.token,
        },
        status=status_code,
    )


class RoomCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            room, session = create_room(**serializer.validated_data)
        except InvalidBoardError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return _session_response(room, session)


class RoomJoinView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        serializer = RoomJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            session = join_room(room=room, **serializer.validated_data)
        except WrongPassphraseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return _session_response(room, session)


class RoomBoardView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        game = room.current_game
        return Response(SquareSerializer(game.squares.all(), many=True).data)


class RoomSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        return Response({"room": RoomSerializer(room).data, "game": GameSerializer(room.current_game).data})


class NewCardView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        serializer = NewCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            game, event = start_new_game(room=room, player=request.user, **serializer.validated_data)
        except InvalidBoardError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        broadcast_event(event)
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)


class RoomPlayersView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        return Response(PlayerSerializer(room.players.all(), many=True).data)


class RoomFeedView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        events = room.events.select_related("player").all()
        return Response(EventSerializer(events, many=True).data)


class MarkSquareView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        serializer = MarkSquareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        game = room.current_game
        try:
            event = mark_square(
                game=game,
                player=request.user,
                row=data["row"],
                col=data["col"],
                color=color_from_name(data["color"]),
                remove=data["remove"],
            )
        except Square.DoesNotExist as exc:
            raise NotFound("No such square.") from exc
        except LockoutViolationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        broadcast_event(event)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class ChangeColorView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def post(self, request, room_id):
        serializer = ChangeColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = change_player_color(player=request.user, color=color_from_name(serializer.validated_data["color"]))
        broadcast_event(event)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = send_chat_message(room=room, player=request.user, text=serializer.validated_data["text"])
        broadcast_event(event)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class RevealCardView(APIView):
    permission_classes = [IsAuthenticated, IsRoomMember]

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        event = reveal_card(room=room, player=request.user)
        broadcast_event(event)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)
