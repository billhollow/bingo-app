from django.contrib import admin

from rooms.models import Event, Game, Player, Room, Square


class SquareInline(admin.TabularInline):
    model = Square
    extra = 0


class GameInline(admin.TabularInline):
    model = Game
    extra = 0
    show_change_link = True
    fields = ("board_type", "lockout_mode", "rows", "cols", "seed", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "hide_card", "created_at")
    search_fields = ("name",)
    inlines = [GameInline]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("room", "board_type", "lockout_mode", "rows", "cols", "created_at")
    list_filter = ("board_type", "lockout_mode")
    inlines = [SquareInline]


@admin.register(Square)
class SquareAdmin(admin.ModelAdmin):
    list_display = ("game", "row", "col", "goal", "colors")
    list_filter = ("game__room",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "room", "is_spectator", "color_value", "created_at")
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("type", "room", "player", "created_at")
    list_filter = ("type",)
