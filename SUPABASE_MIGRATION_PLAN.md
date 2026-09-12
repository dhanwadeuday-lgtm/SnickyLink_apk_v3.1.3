# Render → Supabase migration plan

Decision made: fully move off Render (FastAPI + Postgres + Redis) onto
Supabase. This is a real architectural rewrite, not a config change —
your current backend has real business logic (E2EE chat, an event bus,
idempotent diamond transactions, AI-verification scoring, moderation) that
lived in Python. All of that has to be re-homed somewhere. In Supabase,
that "somewhere" is: RLS policies (for access control), Postgres functions
/ triggers (for logic that must be atomic and server-side), and Edge
Functions (for anything needing external calls, e.g. the AI verification
step, or logic too complex for a SQL function).

Doing this correctly in one shot isn't realistic — here's the phased plan.
Each phase is independently useful and testable before moving to the next.

## Phase 1 — Database schema + RLS (delivered in this pass)
- `supabase/migrations/0001_initial_schema.sql`: every table from the
  FastAPI models, translated to Postgres, with `profiles` replacing the old
  `users` table (linked to Supabase's built-in `auth.users` instead of
  storing `hashed_password` ourselves — Supabase Auth owns that now).
- `password_reset_tokens` is dropped entirely — Supabase Auth has built-in
  password reset email flows, no custom table needed.
- RLS enabled on every table, scoped so a user can only ever see their own
  data or their paired partner's data (via a `current_couple_id()` helper
  function). Tables with logic that must not be tampered with client-side
  (diamond crediting, submission verification/approval, couple pairing
  itself) get **no direct client write policies at all** — only Postgres's
  `service_role` (used by Edge Functions, never exposed to the app) can
  write to them. This preserves the same trust boundary FastAPI used to
  enforce in Python.

## Phase 2 — Auth
- Enable Email/Password and Google sign-in in Supabase dashboard
  (Authentication → Providers).
- A Postgres trigger on `auth.users` auto-creates a matching `profiles` row
  on signup (included in the Phase 1 migration file).
- Flutter: replace the custom `AuthRepository`/`AuthNotifier` (which call
  your FastAPI `/auth/*` endpoints) with `supabase_flutter`'s
  `supabase.auth.signUp/signInWithPassword/signInWithOAuth`.

## Phase 3 — Storage
- Buckets: `profile-photos`, `couple-media` (memories, chat media, snick
  submission photos), scoped by folder-per-couple with Storage RLS
  policies mirroring the Postgres ones.
- Flutter: replace whatever currently uploads to your FastAPI `/media`
  endpoint with `supabase.storage.from(...).upload(...)`.

## Phase 4 — Business logic as Edge Functions
Anything that must be atomic, trusted, or call an external API moves here
(Deno/TypeScript, deployed with the Supabase CLI):
- `redeem-invite` — atomically creates a couple + couple_members rows,
  marks the invite used (replaces the FastAPI invite-redemption endpoint).
- `submit-snick` / `verify-snick` — submission intake and the AI
  verification + diamond crediting step (idempotent, using
  `source_event_id` exactly as your current `DiamondTransaction` does).
- `generate-daily-snicks` — replaces whatever currently schedules the 5
  daily snicks per couple; scheduled via `pg_cron` calling this function
  (or Supabase's native Cron Jobs feature) instead of your Redis-backed
  worker.
- `report-post` / moderation actions — keeps reporter identity and
  moderation status changes out of client hands.

## Phase 5 — Realtime
- Enable Realtime replication on `chat_messages` and `notifications`.
- Flutter: `ChatNotifier` subscribes to a Supabase Realtime channel instead
  of polling your FastAPI endpoint. Messages stay end-to-end encrypted —
  Realtime just pushes the same encrypted blob faster.

## Phase 6 — Flutter frontend cutover
- Add `supabase_flutter` to `pubspec.yaml`, initialize once in `main.dart`
  with your project URL + anon key.
- Go repository-by-repository (`auth_repository.dart`,
  `couple_repository.dart`, `chat_repository.dart`, etc.) replacing the
  `dio`/`ApiClient` calls with the equivalent Supabase client calls or
  `supabase.functions.invoke('function-name')` for the Edge Functions above.

## Phase 7 — Decommission Render
Only after Phase 1–6 are verified end-to-end on a test couple account:
delete the `snickylink-api` web service, `snickylink-db` Postgres, and
`snickylink-redis` instance on Render.

---
**This pass delivers Phase 1.** Next message, tell me which phase to do
next (Auth is the natural Phase 2, since nothing else works without it).
