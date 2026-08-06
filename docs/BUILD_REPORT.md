# Build report

A step-by-step account of how this project was analyzed, designed, and
built, from the initial request through the working end-to-end system.

## 1. The brief

Build a new bingo web app (Vue 3 + Django/DRF) that reproduces the
functionality of the existing **bingosync** project, using bingosync only as
a *functional reference* — not something to refactor or copy code from. The
requested process was explicit:

1. Analyze the existing project.
2. Explain understanding of how it works.
3. Propose a backend architecture.
4. Propose a frontend architecture.
5. Identify things worth improving vs. the original.
6. Produce an implementation plan broken into small milestones.
7. Implement one milestone at a time, with approval between each.

A future feature (not to be built yet, but designed for) was flagged up
front: configurable bingo card sizes instead of bingosync's fixed 5×5 grid.

## 2. Analyzing bingosync

The reference project (`bingosync/`) was read in depth: models, views,
forms, URLs, the Tornado websocket service, and the room frontend
(jQuery-based). Key findings:

- **Two-server split.** Django (`bingosync-app`) serves pages and talks to
  Postgres; a separate **Tornado** process (`bingosync-websocket/app.py`)
  holds all websocket connections and relays events pub/sub-style. Django
  calls Tornado over HTTP to publish events; Tornado calls back into Django
  to authenticate sockets and record connect/disconnect. Two processes, two
  deploy targets, and an HTTP round-trip in each direction just to broadcast
  an event.
- **No server-side win detection.** Bingosync never declares a winner — it
  tracks, per player color, how many squares and how many completed
  rows/cols/diagonals are that color, and leaves "bingo!" as a human
  judgment call.
- **Board generation shells out to Node.js.** Each of ~460 supported "game
  types" is a hand-authored `<game>_generator.js` file (a goal list plus a
  generation algorithm), evaluated via `subprocess.check_output(["node",
  "-"], ...)`. This is the single largest chunk of content in the reference
  app, and the least reusable — it's per-game trivia data, not core bingo
  logic.
- **Colors are bitmask composites.** A square can hold multiple overlapping
  player colors at once (non-lockout mode) via a hand-rolled
  `CompositeColor` class built from a plain `Color` enum plus manual bit
  arithmetic.
- **Auth is per-room, session-based**, not global accounts: joining a room
  stores `{room_uuid: player_uuid}` in the Django session. No login system,
  just a room passphrase + nickname.
- **Board is hardcoded 5×5**: `SLOT_RANGE = range(1, 26)`, a fixed 25-cell
  HTML `<table>` with row/col/diagonal CSS classes for hover highlighting.

## 3. Proposed architecture (presented to the user)

**Backend**: generalize the schema (`Square(row, col)` instead of a flat
1–25 `slot`, board size as data rather than a constant), replace the
Node-subprocess generator with pure Python, replace bingosync's six
event-subclass tables with one `Event` table (`type` + JSON `payload`), and
replace the Tornado relay with Django Channels running in the same process.

**Frontend**: Vue 3 Composition API, Pinia for room/session state, Vue
Router, a `useRoomSocket` composable wrapping the websocket connection, and
a board rendered as a CSS grid sized from `rows × cols` rather than a
hardcoded table.

## 4. Decisions confirmed with the user

Three scope-defining questions were asked directly rather than assumed,
since each one materially changes the size and shape of the project:

| Question | Decision |
|---|---|
| Port bingosync's ~460 built-in per-game goal lists? | **No** — custom boards only (paste your own goal list, fixed-length or randomized-from-a-pool), matching bingosync's "Custom (Advanced)" mode. The game catalog may become a much later feature. |
| Keep the two-server (Django + separate websocket service) design? | **No** — consolidate onto **Django Channels**, one ASGI process. |
| Session cookies or bearer tokens for the SPA? | **Bearer tokens**, issued on room join, sent as `Authorization: Bearer <token>` — avoids cross-origin cookie/CORS friction between a separately-served Vue frontend and Django backend. |

## 5. Milestone plan

```
M0  Project scaffolding (Django+DRF+Channels, Vue+Vite+TS, healthcheck round-trip)
M1  Core data model (Room/Game/Square/Player/Event) + create_room/join_room services
M2  REST API: create/join a room, fetch board/settings, generate a new card
M3  Gameplay REST API: mark/unmark a square (lockout rules), color, chat, reveal, feed
M4  Realtime: Django Channels consumer + broadcast wired into every M3 action
M5  Vue: room lifecycle (home, join, Pinia, router)
M6  Vue: board + gameplay (grid, color chooser, players panel, room settings)
M7  Vue: chat + hide-card/reveal flow + styling
M8  End-to-end smoke test + hardening
```

