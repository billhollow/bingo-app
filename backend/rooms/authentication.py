from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from rooms.tokens import InvalidTokenError, resolve_player_token


class PlayerTokenAuthentication(BaseAuthentication):
    """Authenticates a request via `Authorization: Bearer <player token>`.

    There's no Django auth User in this app - request.user ends up being the
    Player itself (see Player.is_authenticated in models.py), and
    request.auth is the raw token string.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        prefix = self.keyword + " "
        if not header.startswith(prefix):
            return None

        token = header[len(prefix):]
        try:
            player = resolve_player_token(token)
        except InvalidTokenError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        return (player, token)

    def authenticate_header(self, request):
        # Presence of this (any truthy string) is what makes DRF respond
        # 401 Unauthorized for missing/bad credentials instead of 403.
        return self.keyword
