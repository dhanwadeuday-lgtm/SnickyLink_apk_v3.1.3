# SNICKYLINK DEPLOYMENT PACKAGE V1.2

## Source of truth
The `frontend/` directory from the backend bundle is the source of truth. The disconnected preview frontend was NOT used.

## What was merged/fixed
- Replaced the old copper-rose theme with Wine & Peach:
  #6B2B3C Muted Wine
  #3A1620 Deep Wine-Black
  #E8B99C Warm Peach
  #FBF4F1 Blush White
  #1E0E13 Ink Wine
- Integrated the new moon/bridge SnickyLink logo assets.
- Added system light/dark theme support.
- Added production `--dart-define=API_BASE_URL` support.
- Increased network timeouts for mobile networks.
- Added real `/auth/logout` call before clearing local tokens.
- Added chat repository `since_timestamp` support.
- Removed unsafe fake `stub-media-id` memory creation.
- Fixed the profile-screen syntax error and wired logout.
- Preserved the real Riverpod/Dio/secure-storage architecture.
- Added Docker Compose for PostgreSQL + Redis + API + worker.
- Added reverse-proxy rate limiting example.
- Added deployment documentation.

## Backend
FastAPI + PostgreSQL + Redis + durable outbox/event worker.

Production services:
- api: `uvicorn app.main:app`
- worker: `python -m app.worker`

Do not run the API's scheduler in production; the dedicated worker owns scheduled jobs and event delivery.

## Text verification policy
Text submissions intentionally enter `NEEDS_PARTNER_CONFIRMATION`. The partner decision is the server-side verification authority. This is the conservative V1 business rule used by the current codebase.

## Mobile
The package contains the Flutter Dart source and assets for one Android+iOS codebase. Native platform wrappers may need to be generated with the installed Flutter SDK:

```bash
cd frontend
flutter create .
flutter pub get
```

Then configure Android signing and iOS Bundle ID/Apple signing.

Build:
```bash
flutter build apk --release --dart-define=API_BASE_URL=https://api.snickylink.app
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.snickylink.app
# macOS:
flutter build ipa --release --dart-define=API_BASE_URL=https://api.snickylink.app
```

## Required production secrets/config
- DATABASE_URL / POSTGRES_PASSWORD
- SECRET_KEY (>=32 random chars)
- MEDIA_SIGNING_KEY (>=32 random chars)
- S3-compatible storage credentials
- AI_API_KEY
- FCM configuration
- SMTP configuration
- CORS_ORIGINS
- HTTPS reverse proxy

Never commit `.env` or signing credentials.
