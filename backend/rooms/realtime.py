from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rooms.models import Event
from rooms.serializers import EventSerializer


def room_group_name(room_id) -> str:
    return f"room.{room_id}"


def broadcast_event(event: Event) -> None:
    """Push a just-created Event to every websocket connected to its room.

    Sync on purpose: called directly from DRF views (M2/M3), and from the
    Channels consumer's database_sync_to_async-wrapped connect/disconnect
    handlers (M4) - both are sync contexts, so async_to_sync is the right
    bridge in both places rather than duplicating this in two forms.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        room_group_name(event.room_id),
        {"type": "room.event", "event": EventSerializer(event).data},
    )
