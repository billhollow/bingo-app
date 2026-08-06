# Build commands

The exact shell commands used to build this project, in order, grouped by
milestone. Commands run repeatedly during debugging (re-running the test
suite, curling a healthcheck, restarting a dev server) are shown once
representatively rather than every time they were actually invoked. File
edits (the actual source code) aren't listed here — this is the
environment/tooling trail; see `docs/BUILD_REPORT.md` for what was built and
why, and `git log` for the code itself.

All commands are relative to `/home/piero/work/bingo-app` unless a `cd` is
shown.

## M0 — project scaffolding

### Environment check

```bash
python3 --version; pip3 --version; node --version; npm --version
pyenv versions
```

pyenv's `system` Python had no `pip`; picked an already-installed pyenv
version with pip available instead of installing a new one.

### Backend: Django + DRF + Channels

```bash
mkdir -p backend && cd backend
~/.pyenv/versions/3.12.10/bin/python3 -m venv .venv
echo "3.12.10" > .python-version

.venv/bin/pip install --upgrade pip
.venv/bin/pip install django djangorestframework channels daphne django-cors-headers django-environ

.venv/bin/django-admin startproject config .
.venv/bin/python manage.py startapp core
```

`pip install django` pulled Django 6.1 (just released), which DRF 3.17
isn't compatible with yet (`ImportError: cannot import name 'cc_delim_re'`).
Pinned back to the 5.2 LTS line:

```bash
.venv/bin/pip install "django==5.2.*"
.venv/bin/python manage.py check
.venv/bin/pip freeze | sort > requirements.txt
```

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 8000 &
curl -s http://localhost:8000/api/healthcheck/
```

### Frontend: Vue 3 + Vite + TypeScript

```bash
cd /home/piero/work/bingo-app
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install

npm install -D eslint @eslint/js eslint-plugin-vue @vue/eslint-config-typescript prettier eslint-config-prettier

npx vue-tsc -b
npm run lint
npm run dev -- --port 5173 &
curl -s -i http://localhost:5173/
curl -s -i -H "Origin: http://localhost:5173" http://localhost:8000/api/healthcheck/   # verify CORS
```

## M1 — core data model

```bash
cd backend
.venv/bin/python manage.py startapp rooms
rm rooms/tests.py rooms/views.py
mkdir rooms/tests && touch rooms/tests/__init__.py

.venv/bin/python manage.py makemigrations rooms
.venv/bin/python manage.py migrate
.venv/bin/python manage.py check

.venv/bin/python manage.py test rooms -v 2
```

## M2–M4 — REST API, gameplay endpoints, Channels realtime

No new dependencies (Channels, DRF, and CORS were already installed in M0).
Iterated on `rooms/{authentication,permissions,serializers,views,urls,
services,realtime,consumers,routing}.py`, re-running after each change:

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test rooms
```

One fix mid-stream: DRF returned 403 instead of 401 for missing credentials
until `PlayerTokenAuthentication.authenticate_header()` was added (DRF only
sends a 401 challenge if an authenticator declares one).

```bash
.venv/bin/pip freeze | sort > requirements.txt   # unchanged, confirmed no new deps
```

## M5–M7 — Vue frontend (room lifecycle, board, gameplay, chat)

```bash
cd frontend
npm install pinia vue-router
npx vue-tsc -b
npm run lint
```

## M8 — end-to-end smoke test and hardening

```bash
lsof -ti:8000,5173 | xargs -r kill   # clear stale dev servers before a clean run

cd backend
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 8000 &
curl -s http://localhost:8000/api/healthcheck/
```

Wrote `scripts/smoke_test.mjs`, exercising the real running server end to
end: create room → join second player → wrong-passphrase rejection → fetch
board/players → open two real websockets → mark a square and confirm the
other player receives it live → lockout conflict → chat broadcast →
regenerate the board at a different size → feed replay → disconnect
broadcast.

```bash
cd /home/piero/work/bingo-app
node scripts/smoke_test.mjs
```

First run failed at the websocket step: the consumer read the `?token=`
query parameter without URL-decoding it, so a real client's
`encodeURIComponent()`-encoded token (it contains `:` separators from
`django.core.signing`) never verified. Diagnosed via the Daphne log
(`WebSocket REJECT`) and by reading `channels.routing.URLRouter`'s source
to rule out a routing/path issue first:

```bash
tail -60 django.log
.venv/bin/python -c "import channels.routing, inspect; print(inspect.getsource(channels.routing.URLRouter))"
```

Fixed in `rooms/consumers.py` (added `urllib.parse.unquote`), added a
regression test exercising a URL-encoded token, then re-verified everything:

```bash
.venv/bin/python manage.py test rooms      # (from backend/)

lsof -ti:8000 | xargs -r kill
.venv/bin/python manage.py runserver 8000 &
cd .. && node scripts/smoke_test.mjs       # now passes end to end

cd frontend
npm run build               # vue-tsc -b && vite build
npm run dev -- --port 5173 &
```

Final verification pass (everything green):

```bash
cd backend && .venv/bin/python manage.py test rooms
cd ../frontend && npm run lint && npx vue-tsc -b
cd .. && node scripts/smoke_test.mjs
```