M0 and M1 were built and reviewed individually, per the original one-at-a-
time process. After that, the user was asked explicitly whether to keep
that cadence or run the remaining milestones back-to-back, and chose the
latter — M2 through M8 were then built and verified in one continuous pass
before reporting back.

## 6. M0 — Scaffolding

- **Backend**: Django 5.2 (Django 6.1, what `pip install django` resolved to
  by default, isn't compatible with DRF 3.17 yet — hit an `ImportError` on
  first boot and pinned back to 5.2 LTS) + DRF + Channels, served via
  Daphne so `runserver` is ASGI-aware from the start. `django-environ` for
  `.env`-based settings. `django-cors-headers` for the separately-served
  Vite dev server. SQLite for local dev (`DATABASES` reads `DATABASE_URL`,
  so swapping to Postgres later is a one-line env change). Channels'
  `InMemoryChannelLayer` for now (single-process; would move to
  `channels_redis` before running multiple workers).
- **Frontend**: Vite's `vue-ts` template, ESLint (flat config) + Prettier,
  `.env.development` for `VITE_API_BASE_URL`.
- Verified with a real round-trip: a `core` app healthcheck endpoint, and
  `App.vue` fetching it on mount, confirmed working cross-origin.

## 7. M1 — Core data model

App: `backend/rooms/`.

