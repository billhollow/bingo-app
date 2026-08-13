from django.core import signing

from rooms.models import Player

# Distinct salt so these tokens can't be swapped with other signed values
# elsewhere in the app.
TOKEN_SALT = "rooms.player-token"


class InvalidTokenError(Exception):
    pass


def issue_player_token(player: Player) -> str:
    """Return an opaque bearer token identifying this player.

    Stateless: the player id is embedded and cryptographically signed
    (via SECRET_KEY), so resolving a token needs no separate token table -
    just a signature check plus a Player lookup by id.
    """
    return signing.dumps({"player_id": str(player.id)}, salt=TOKEN_SALT)


def resolve_player_token(token: str) -> Player:
    try:
        data = signing.loads(token, salt=TOKEN_SALT)
    except signing.BadSignature as exc:
        raise InvalidTokenError("Invalid or tampered token.") from exc

    try:
        # select_related("room"): every room-scoped view reads request.user.room
        # (for the permission check and as the room itself), so fetching it here
        # keeps that a single query instead of a lazy second one.
        return Player.objects.select_related("room").get(id=data["player_id"])
    except (Player.DoesNotExist, KeyError, ValueError) as exc:
        raise InvalidTokenError("Token does not match any player.") from exc
