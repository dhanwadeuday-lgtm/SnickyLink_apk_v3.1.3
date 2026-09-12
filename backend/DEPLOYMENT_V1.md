# SnickyLink Backend Deployment

## Docker production layout

Use `docker-compose.production.yml` as a reference deployment:

- `api`: FastAPI, no scheduler in the API replica.
- `worker`: dedicated APScheduler + durable event worker.
- `postgres`: durable relational state/outbox.
- `redis`: leaderboard/cache projection.

Before startup, copy `.env.example` to `.env` and replace every production secret/placeholder.

## Database

Run these migrations against PostgreSQL:

```text
migrations/001_architecture_hardening.sql
migrations/002_production_hardening.sql
```

Do not use `AUTO_CREATE_TABLES=true` in production.

## API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

## Dedicated worker

```bash
python -m app.worker
```

The worker owns the scheduled jobs and durable event delivery. Multiple worker processes can safely claim events because event rows use PostgreSQL `FOR UPDATE SKIP LOCKED`.

## Event delivery

`EventBus.publish()` only writes a durable outbox row. The worker executes handlers later. Handler delivery has its own status, retry count, error and next-attempt timestamp. One failed handler does not prevent successful sibling handlers from being recorded.

## Media

Production media requires S3/R2-compatible storage. Images are validated server-side with Pillow, bounded by byte size and pixel count, and thumbnails are generated asynchronously from `MEDIA_UPLOADED`.

## AI

Set `AI_PROVIDER=vision` and `AI_API_KEY` in production. AI verification is background work and falls back to partner confirmation when confidence is below the auto-verification threshold.

## Chat

V1 deliberately uses HTTP polling, not WebSockets:

```text
GET /chat/messages/history?since_timestamp=<ISO-8601>
```

The client can poll this endpoint until a realtime transport is added in a later release.

## Password recovery

Password recovery endpoints are included. Configure SMTP variables for actual email delivery. OTP remains out of scope for this release.
