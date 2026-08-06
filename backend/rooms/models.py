import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from rooms.choices import BoardType, LockoutMode
from rooms.colors import PLAYER_COLOR_CHOICES, Color


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    passphrase_hash = models.CharField(max_length=255)
    hide_card = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def set_passphrase(self, raw_passphrase: str) -> None:
        self.passphrase_hash = make_password(raw_passphrase)

    def check_passphrase(self, raw_passphrase: str) -> bool:
        return check_password(raw_passphrase, self.passphrase_hash)

    @property
    def current_game(self) -> "Game | None":
        return self.games.order_by("-created_at").first()


class Game(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="games")
    # Board size lives here (not on Room) since, like lockout_mode, it's a
    # per-card setting rather than a fixed room property - this is the hook
    # for the future "configurable card size" feature.
    rows = models.PositiveSmallIntegerField(default=5)
    cols = models.PositiveSmallIntegerField(default=5)
    board_type = models.CharField(max_length=20, choices=BoardType.choices)
    lockout_mode = models.CharField(
        max_length=20, choices=LockoutMode.choices, default=LockoutMode.NON_LOCKOUT
    )
    seed = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.room.name}: {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def size(self) -> int:
        return self.rows * self.cols


class Square(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="squares")
    # 0-indexed, unlike bingosync's 1-indexed flat "slot" - pairs naturally
    # with a rows x cols grid instead of a hardcoded 1..25 range.
    row = models.PositiveSmallIntegerField()
    col = models.PositiveSmallIntegerField()
    goal = models.CharField(max_length=255)
    # Bitmask of Color flags. Plural name (vs. the `color` property below)
    # mirrors bingosync's color_value/color split.
    colors = models.PositiveSmallIntegerField(default=Color.BLANK.value)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "row", "col"], name="unique_square_position"),
        ]
        ordering = ["row", "col"]

    def __str__(self):
        return f"({self.row}, {self.col}): {self.goal}"

    @property
    def color(self) -> Color:
        return Color(self.colors)

    @color.setter
    def color(self, value: Color) -> None:
        self.colors = int(value)

    def add_color(self, color: Color) -> None:
        self.color = self.color | color

    def remove_color(self, color: Color) -> None:
        self.color = self.color & ~color


class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=50)
    color_value = models.PositiveSmallIntegerField(choices=PLAYER_COLOR_CHOICES, default=Color.RED.value)
    is_spectator = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    @property
    def color(self) -> Color:
        return Color.BLANK if self.is_spectator else Color(self.color_value)

    @color.setter
    def color(self, value: Color) -> None:
        self.color_value = int(value)

    # Duck-typed to satisfy DRF's IsAuthenticated permission, which just
    # checks `request.user.is_authenticated`. There's no Django auth User
    # here - a resolved Player token *is* the authenticated principal.
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_connected(self) -> bool:
        """No connection event yet -> assume connected (a player is
        "innocent until proven disconnected", e.g. right after joining over
        HTTP but before their websocket has opened)."""
        last_event = self.events.filter(type=Event.Type.CONNECTION).order_by("-created_at").first()
        return last_event is None or bool(last_event.payload.get("connected", True))


class Event(models.Model):
    """A single append-only entry in a room's activity feed.

    One table with a `type` + JSON `payload`, replacing bingosync's six
    separate event subclasses (ChatEvent, GoalEvent, ColorEvent, ...) -
    same event-sourcing value, far less schema duplication.
    """

    class Type(models.TextChoices):
        CHAT = "chat", "Chat"
        GOAL = "goal", "Goal"
        COLOR = "color", "Color"
        REVEALED = "revealed", "Revealed"
        CONNECTION = "connection", "Connection"
        NEW_CARD = "new_card", "New Card"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="events")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=20, choices=Type.choices)
    # The player's color *at the time of the event*, since it may change
    # later and past chat/activity entries should keep their original color.
    player_color = models.PositiveSmallIntegerField(choices=PLAYER_COLOR_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.type} by {self.player.name} at {self.created_at:%Y-%m-%d %H:%M:%S}"

    @property
    def player_color_enum(self) -> Color:
        return Color(self.player_color)
