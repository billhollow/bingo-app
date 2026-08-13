from django.urls import include, path

from rooms import views

# Everything room-scoped nests under one prefix so `rooms/<uuid:room_id>/`
# is written once. Full paths are /api/rooms/<id>/<name>/ - config/urls.py
# supplies the `api/`.
urlpatterns = [
    path("rooms/", views.RoomCreateView.as_view(), name="room-create"),
    path(
        "rooms/<uuid:room_id>/",
        include(
            [
                path("join/", views.RoomJoinView.as_view(), name="room-join"),
                path("board/", views.RoomBoardView.as_view(), name="room-board"),
                path("settings/", views.RoomSettingsView.as_view(), name="room-settings"),
                path("players/", views.RoomPlayersView.as_view(), name="room-players"),
                path("new-card/", views.NewCardView.as_view(), name="room-new-card"),
                path("feed/", views.RoomFeedView.as_view(), name="room-feed"),
                path("goal/", views.MarkSquareView.as_view(), name="room-goal"),
                path("color/", views.ChangeColorView.as_view(), name="room-color"),
                path("chat/", views.ChatMessageView.as_view(), name="room-chat"),
                path("reveal/", views.RevealCardView.as_view(), name="room-reveal"),
            ]
        ),
    ),
]
