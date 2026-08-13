# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A clean-room reimplementation of [bingosync](https://bingosync.com) with a Vue 3 SPA
frontend and a Django/DRF + Channels backend. `bingosync/` is a **vendored copy of the
original project, used only as a functional reference** — it is gitignored, is not part
of this project's history, and must never be edited or imported from. Read it to answer
"how did the original behave?", nothing else.

`docs/BUILD_REPORT.md` records the architecture decisions and the reasoning behind each
divergence from bingosync; `docs/COMMANDS.md` records the setup command trail.

## Commands

Backend (from `backend/`, venv lives at `backend/.venv`):

```bash
.venv/bin/python manage.py runserver 8000     # ASGI (Daphne): serves HTTP *and* websockets
.venv/bin/python manage.py test rooms         # full suite (~49 tests)
.venv/bin/python manage.py test rooms.tests.test_services.MarkSquareTests.test_lockout_conflict
.venv/bin/python manage.py makemigrations rooms && .venv/bin/python manage.py migrate
.venv/bin/pip freeze | sort > requirements.txt   # how requirements.txt is maintained
```

Frontend (from `frontend/`):

```bash
npm run dev      # Vite on :5173
npm run lint     # eslint --max-warnings 0
npm run build    # vue-tsc -b && vite build (this is the type-check gate)
npx vue-tsc -b   # type-check only
```

End-to-end smoke test — requires the backend already running on :8000, and is **not**
part of `manage.py test`:

```bash
node scripts/smoke_test.mjs
```

Config comes from `backend/.env` (copy of `.env.example`; `SECRET_KEY` is required or
Django won't boot) and `frontend/.env.development` (`VITE_API_BASE_URL`).

Django 5.2 is pinned deliberately — Django 6.x breaks DRF 3.17 (`ImportError: cc_delim_re`).

## Architecture

**One ASGI process.** Unlike bingosync (Django + a separate Tornado websocket service
that HTTP round-trips in both directions), this app runs everything under Daphne.
`daphne` is first in `INSTALLED_APPS` so `runserver` is ASGI-aware; `config/asgi.py`
routes HTTP to Django and websockets to `RoomConsumer` via `core/routing.py`.

**Writes go over REST; state changes come back over the websocket.** Every mutation is a
DRF `POST` under `/api/rooms/<uuid>/…`. The consumer accepts no client messages
(`receive()` is a deliberate no-op) — it only receives broadcasts and tracks
connect/disconnect. Each mutating view calls a `services.py` function, which returns an
`Event`, then passes it to `realtime.broadcast_event()`.

The acting player's own socket is in the same channel group, so **the frontend never
applies its own REST response to local state** — it waits for the broadcast, exactly like
bingosync's click handler does. `stores/room.ts::applyEvent()` is the single dispatcher
for every incoming event type; adding a new event type means adding a case there and a
`services.py` emitter, not touching individual components.

**All business logic lives in `rooms/services.py`**, transaction-wrapped; views are
serializer → service → broadcast → response. Every event is written through
`emit_event()`, which snapshots the player's color at emit time so historical feed
entries keep their original color when a player later recolors.

**Auth: stateless signed bearer tokens, no Django `User`.** `tokens.py` signs a player id
with `SECRET_KEY` (`django.core.signing`, dedicated salt) — no token table.
`PlayerTokenAuthentication` resolves `Authorization: Bearer <token>` and sets
`request.user` to the **`Player` model instance itself**; `Player` duck-types
`is_authenticated`/`is_anonymous` so DRF's `IsAuthenticated` works unmodified. Pair it
with `IsRoomMember` on every room-scoped view — a valid token for room A must not
authorize room B.

Websockets can't send headers, so the consumer reads `?token=`. **The raw ASGI
`query_string` is still percent-encoded** and must be `unquote`d — skipping that was a
real bug that in-process tests missed and `smoke_test.mjs` caught.

**Board size is data, not a constant.** `Game.rows`/`cols` (default 5×5, capped at
`MAX_BOARD_DIMENSION = 15` in serializers), `Square(row, col)` 0-indexed instead of
bingosync's flat 1–25 `slot`, and the frontend renders a CSS grid sized from
`game.rows`/`game.cols`. This is the groundwork for a planned configurable-card-size
feature — don't reintroduce 5×5 assumptions. Note `lineCountForColor()` only counts
diagonals when `rows === cols`.

**Colors are an `IntFlag` bitmask.** `Color` in `rooms/colors.py` replaces bingosync's
hand-rolled `CompositeColor`: compose with `|`, test with `in`, remove with `& ~`. A
`Square` holds a composite (multiple players in non-lockout mode); a `Player` holds a
single color. `Color.names` renders a bitmask to the lowercase string list the API and
frontend speak — the wire format is always color *names*, never the integer.

**One `Event` table** (`type` + JSON `payload`) replaces bingosync's six event subclasses.
`Event.Type` values: `chat`, `goal`, `color`, `revealed`, `connection`, `new_card`.

**A "new card" creates a new `Game` row**, it doesn't mutate the old one;
`Room.current_game` is just the newest game by `created_at`. Old boards stay in the DB.

**Deliberately not ported:** bingosync's ~460 built-in per-game goal-list generators
(hand-written JS eval'd via a `node` subprocess). Board generation is pure Python in
`board_generator.py` and supports only custom goal lists — `fixed` (exactly rows×cols
goals) or `randomized` (sample rows×cols from a larger pool, seedable). Also absent:
server-side win detection — like bingosync, the app counts squares/lines per color and
leaves "bingo!" to humans.

**`InMemoryChannelLayer` is single-process only.** Running multiple workers requires
switching to `channels_redis` first.

## Conventions

- Backend tests live in `rooms/tests/test_*.py` (the app has no `tests.py`); they use
  Django's built-in test runner, not pytest.
- Comments in this codebase explain *why a decision diverges from bingosync* rather than
  what the code does — match that when adding to it.
- Frontend is `<script setup>` + Composition API throughout, Pinia setup-stores (not
  option stores), DTO types in `types/api.ts` mirroring the DRF serializers by hand —
  changing a serializer means updating that file.
- Work on this project has been run milestone-by-milestone with user approval between
  milestones (see `docs/BUILD_REPORT.md` §5); check before scoping work beyond what was
  asked.
