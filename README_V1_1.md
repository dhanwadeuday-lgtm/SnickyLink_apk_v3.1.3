# SnickyLink Cross-Platform V1.1

This is the cumulative SnickyLink codebase: Flutter frontend + FastAPI backend.

## Backend
See `backend/PRODUCTION_AUDIT_V1_1.md` and `backend/DEPLOYMENT_V1.md`.

The V1.1 backend hardening covers the remaining architecture gaps identified in the 22-engine reconciliation: durable event delivery with handler-level retries, background AI verification/moderation, media validation and thumbnails, automatic memories, moderation/suspension, gamification levels/badges, chat polling, calendar reminders, device management, refresh tokens and password recovery.

## Mobile
The `frontend/` directory remains the cross-platform Flutter client. It targets Android and iOS from the same Dart codebase.

## Build

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Production worker:

```bash
cd backend
python -m app.worker
```

Mobile:

```bash
cd frontend
flutter pub get
flutter run
```

For store builds, use the Flutter Android/iOS signing configuration on the release machine.
