from rest_framework import serializers

from rooms.choices import BoardType, LockoutMode
from rooms.colors import PLAYER_COLOR_NAMES, Color, color_from_name
from rooms.models import Event, Game, Player, Room, Square

MAX_BOARD_DIMENSION = 15


# The wire format is always colour *names*, never the bitmask integer. These
# two fields are the single place that translation happens, in both directions.


class ColorNameField(serializers.ChoiceField):
    """A single player colour: `Color` <-> lowercase name."""

    def __init__(self, **kwargs):
        super().__init__(choices=PLAYER_COLOR_NAMES, **kwargs)

    def to_representation(self, value: Color) -> str:
        return value.name.lower()

    def to_internal_value(self, data) -> Color:
        return color_from_name(super().to_internal_value(data))


class ColorNamesField(serializers.Field):
    """A square's composite bitmask -> the list of colours marking it."""

    def to_representation(self, value: Color) -> list[str]:
        return value.names


class SquareSerializer(serializers.ModelSerializer):
    colors = ColorNamesField(source="color", read_only=True)

    class Meta:
        model = Square
        fields = ["row", "col", "goal", "colors"]


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id", "rows", "cols", "board_type", "lockout_mode", "seed", "created_at"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "hide_card", "created_at"]


class PlayerSerializer(serializers.ModelSerializer):
    color = ColorNameField(read_only=True)
    connected = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ["id", "name", "color", "is_spectator", "connected"]

    def get_connected(self, player: Player) -> bool:
        """Prefer a bulk-computed map from the view over Player.is_connected.

        is_connected costs one query per player, and this serializer is nested
        inside EventSerializer - so serializing a room's feed without the map
        would be one query per event. See views.connection_map().
        """
        connection_map = self.context.get("connection_map")
        if connection_map is None:
            return player.is_connected
        return connection_map.get(player.id, True)


class EventSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    player_color = ColorNameField(source="player_color_enum", read_only=True)

    class Meta:
        model = Event
        fields = ["type", "player", "player_color", "payload", "created_at"]


# --- request bodies -----------------------------------------------------


class NewCardSerializer(serializers.Serializer):
    """The board options every "make me a board" request shares."""

    goals = serializers.ListField(child=serializers.CharField(allow_blank=False), min_length=1)
    board_type = serializers.ChoiceField(choices=BoardType.choices, default=BoardType.FIXED)
    rows = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    cols = serializers.IntegerField(min_value=1, max_value=MAX_BOARD_DIMENSION, default=5)
    lockout_mode = serializers.ChoiceField(choices=LockoutMode.choices, default=LockoutMode.NON_LOCKOUT)
    seed = serializers.CharField(required=False, allow_blank=True, default="")
    hide_card = serializers.BooleanField(default=False)


class RoomCreateSerializer(NewCardSerializer):
    """Creating a room is a new card plus the room and its first player."""

    name = serializers.CharField(max_length=255)
    passphrase = serializers.CharField(write_only=True)
    creator_name = serializers.CharField(max_length=50)
    is_spectator = serializers.BooleanField(default=False)


class RoomJoinSerializer(serializers.Serializer):
    passphrase = serializers.CharField(write_only=True)
    player_name = serializers.CharField(max_length=50)
    is_spectator = serializers.BooleanField(default=False)


class MarkSquareSerializer(serializers.Serializer):
    row = serializers.IntegerField(min_value=0)
    col = serializers.IntegerField(min_value=0)
    color = ColorNameField()
    remove = serializers.BooleanField(default=False)


class ChangeColorSerializer(serializers.Serializer):
    color = ColorNameField()


class ChatMessageSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000, allow_blank=False)
