from rest_framework import serializers

from rooms.choices import BoardType, LockoutMode
from rooms.colors import PLAYER_COLOR_NAMES
from rooms.models import Event, Game, Player, Room, Square

MAX_BOARD_DIMENSION = 15


class SquareSerializer(serializers.ModelSerializer):
    colors = serializers.SerializerMethodField()

    class Meta:
        model = Square
        fields = ["row", "col", "goal", "colors"]

    def get_colors(self, square: Square) -> list[str]:
        return square.color.names


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id", "rows", "cols", "board_type", "lockout_mode", "seed", "created_at"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "hide_card", "created_at"]


class PlayerSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()
    connected = serializers.BooleanField(source="is_connected", read_only=True)

    class Meta:
        model = Player
        fields = ["id", "name", "color", "is_spectator", "connected"]

    def get_color(self, player: Player) -> str:
        return player.color.name.lower()


class EventSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    player_color = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ["type", "player", "player_color", "payload", "created_at"]

    def get_player_color(self, event: Event) -> str:
        return event.player_color_enum.name.lower()


# --- request bodies -----------------------------------------------------


class RoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    passphrase = serializers.CharField(write_only=True)
    creator_name = serializers.CharField(max_length=50)
    goals = serializers.ListField(child=serializers.CharField(allow_blank=False), min_length=1)
    board_type = serializers.ChoiceField(choices=BoardType.choices, default=BoardType.FIXED)
    rows = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    cols = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    lockout_mode = serializers.ChoiceField(choices=LockoutMode.choices, default=LockoutMode.NON_LOCKOUT)
    seed = serializers.CharField(required=False, allow_blank=True, default="")
    hide_card = serializers.BooleanField(default=False)
    is_spectator = serializers.BooleanField(default=False)


class RoomJoinSerializer(serializers.Serializer):
    passphrase = serializers.CharField(write_only=True)
    player_name = serializers.CharField(max_length=50)
    is_spectator = serializers.BooleanField(default=False)


class NewCardSerializer(serializers.Serializer):
    goals = serializers.ListField(child=serializers.CharField(allow_blank=False), min_length=1)
    board_type = serializers.ChoiceField(choices=BoardType.choices, default=BoardType.FIXED)
    rows = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    cols = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    lockout_mode = serializers.ChoiceField(choices=LockoutMode.choices, default=LockoutMode.NON_LOCKOUT)
    seed = serializers.CharField(required=False, allow_blank=True, default="")
    hide_card = serializers.BooleanField(default=False)


class MarkSquareSerializer(serializers.Serializer):
    row = serializers.IntegerField(min_value=0)
    col = serializers.IntegerField(min_value=0)
    color = serializers.ChoiceField(choices=PLAYER_COLOR_NAMES)
    remove = serializers.BooleanField(default=False)


class ChangeColorSerializer(serializers.Serializer):
    color = serializers.ChoiceField(choices=PLAYER_COLOR_NAMES)


class ChatMessageSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000, allow_blank=False)
