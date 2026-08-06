from django.urls import path

from rooms import views

urlpatterns = [
    path("rooms/", views.RoomCreateView.as_view(), name="room-create"),
    path("rooms/<uuid:room_id>/join/", views.RoomJoinView.as_view(), name="room-join"),
    path("rooms/<uuid:room_id>/board/", views.RoomBoardView.as_view(), name="room-board"),
    path("rooms/<uuid:room_id>/settings/", views.RoomSettingsView.as_view(), name="room-settings"),
    path("rooms/<uuid:room_id>/players/", views.RoomPlayersView.as_view(), name="room-players"),
    path("rooms/<uuid:room_id>/new-card/", views.NewCardView.as_view(), name="room-new-card"),
    path("rooms/<uuid:room_id>/feed/", views.RoomFeedView.as_view(), name="room-feed"),
    path("rooms/<uuid:room_id>/goal/", views.MarkSquareView.as_view(), name="room-goal"),
    path("rooms/<uuid:room_id>/color/", views.ChangeColorView.as_view(), name="room-color"),
    path("rooms/<uuid:room_id>/chat/", views.ChatMessageView.as_view(), name="room-chat"),
    path("rooms/<uuid:room_id>/reveal/", views.RevealCardView.as_view(), name="room-reveal"),
]
