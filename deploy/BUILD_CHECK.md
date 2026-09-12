# Build check

The frontend is Flutter. Cloudflare must build the Flutter web output before Wrangler deploys it.

Use:

```bash
bash deploy/cloudflare_build.sh
```

The script installs Flutter stable if needed, runs `flutter pub get`, then `flutter build web --release` and outputs `frontend/build/web`.

Cloudflare Worker deploy command:

```bash
npx wrangler deploy
```

Cloudflare Pages deploy command (if using Pages instead of Workers):

```bash
npm run cf:deploy
```
