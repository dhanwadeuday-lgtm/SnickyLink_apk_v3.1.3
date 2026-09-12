I have provided you backend strategy and UI/UX mockup for color scheme and logo also.

PROJECT: SnickyLink — a gamified relationship app for couples (Flutter, Android target).

CONTEXT
- Flutter frontend already exists (Riverpod for state management, dio for
  networking, flutter_secure_storage for tokens). Features implemented:
  auth (login/signup), home dashboard, couple pairing via invite codes,
  end-to-end encrypted chat, a calendar, a memories/photo journal, a
  community feed with report/block moderation, and "Snicks" — daily
  paired challenge cards across four pillars (Growth, Connection, Impact,
  Wellness) that reward "diamonds" and track streaks.
- Backend strategy (attached separately): Migrating from a FastAPI backend
  (Render) to Supabase. Phase 1 (Postgres schema + RLS policies) is done —
  see supabase/migrations/0001_initial_schema.sql and
  SUPABASE_MIGRATION_PLAN.md. Auth, Storage, and the Edge Functions for
  business logic (pairing, diamond crediting, snick verification,
  moderation) are NOT built yet — those still live in the old FastAPI
  backend on Render for now. Don't assume Supabase Auth/Storage/Realtime
  work yet; the app should keep talking to the existing FastAPI endpoints
  until each phase of the migration is actually done.
- Brand system (attached separately): Copper Rose (#B8654A) as the sole
  accent color on white (day mode) / near-black (night mode) backgrounds.
  Instrument Serif italic for display/wordmarks; Satoshi (Plus Jakarta
  Sans substitute) for body UI. Logo: interlocking links forming a
  heart-shaped negative space; the Snicks sub-feature uses a tilted domino
  as its icon.

TASK
Continue building out the Android app to a beta-ready state, using the
color scheme, typography, and logo assets provided, and wiring every
screen to the real backend from the shared strategy doc (no mock/dummy
data in the final build).

REQUIREMENTS
1. Match the existing Flutter project's folder structure
   (lib/core, lib/features/<feature>/{data,domain,presentation}) — don't
   introduce a different architecture.
2. Apply the brand colors/fonts consistently across every screen you touch
   — reuse the existing AppTheme, don't hardcode colors inline.
3. Every network call goes through the pattern already established
   (repository -> notifier -> screen) and matches the shared backend
   strategy's actual field names/endpoints.
4. Keep chat end-to-end encryption intact — the app must never send
   plaintext message content to the backend.
5. Flag anything ambiguous (a screen with no corresponding backend
   endpoint, a mockup detail that conflicts with existing theme values)
   instead of guessing.

OUTPUT
- Working, compiling Flutter code for the requested screens/features.
- A short summary of what you built, what backend endpoints/tables each
  screen depends on, and anything still open.
- The end goal is a `flutter build apk --release` that installs cleanly
  for beta testers (not a Play Store submission yet).
