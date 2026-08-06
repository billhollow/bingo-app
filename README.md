# Bingo App

A clean-room reimplementation of [bingosync](https://bingosync.com) (vendored for
reference under `bingosync/`) using a Vue 3 frontend and a Django REST
Framework backend. Not a refactor of bingosync — the original is used only as
a functional reference for behavior and business rules.

See `docs/BUILD_REPORT.md` for a full narrative of the analysis, architecture
decisions, and milestones behind this implementation, and `docs/COMMANDS.md`
for the exact commands used to set it up from scratch.

## Tech stack

- **Backend**: Django 5.2, Django REST Framework, Django Channels (ASGI, served via Daphne)
- **Frontend**: Vue 3 (Composition API, `<script setup>`), TypeScript, Vite, Pinia, Vue Router
- **Realtime**: Django Channels websockets, one room per channel group
- **Auth**: stateless bearer tokens (a room passphrase + nickname issues a signed player token; no user accounts)
- **Dev database**: SQLite (swap via `DATABASE_URL` for Postgres in production)

## Project structure

```
backend/
  config/          Django project (settings, urls, asgi)
  core/            healthcheck endpoint, websocket routing aggregator
  rooms/           the actual app: models, REST API, Channels consumer
    models.py        Room, Game, Square, Player, Event
    board_generator.py  pure-Python board generation (fixed/randomized)
    services.py       business logic (create_room, join_room, mark_square, ...)
    authentication.py / permissions.py   bearer-token DRF auth
    consumers.py / routing.py / realtime.py   Channels websocket layer
    tests/

frontend/
  src/
    features/home/    create-room form
    features/room/    join form, room view, board grid, chat, players, settings
    stores/           Pinia stores (session, room)
    composables/       useRoomSocket (websocket lifecycle)
    lib/               API client, room-scoped API calls, color helpers
    types/              TypeScript DTOs mirroring the DRF serializers
```

## Running it locally

### Backend

```bash
cd backend
python3 -m venv .venv          # or: pyenv install 3.12.10 && use it
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

The server is ASGI (Channels) from the start, so `runserver` serves both HTTP
and websockets. API root: `http://localhost:8000/api/`, websocket:
`ws://localhost:8000/ws/rooms/<room_id>/?token=<player_token>`.

Run the backend tests:

```bash
python manage.py test rooms
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.development
npm run dev
```

Opens on `http://localhost:5173`, pointed at the backend via
`VITE_API_BASE_URL` in `.env.development`.

```bash
npm run lint     # eslint
npm run build    # type-checks (vue-tsc) then builds
```

## Current status

Feature-parity milestones M0–M8 are complete: room/game/player data model,
full REST API (create/join a room, fetch board/settings/players/feed, mark a
square with lockout-mode rules, change color, chat, reveal, generate a new
card), Django Channels realtime broadcast, and the full Vue UI wired to all
of it. Deliberately **not** ported: bingosync's ~460 built-in per-game goal
list generators — this implementation only supports custom boards (paste
your own goal list, fixed or randomized-from-a-pool). See
`docs/BUILD_REPORT.md` for the reasoning and the full list of scope
decisions.

Board size (`rows` × `cols`) is configurable per game rather than hardcoded
to 5×5, ahead of a planned future "configurable card size" feature.
