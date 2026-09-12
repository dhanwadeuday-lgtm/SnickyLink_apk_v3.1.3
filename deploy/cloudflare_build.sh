#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${API_BASE_URL:=https://api.snickylink.app}"

install_flutter() {
  if command -v flutter >/dev/null 2>&1; then
    return
  fi
  echo "Flutter SDK not found; installing stable Flutter SDK for this build..."
  mkdir -p "$ROOT/.tooling"
  if [ ! -x "$ROOT/.tooling/flutter/bin/flutter" ]; then
    curl -fsSL https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json \
      -o "$ROOT/.tooling/releases_linux.json"

    # Resolve the current stable archive URL with node, not python3.
    # Cloudflare's Pages/Workers build image is Node-based and guarantees
    # node (wrangler itself needs it) but does NOT guarantee python3, so
    # relying on python3 here is a real source of "command not found" build
    # failures on Cloudflare specifically.
    FLUTTER_URL=$(node -e '
      const fs = require("fs");
      const data = JSON.parse(fs.readFileSync(".tooling/releases_linux.json", "utf8"));
      const base = "https://storage.googleapis.com/flutter_infra_release/releases/";
      const stableHash = data.current_release.stable;
      const release = data.releases.find(r => r.hash === stableHash);
      if (!release) {
        console.error("Could not locate Flutter stable archive");
        process.exit(1);
      }
      console.log(base + release.archive);
    ')

    curl -fL "$FLUTTER_URL" -o "$ROOT/.tooling/flutter.tar.xz"
    tar -xJf "$ROOT/.tooling/flutter.tar.xz" -C "$ROOT/.tooling"
    rm -f "$ROOT/.tooling/flutter.tar.xz"
  fi
  export PATH="$ROOT/.tooling/flutter/bin:$PATH"
}

install_flutter
flutter --version
flutter config --enable-web >/dev/null

cd "$ROOT/frontend"
# Generate the native/web Flutter scaffolding only if this source package
# does not already contain it (it does -- web/index.html, manifest.json,
# icons/ and favicon.png are committed). This preserves the existing Dart
# code and assets and avoids depending on `flutter create` mutating the
# project non-deterministically inside CI.
if [ ! -f web/index.html ]; then
  flutter create --platforms=web .
fi

flutter clean
flutter pub get

# `flutter analyze` is run for diagnostics only. Style-level warnings/infos
# must never block a production deploy; only genuine analyzer *errors* do.
# (Cloudflare Pages otherwise fails an entire deploy on a lint nit, which is
# not the intent behind running this step -- see deploy/BUILD_DIAGNOSTIC.md.)
set +e
ANALYZE_OUTPUT="$(flutter analyze 2>&1)"
ANALYZE_EXIT=$?
set -e
echo "$ANALYZE_OUTPUT"
if [ "$ANALYZE_EXIT" -ne 0 ] && echo "$ANALYZE_OUTPUT" | grep -qE "^[[:space:]]*error •"; then
  echo "flutter analyze found real errors above; failing the build."
  exit 1
fi

flutter build web --release --dart-define="API_BASE_URL=${API_BASE_URL}"

# SPA fallback routing:
# - Cloudflare Workers static assets (wrangler.toml's [assets]
#   not_found_handling = "single-page-application") already handles this at
#   the asset-serving layer. Also writing a `_redirects` file with
#   `/* /index.html 200` on top of that causes wrangler to reject the
#   deploy with "Invalid _redirects configuration: infinite loop detected"
#   (the redirect and the not_found handler fight over the same rule).
# - Cloudflare Pages (`wrangler pages deploy`) does NOT read wrangler.toml's
#   [assets] block at all, so it needs the `_redirects` file instead.
# DEPLOY_TARGET is set to "pages" by `npm run cf:deploy` and left unset
# (defaulting to the Workers-safe behavior) by `npm run cf:deploy:worker`.
if [ "${DEPLOY_TARGET:-workers}" = "pages" ]; then
  cat > build/web/_redirects <<'REDIRECTS'
/* /index.html 200
REDIRECTS
  echo "Wrote build/web/_redirects for Cloudflare Pages."
else
  echo "Skipping _redirects (Workers assets handles SPA fallback via wrangler.toml)."
fi

echo "Cloudflare web build ready: $ROOT/frontend/build/web"
