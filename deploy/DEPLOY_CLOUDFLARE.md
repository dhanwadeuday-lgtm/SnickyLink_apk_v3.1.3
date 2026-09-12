# SnickyLink — Cloudflare deployment

## Important
Cloudflare Pages/Workers hosts the **Flutter Web** build. It does not install or publish an Android APK or iOS IPA. The same Flutter source is used to build Android/iOS separately.

## Cloudflare Pages (recommended for web)
Set these in the Cloudflare Pages project:

- Build command: `bash deploy/cloudflare_build.sh`
- Build output directory: `frontend/build/web`
- Environment variable: `API_BASE_URL=https://YOUR-FASTAPI-DOMAIN`

Alternatively, from a machine with Node + Flutter/network access:

```bash
npm install
API_BASE_URL=https://YOUR-FASTAPI-DOMAIN npm run cf:deploy
```

The build script installs Flutter stable if it is missing, generates the Flutter web wrapper if needed, runs `flutter pub get`, builds `frontend/build/web`, and adds the SPA fallback.

## Cloudflare Workers static assets
After `npm install`:

```bash
API_BASE_URL=https://YOUR-FASTAPI-DOMAIN npm run cf:deploy:worker
```

This uses `wrangler.toml` and serves `frontend/build/web` as static assets.

## Cloudflare Workers Builds (git-connected CI/CD)
If you connected this repo to Cloudflare through **Workers Builds** (the
dashboard project has separate **Build command** and **Deploy command**
fields, rather than Pages' single "build output directory" setting), both
fields must be set explicitly — leaving Build command blank means nothing
ever runs `flutter build web`, so the Deploy command's `wrangler deploy`
fails with:

```
X [ERROR] The directory specified by the "assets.directory" field in your
configuration file does not exist: /opt/buildhome/repo/frontend/build/web
```

Set, in the Cloudflare dashboard under the project's **Settings → Build**:

- **Build command**: `bash deploy/cloudflare_build.sh` (or `npm run build`,
  which is an alias for the same script)
- **Deploy command**: `npx wrangler deploy`
- **Environment variable**: `API_BASE_URL` = your deployed FastAPI backend
  URL (e.g. the Render URL for `snickylink-api`)

Both commands run in the same build container in order (build, then
deploy), so the Flutter web output exists on disk by the time `wrangler
deploy` reads `wrangler.toml`'s `[assets] directory`.

## Android APK
Cloudflare is not the Android build environment. Build the same `frontend/` source with Flutter/Android SDK:

```bash
cd frontend
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://YOUR-FASTAPI-DOMAIN
```

## iOS IPA
Build on macOS with Xcode:

```bash
cd frontend
flutter pub get
flutter build ipa --release --dart-define=API_BASE_URL=https://YOUR-FASTAPI-DOMAIN
```

Configure Apple signing in Xcode before App Store submission.

## Backend
Deploy `backend/` separately as a FastAPI service. Cloudflare Pages should point to the backend's HTTPS URL; do not attempt to deploy FastAPI as a Pages static directory.