- **`Room`** — UUID primary key (used directly as the public identifier;
  bingosync base64-encodes a separate UUID field to shorten URLs, which
  wasn't judged worth the complexity here), hashed passphrase, `hide_card`.
- **`Game`** — belongs to a room; carries `rows`/`cols` (not `BoardConfig`,
  a separate model originally sketched for this — folded into `Game` since
  a standalone table for two integers that always live 1:1 with a `Game`
  was pure ceremony), `board_type` (fixed/randomized), `lockout_mode`,
  `seed`.
- **`Square`** — `(row, col)`, 0-indexed (vs. bingosync's 1-indexed flat
  `slot`), and a bitmask `colors` field.
- **`Player`** — UUID primary key, `color_value`, `is_spectator`.
- **`Event`** — one table, `type` + JSON `payload`, replacing bingosync's
  six event subclasses (`ChatEvent`, `GoalEvent`, `ColorEvent`,
  `RevealedEvent`, `ConnectionEvent`, `NewCardEvent`).
- **`Color`** (`rooms/colors.py`) — a Python `IntFlag` enum. This is the
  concrete payoff of the "improvements" proposal: `Color.RED | Color.BLUE`,
  `in` for membership, `& ~Color.RED` for removal — all free from the
  standard library, replacing bingosync's ~150-line hand-rolled
  `CompositeColor` class outright.
- **`board_generator.py`** — pure Python (`random.Random(seed).sample(...)`
  for randomized boards), no more shelling out to `node`.
- **`tokens.py`** — stateless bearer tokens via `django.core.signing`
  (player id signed with `SECRET_KEY`); no separate token table.
- **`services.py`** — `create_room()` / `join_room()`, transaction-wrapped.

27 tests, covering the color bitmask, board generation (fixed/randomized/
non-square/too-small), token round-trip/tamper/unknown-player, and
`create_room`/`join_room` (hashing, wrong passphrase, invalid-board
rollback, spectators, configurable board size).

## 8. M2 — Room/board REST API

- **`authentication.py`** — `PlayerTokenAuthentication`, a DRF
  `BaseAuthentication` reading `Authorization: Bearer <token>`. Since
  there's no Django auth `User` in this app, `request.user` ends up being
  the `Player` instance itself — made possible by adding duck-typed
  `is_authenticated`/`is_anonymous` properties to the `Player` model so
  DRF's `IsAuthenticated` permission works unmodified.
- **`permissions.py`** — `IsRoomMember`, checking the authenticated
  player's `room_id` matches the room in the URL (a valid token for room A
  shouldn't authorize actions in room B).
- Endpoints: `POST /api/rooms/` (create), `POST /api/rooms/<id>/join/`,
  `GET .../board/`, `GET .../settings/`, `GET .../players/`,
  `POST .../new-card/`.
- Fixed mid-build: DRF returned `403` instead of `401` for missing
  credentials until `PlayerTokenAuthentication.authenticate_header()` was
  added — DRF only sends the `401` challenge if an authenticator declares
  one.

## 9. M3 — Gameplay REST API

Added to `services.py`: `mark_square()` (enforces lockout-mode rules —
can't claim an already-claimed square, can't clear someone else's claim),
`change_player_color()`, `send_chat_message()`, `reveal_card()`, all going
through a shared `emit_event()` helper that records the player's color *at
the time of the event* (so historical chat/activity entries don't change
color if the player later switches). Endpoints: `.../goal/`, `.../color/`,
`.../chat/`, `.../reveal/`, `.../feed/`.

## 10. M4 — Django Channels realtime

- **`consumers.py`** — `RoomConsumer`, one websocket per browser tab,
  joined to a `room.<uuid>` Channels group. Authenticates via a `?token=`
  query parameter (browsers can't set custom headers on a WebSocket
  handshake) rather than Django's session-based `AuthMiddlewareStack`,
  consistent with the bearer-token decision.
- **`realtime.py`** — a single sync `broadcast_event()` helper (wraps
  `channel_layer.group_send` in `async_to_sync`), called from both the
  DRF views (M2/M3, already sync) and the consumer's
  `database_sync_to_async`-wrapped connect/disconnect handlers (M4) — one
  broadcast path, not two.
- Connect/disconnect emit and broadcast `connection` events, mirroring
  bingosync's presence tracking.

## 11. M5–M7 — Vue frontend

- **State**: two Pinia stores. `session` persists per-room `{token,
  playerId}` to `localStorage` (a browser can hold sessions for several
  rooms). `room` holds the live room/game/squares/players/events and every
  gameplay action (`toggleSquare`, `setColor`, `postChat`, `reveal`,
  `newCard`), plus `applyEvent()` — a single dispatcher that updates local
  state from every incoming websocket event type.
- **Realtime UI updates go through the websocket only**, not the direct
  REST response — the acting player's own socket is in the same Channels
  group, so the broadcast reaches them too. This mirrors bingosync's own
  pattern (its click handler doesn't touch the DOM directly either) and
  avoids a class of "applied the event twice" bugs.
- **Routing**: `/` (create room), `/rooms/:roomId/join`, `/rooms/:roomId`
  (guarded — no stored session for that room redirects to the join form).
- **Board**: CSS grid sized from `game.rows`/`game.cols`, not a fixed
  table. Multi-color squares render as diagonal stripes (a simpler
  approximation of bingosync's skewed-layer CSS trick, not a pixel-for-
  pixel copy — sufficient for functional parity).
- **Components**: `BoardGrid` (+ hide-card overlay/reveal), `ColorChooser`,
  `PlayersPanel` (live square/line counters per color, ported from
  bingosync's row/col/diagonal counting logic), `RoomSettingsPanel`
  (current settings + new-card form), `ChatPanel` (renders every event
  type, not just chat messages, matching bingosync's combined activity
  feed).
- One functional gap closed along the way: the REST API had no
  players-list endpoint (M2/M3 didn't need one), but the frontend needs an
  initial roster, not just incremental events. Added `GET
  /api/rooms/<id>/players/` plus a `Player.is_connected` property (ported
  from bingosync's `connected` property: no connection event yet = assume
  connected).

## 12. M8 — End-to-end verification and a real bug

Backend unit/integration tests (`manage.py test rooms`, in-process) were
already green — but in-process Channels tests never exercise the actual
network path a browser uses. Wrote `scripts/smoke_test.mjs`, a Node script
hitting the *real running* Daphne server: create a room → join a second
player → reject a wrong passphrase → fetch board/players → open two real
websockets → mark a square and confirm the other player receives it live
→ hit a lockout conflict → broadcast a chat message → regenerate the board
at a different size → replay the feed → observe a disconnect broadcast.

**This caught a real bug.** The first run failed at the websocket step:
`RoomConsumer` read the `?token=` query parameter and used it as-is, but a
real client (correctly) percent-encodes it via `encodeURIComponent()`
because tokens from `django.core.signing` contain `:` separators. The
server never URL-decoded it back, so every real connection's signature
verification failed silently and got rejected. The existing
`test_consumer.py` test hadn't caught this because it connected with the
raw, unencoded token directly — a gap between "the app logic is right" and
"the app works over the wire."

Diagnosed by reading the Daphne log (`WebSocket REJECT`), ruling out a
routing/path issue by reading `channels.routing.URLRouter`'s source
directly, then finding the actual cause. Fixed with `urllib.parse.unquote`
in `consumers.py`, and added `test_connect_with_url_encoded_token` as a
regression test so this can't silently regress.

**Final state, all green:**
- 49 backend tests (`manage.py test rooms`)
- Frontend: `npm run lint` and `npx vue-tsc -b` clean, `npm run build`
  succeeds
- `scripts/smoke_test.mjs` passes all 11 checks against the live server

## 13. Known gaps / deliberately out of scope

- No room-listing page — create/join only (bingosync's homepage room list
  wasn't part of the milestone plan).
- Chat/activity feed always fetches full history on load; bingosync splits
  "recent" (last 24h) vs. "full" as an optimization that wasn't ported.
- No automated *browser* test — verification is TypeScript/ESLint/build
  correctness plus a scripted REST/WebSocket client, not actual rendered-
  page interaction (no browser automation tool was available in this
  environment).
- The ~460-game built-in goal-list catalog was explicitly not ported (see
  §4) — this app only supports custom boards.
