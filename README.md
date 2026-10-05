# SocialPulse

> **Maintained by [Jennita S](https://github.com/Jennita-Santhakumar)** · [LinkedIn](https://linkedin.com/in/jennitas) · jennitasanthakumar0@gmail.com

A social network API and web client: posts, comments, likes, follows, and real-time
notifications delivered over WebSocket. Built with Django REST Framework, Django
Channels, Celery, PostgreSQL, Redis, and a React + TypeScript frontend.

## Architecture

```
                     ┌──────────────────────────┐
                     │  React + TypeScript (SPA) │
                     │  Vite build → nginx :5230 │
                     └─────────────┬─────────────┘
                                   │ REST (JWT)         WebSocket (?token=<jwt>)
                                   ▼                          ▼
                     ┌───────────────────────────────────────────────┐
                     │        Daphne ASGI server  :8050               │
                     │  ┌─────────────┐        ┌────────────────────┐│
                     │  │ Django REST │        │  Channels consumer  ││
                     │  │  Framework  │        │  (NotificationCons.)││
                     │  └──────┬──────┘        └──────────┬─────────┘│
                     └─────────┼──────────────────────────┼──────────┘
                                │                          │ group_send
                                ▼                          │ (user_{id} groups)
                     ┌────────────────────┐                │
                     │   PostgreSQL 15     │                │
                     │ posts/comments/     │                │
                     │ likes/follows/      │                │
                     │ notifications       │                │
                     └────────────────────┘                │
                                ▲                            │
                                │ writes                     │
                     ┌──────────┴──────────┐     ┌───────────▼──────────┐
                     │   Celery worker      │◄────┤  Redis (broker +     │
                     │  create_notification │     │  channel layer +     │
                     │  send_notification_  │     │  Celery result store)│
                     │  email (+15s delay)  │     └───────────┬──────────┘
                     └──────────┬───────────┘                 │
                                │                    ┌─────────▼─────────┐
                                │                    │   Celery beat      │
                                │                    │ prune_old_         │
                                │                    │ notifications      │
                                │                    │ (hourly)           │
                                └────────────────────┴─────────────────────
```

Flow for a "like": client `POST /api/posts/{id}/like/` → view updates `likes_count`
in Postgres → `create_notification.delay(...)` enqueues a Celery task → the worker
writes a `Notification` row, pushes it live to the `user_{recipient_id}` Channels
group over Redis, and schedules a 15-second-delayed confirmation email via a second
Celery task. Any browser with an open WebSocket to that user's notification stream
receives the event immediately, with no polling.

## Features

- Posts: create/read/update/delete, like/unlike, personalized feed (posts from
  followed users only)
- Comments on posts, with running `comments_count` maintained on the post
- Follow/unfollow with maintained `followers_count`/`following_count` on profiles
- Real-time in-app notifications over WebSocket (Django Channels, per-user group
  `user_{id}`) for likes, comments, and follows
- Async processing via Celery: notification creation + WebSocket push, and a
  15-second-delayed confirmation email
- Celery Beat periodic task: hourly pruning of read notifications older than 30 days
- JWT auth (`djangorestframework-simplejwt`): register, obtain, refresh
- DRF throttling (`UserRateThrottle` / `AnonRateThrottle`) on every endpoint

## Design Decisions & Trade-offs

- **DRF throttle classes instead of `django-ratelimit`.** The PRD's sketch uses
  `django-ratelimit`, but DRF ships `UserRateThrottle`/`AnonRateThrottle` that
  integrate natively with `DEFAULT_PERMISSION_CLASSES`/viewsets, need no extra
  dependency, and are configured entirely through `REST_FRAMEWORK` settings
  (`THROTTLE_RATE_USER`/`THROTTLE_RATE_ANON` env vars here). One fewer package to
  patch and version-track for the same behavior.
- **Daphne (ASGI) instead of `runserver`/gunicorn+WSGI.** Real-time notifications
  require Channels, which needs an ASGI server end-to-end. Daphne is the
  Channels-maintained reference server, so `web` in docker-compose runs
  `daphne config.asgi:application` rather than a WSGI app server, serving both the
  REST API and the `/ws/notifications/` consumer from one process.
- **A real periodic task for Celery Beat, not a stub.** Rather than leave
  `celery-beat` running with nothing to do, it prunes `Notification` rows that are
  both read and older than 30 days every hour (`social.tasks.prune_old_notifications`).
  This keeps the notifications table from growing unbounded while never touching
  unread notifications a user hasn't seen yet.
- **Console email backend by default.** `EMAIL_BACKEND` defaults to
  `django.core.mail.backends.console.EmailBackend`, which prints outgoing mail to
  the `celery` worker's stdout instead of requiring SMTP credentials for local dev
  or CI. Set `EMAIL_BACKEND`/`EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` to
  point at real SMTP (e.g. SES, SendGrid) in production.
- **JWT auth over sessions.** The SPA and API are decoupled (separate origins/ports
  in dev), so stateless JWT access/refresh tokens (`SIMPLE_JWT`, 30 min access /
  7 day refresh, rotating) avoid CSRF/cookie complexity across origins. The
  WebSocket consumer authenticates the same JWT via a `?token=` query param, since
  browsers cannot set `Authorization` headers on WebSocket handshakes.
- **Non-default host ports.** To avoid clashing with other local portfolio
  projects running simultaneously, every service is bound to a non-default host
  port (see table below) rather than the PRD's plain 8000/3000/5432/6379.

## Running locally

### Option A: Docker Compose (recommended, one command)

```bash
cp .env.example .env
docker compose up --build
```

| Service      | Container port | Host port | URL |
|--------------|-----------------|-----------|-----|
| web (Daphne) | 8000            | **8050**  | http://localhost:8050 |
| frontend     | 80              | **5230**  | http://localhost:5230 |
| db (Postgres)| 5432            | **5442**  | postgres://localhost:5442 |
| redis        | 6379            | **6390**  | redis://localhost:6390 |
| celery       | -               | -         | worker, no exposed port |
| celery-beat  | -               | -         | scheduler, no exposed port |

Postgres and Redis have healthchecks; `web`/`celery`/`celery-beat` wait for
`service_healthy` on both before starting, and the backend entrypoint also blocks
until Postgres accepts TCP connections before running migrations.

### Option B: Run natively

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
# start Postgres 15 and Redis 7 locally (or via `docker compose up db redis`)
python manage.py migrate
daphne -b 0.0.0.0 -p 8050 config.asgi:application
# in separate terminals:
celery -A config worker -l info
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5230
```

## API reference

Base URL: `http://localhost:8050/api/`

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register/` | Create a user (`username`, `password`, `email`) |
| POST | `/auth/token/` | Obtain JWT access + refresh tokens |
| POST | `/auth/token/refresh/` | Refresh an access token |
| GET | `/auth/me/` | Current authenticated user + profile |
| GET/POST | `/posts/` | List / create posts |
| GET/PUT/PATCH/DELETE | `/posts/{id}/` | Retrieve / update / delete a post (author only) |
| POST | `/posts/{id}/like/` | Like a post (idempotent, notifies author) |
| POST | `/posts/{id}/unlike/` | Unlike a post |
| GET | `/posts/feed/` | Posts from users you follow, newest first |
| GET/POST | `/comments/?post={id}` | List comments for a post / create a comment |
| GET/POST | `/follows/` | List who you follow / follow a user (`following=<id>`) |
| DELETE | `/follows/{id}/` | Unfollow |
| GET | `/notifications/` | List your notifications |
| POST | `/notifications/{id}/mark_read/` | Mark one notification read |
| POST | `/notifications/mark-all-read/` | Mark all notifications read |
| WS | `/ws/notifications/?token=<jwt access token>` | Live notification stream |

All endpoints except `register`/`token` require `Authorization: Bearer <access>`.

## Running tests

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements-dev.txt
# needs a real Postgres + Redis reachable at POSTGRES_HOST/PORT, REDIS_HOST/PORT
# e.g. docker run -d -p 5442:5432 -e POSTGRES_DB=socialpulse_test -e POSTGRES_USER=socialpulse -e POSTGRES_PASSWORD=socialpulse postgres:15-alpine
# e.g. docker run -d -p 6390:6379 redis:7-alpine
pytest --cov=social --cov-report=term-missing
```

Actual result on this build (real Postgres 15 + Redis 7 containers, Python 3.11):
**29 passed, 0 failed, 95% coverage** on the `social` app. Tests are split into
`tests/unit/` (permission/serializer/celery-config logic, no DB) and
`tests/integration/` (auth, posts, comments, follows, notifications/Celery tasks,
and a WebSocket test using Channels' `WebsocketCommunicator` against the real
Redis-backed channel layer).

Frontend:

```bash
cd frontend
npm install
npm run lint     # eslint — passes clean
npm run build    # tsc -b && vite build — passes clean, ~173 kB JS bundle (56 kB gzip)
```

## Tech stack

Django 5, Django REST Framework, djangorestframework-simplejwt, Django Channels +
channels-redis, Daphne, Celery + django-celery-beat, PostgreSQL 15, Redis 7,
React 18 + TypeScript + Vite, React Router, pytest + pytest-django, ruff, ESLint,
Docker Compose, GitHub Actions.

## Credits

Developed by Kabilesh Rajaselvan with contributions from Jennita S.
