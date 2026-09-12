# Cloudflare Flutter Web build

The previous build reached `Compiling lib/main.dart for the Web...` and then failed, but the supplied log omitted the actual Dart compiler diagnostic.

This package fixes the relative imports that were invalid in presentation/screens (`../../domain` and `../../../../core`), and the build script now runs `flutter clean` and `flutter analyze` before the web build so Cloudflare prints the real compiler diagnostic if anything remains.

Cloudflare Worker settings:
- Root: `/`
- Build command: `bash deploy/cloudflare_build.sh`
- Deploy command: `npx wrangler deploy`
- Worker assets: `./frontend/build/web`

If a build still fails, the first `Error:` line above `Failed to compile application for the Web` is the actionable compiler diagnostic.
