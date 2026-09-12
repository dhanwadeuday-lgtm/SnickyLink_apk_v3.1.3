# SnickyLink backend hardening

Applied fixes:
- Corrected broken relative imports across `api`, `core`, and `services`.
- Fixed `VerificationService` missing `NotificationService` import.
- Added durable `DomainEvent` + `AuditLog` tables and `EventBus`.
- Emits `SNICK_SUBMITTED`, `SNICK_VERIFIED`, and `DIAMONDS_AWARDED` events.
- Added idempotent daily Snick assignment to prevent duplicate daily missions.
- Added real `UserDevice` storage and device register/unregister endpoints.
- Notification service now persists in-app notifications and sends FCM when configured.
- Redis leaderboard failures no longer make reward writes fail; the diamond ledger remains authoritative.
- Added `role` to `User` and changed admin authorization from hardcoded email to role.
- Added admin audit log endpoint.
- Added Search & Discovery endpoints and a Sticker model.
- Added PostgreSQL migration for new tables/columns.
- Added `backend/requirements.txt`.

Notes:
- `DomainEvent` is a durable event log/outbox-style backbone. A production deployment should run a dedicated worker for retries and external side effects rather than relying only on in-process handlers.
- Existing databases need the migration; `create_all()` does not alter existing columns.
- Set `FCM_SERVER_KEY` and register device tokens from the mobile client for push notifications.
