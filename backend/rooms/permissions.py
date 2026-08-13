from rest_framework.permissions import BasePermission


class IsRoomMember(BasePermission):
    """Require the authenticated player to belong to the room in the URL.

    Being authenticated (a valid token) isn't enough on its own - a token
    for room A shouldn't let you act in room B.
    """

    message = "You must join this room before doing that."

    def has_permission(self, request, view):
        player = request.user
        room_id = view.kwargs.get("room_id")
        if not player or not getattr(player, "is_authenticated", False):
            return False
        return player.room_id == room_id
