# SnickyLink — Cloudflare-ready source package

This package fixes the Wrangler error:

`Could not detect a directory containing static files`

The cause is that Wrangler was being asked to deploy the Flutter source tree instead of the generated Flutter Web output.

Correct flow:

`frontend/` → `flutter build web` → `frontend/build/web/` → Cloudflare Pages/Workers

For Cloudflare Pages, use `npm run cf:deploy` or configure the documented build command/output directory.

For Android/iOS, use the same `frontend/` Flutter source with the Android SDK or Xcode. Cloudflare itself does not publish APK/IPA binaries.
