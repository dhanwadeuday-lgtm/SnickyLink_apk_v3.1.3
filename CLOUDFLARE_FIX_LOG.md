# Cloudflare deploy-readiness fixes (this pass)

Scope of review: full Dart source (all 37 files in `frontend/lib`), the
Cloudflare build pipeline (`wrangler.toml`, `package.json`,
`deploy/cloudflare_build.sh`), and asset/pubspec wiring.

## Dart source
No compile errors found. Verified: every relative import resolves to a real
file, every `package:` import is declared in `pubspec.yaml`, every
`AppTheme.*` reference exists on `AppTheme`, provider/notifier/repository
names match consistently across data → domain → presentation layers, and
every `Image.asset(...)` path exists on disk. No changes needed here.

## Build pipeline fixes
1. **`frontend/web/` was incomplete.** Only `_headers` existed; `index.html`,
   `manifest.json`, favicon, and icons were missing. The build script
   worked around this by calling `flutter create --platforms=web .` at
   build time, which is non-deterministic inside CI (can behave
   differently across Flutter versions, and isn't guaranteed to succeed
   the same way twice). Added the full standard web scaffold by hand,
   branded with the moon/bridge mark and the Wine & Peach palette:
   - `frontend/web/index.html`
   - `frontend/web/manifest.json`
   - `frontend/web/favicon.png`
   - `frontend/web/icons/Icon-192.png`, `Icon-512.png`,
     `Icon-maskable-192.png`, `Icon-maskable-512.png`
   The `flutter create` fallback in the build script is left in place as a
   safety net but will no longer trigger.

2. **`deploy/cloudflare_build.sh` depended on `python3`** to parse Flutter's
   `releases_linux.json` and resolve the stable download URL. Cloudflare's
   Pages/Workers build image is Node-based; `python3` is not guaranteed to
   be present, which was a real "command not found" failure risk. Replaced
   the parsing logic with `node -e '...'` (Node is guaranteed, since
   wrangler itself needs it).

3. **`flutter analyze` could fail the whole deploy on a style lint.** The
   script used `set -euo pipefail`, so any analyzer output (even an `info`)
   returning a non-zero exit code would halt the build. Changed it to only
   fail the build on genuine analyzer `error •` lines; warnings/infos are
   printed for visibility but no longer block deployment.

4. **Added `frontend/analysis_options.yaml`** (was missing) so `flutter
   analyze` runs against the standard `flutter_lints` rule set instead of
   undefined defaults.

5. **Removed `deploy/_headers`**, an unused duplicate of
   `frontend/web/_headers` (the one that actually ships, since Flutter
   copies everything under `web/` into `build/web/` verbatim). It wasn't
   referenced anywhere and only added confusion.

6. Verified `package.json`'s pinned `wrangler@4.131.1` against the npm
   registry — it's a real, currently-latest version. No change needed.

## Round 2: actual deploy-time errors (from a real Cloudflare Workers Builds run)
The build itself succeeded (Flutter web output built, 50 asset files uploaded)
but `wrangler deploy` then failed with two issues:

1. **`⚠ Failed to match Worker name`** — `wrangler.toml` had `name =
   "snickylink-web"`, but the Cloudflare dashboard project (and its CI) was
   named `snickylink-apk-v3-1`. Updated `wrangler.toml`'s `name` to match.
   **If your dashboard project has a different name, update this field to
   match it exactly** — it must be identical to what's in Workers & Pages →
   your project in the Cloudflare dashboard.

2. **`✗ [ERROR] Invalid _redirects configuration: infinite loop detected`**
   — this was the actual fatal error. The build script always wrote a
   `build/web/_redirects` file (`/* /index.html 200`) for SPA fallback
   routing. That file is a **Cloudflare Pages** mechanism. For **Cloudflare
   Workers** static assets (which is what `wrangler deploy` uses),
   `wrangler.toml`'s `[assets] not_found_handling = "single-page-application"`
   already provides the same SPA fallback at the asset-serving layer — having
   both active at once creates a redirect loop that wrangler now refuses to
   deploy.

   Fixed by making `_redirects` generation conditional on a `DEPLOY_TARGET`
   env var:
   - `npm run cf:deploy` (Pages) sets `DEPLOY_TARGET=pages` → writes
     `_redirects`, since `wrangler pages deploy` doesn't read `[assets]` at
     all.
   - `npm run cf:deploy:worker` / the Cloudflare dashboard's Build command
     (`bash deploy/cloudflare_build.sh`) → `DEPLOY_TARGET` unset → skips
     `_redirects`, relying on `wrangler.toml` instead.

## Round 3: clarified goal is an APK, not a web deploy
Cloudflare Pages/Workers can only host the Flutter **web** build — it
cannot produce an Android `.apk`. That whole troubleshooting thread was for
a different goal than what was actually needed. Added a separate,
Cloudflare-independent path to a beta APK:

- **`.github/workflows/build-apk.yml`** — a free GitHub Actions workflow
  that generates the missing `android/` scaffold, runs `flutter build apk
  --release`, and uploads the `.apk` as a downloadable artifact. No local
  Flutter/Android SDK install needed.
- **`APK_BETA_GUIDE.md`** — step-by-step: trigger the workflow, download
  the APK, then distribute it to ~100 testers for free via Firebase App
  Distribution (up to 500 testers/project, no Play Console account or fee
  needed for beta testing).

## Deploying
Nothing about the deploy commands changed:

```bash
npm install
API_BASE_URL=https://api.snickylink.app npm run cf:deploy          # Pages
API_BASE_URL=https://api.snickylink.app npm run cf:deploy:worker   # Workers
```

Set `API_BASE_URL` to your actual deployed FastAPI backend URL (e.g. the
Render URL for `snickylink-api`) before deploying.
