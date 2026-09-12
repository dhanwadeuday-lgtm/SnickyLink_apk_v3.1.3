# SnickyLink Cross-Platform Production Package

This package intentionally uses the **architecturally complete frontend embedded in the backend V1.1 bundle**, not the disconnected preview shell.

## Frontend

`frontend/` is the Flutter client:
- Dio networking
- JWT + refresh token storage
- Riverpod state management
- Existing feature/repository architecture
- Wine & Peach design system
- New SnickyLink moon/bridge logo integrated
- Android + iOS target source

Set the production API at build time:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=https://api.example.com
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.example.com
# macOS + Xcode:
flutter build ipa --release --dart-define=API_BASE_URL=https://api.example.com
```

If the extracted source does not contain generated `android/` and `ios/` wrappers, run `flutter create .` once inside `frontend/`. This generates standard platform wrappers around the same Dart source.

## Backend

`backend/` is FastAPI + PostgreSQL + Redis.

Production requires:
- PostgreSQL
- Redis
- strong SECRET_KEY
- strong MEDIA_SIGNING_KEY
- S3-compatible media storage
- AI API key if using the vision provider
- FCM credentials
- SMTP credentials for password reset

The backend refuses unsafe production secrets at startup.

## Worker

Run a dedicated event worker:

```bash
cd backend
python -m app.worker
```

The worker owns the outbox delivery loop and scheduled jobs.

## Important release checks

Before App Store / Play Store submission:
1. Set production API URL.
2. Configure Android signing.
3. Configure iOS Bundle ID, Team and signing on macOS/Xcode.
4. Configure APNs/FCM credentials.
5. Configure privacy permission strings.
6. Configure S3/R2 and CDN.
7. Run migrations.
8. Put API behind HTTPS and a rate-limiting reverse proxy.
9. Run the backend test suite in CI with real PostgreSQL/Redis services.
