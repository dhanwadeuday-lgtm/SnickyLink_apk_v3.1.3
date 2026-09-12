# SnickyLink Backend — Production Audit V1.1

This pass is based on the uploaded SnickyLink cross-platform V1 codebase and the 22-engine reconciliation supplied in the project discussion.

## Engine reconciliation

1. Auth & Identity — password/JWT/device registration; added refresh-token endpoint and email password-reset flow. OTP remains intentionally out of scope.
2. Couple — invites, pairing, membership present.
3. Snick — daily assignment, weighted selection, windows and state machine present.
4. Personalization — weighted MVP rules present.
5. Verification — photo AI + human fallback; partner confirmation; text requires partner confirmation.
6. AI — verification/moderation run from durable background events rather than the HTTP request path.
7. Diamonds/Gamification — idempotent ledger, levels and badges.
8. Leaderboard — Redis projection via LEADERBOARD_UPDATED.
9. Stats — event-driven projection via STATS_UPDATED.
10. E2EE Chat — encrypted blob storage, pagination and `since_timestamp`; WebSockets remain out of scope.
11. Disappearing Messages — expires_at cleanup job.
12. Media — Pillow server-side validation, pixel/size limits, async thumbnail processing from MEDIA_UPLOADED.
13. Memory — verified Snick media and private chat photos automatically create memories.
14. Calendar — events plus scheduled reminder event.
15. Notifications — durable notification events plus FCM integration; calendar reminders fan out to both couple members.
16. Community — visibility rules and moderation gate.
17. Moderation/Safety — AI moderation flags content; resolved-report threshold auto-suspends users; suspended users are blocked from write flows through the active-user dependency.
18. Search/Discovery — search endpoints present.
19. Stickers/Emoji — sticker model and discovery endpoint present.
20. Analytics — event capture and funnel summary endpoint present.
21. Audit/Event — durable outbox, handler-level delivery records, retries, dead-lettering, granular chain.
22. Admin — role-based admin and audit logging.

## Event map

`SNICK_SUBMITTED`
→ `AI_VERIFICATION_REQUESTED` (photo only)
→ `SNICK_VERIFIED`
→ `DIAMONDS_AWARDED`
→ `XP_AWARDED`
→ `LEVEL_UP` / `BADGE_AWARDED`
→ `STATS_UPDATED`
→ `STREAK_UPDATED`
→ `LEADERBOARD_UPDATED`
→ `NOTIFICATION_REQUESTED`
→ `NOTIFICATION_SENT`

Additionally:

`SNICK_VERIFIED` → `MEMORY_CREATED` when a media reference exists.

`MEDIA_UPLOADED` → asynchronous server-side validation + thumbnail generation.

`PHOTO_SHARED` → `MEMORY_CREATED` for private chat media.

`COMMUNITY_POSTED` → automated moderation → `COMMUNITY_POST_APPROVED` when safe.

`REPORT_RESOLVED` → suspension threshold check → `USER_SUSPENDED` when threshold is reached.

`CALENDAR_REMINDER_DUE` → notification fan-out → `NOTIFICATION_SENT`.

## Production process model

For a single development process, the API scheduler can run jobs in-process.

For production/multiple API replicas:

- API containers: `RUN_SCHEDULER=false`, `RUN_EVENT_WORKER=false`
- One or more worker containers: `python -m app.worker`
- PostgreSQL provides row-locking/`SKIP LOCKED` event claims.
- Redis provides leaderboard projections.

## Required production configuration

Set strong `SECRET_KEY` and `MEDIA_SIGNING_KEY`, PostgreSQL, Redis, S3/R2, AI provider credentials, CORS origins, and FCM credentials. Configure SMTP if password-reset emails are required.

Run migrations in order:

- `001_architecture_hardening.sql`
- `002_production_hardening.sql`

Do not enable `AUTO_CREATE_TABLES` in production.

## Validation performed

Python compilation: PASS.

Automated tests: **12 passed**.
