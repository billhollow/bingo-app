#!/bin/sh
set -e

python manage.py migrate --noinput

# One process, deliberately: CHANNEL_LAYERS uses InMemoryChannelLayer, so a second
# worker would broadcast into its own private layer and rooms would desync.
# exec so Daphne is PID 1 and gets the SIGTERM from `docker compose down`.
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
