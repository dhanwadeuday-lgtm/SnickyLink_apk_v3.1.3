# SnickyLink Fixed V1

Implemented against the uploaded `snickylink_fixed(1).zip`.

## V1 changes
1. Durable outbox worker with row locking, per-handler isolation, retries, stale-claim recovery and dead-letter state.
2. AI photo verification moved out of the HTTP request into `AI_VERIFICATION_REQUESTED`.
3. Text and partner-confirmation submissions enter partner review; partner decision publishes `SNICK_VERIFIED` on approval.
4. Media validation + Pillow thumbnails via `MEDIA_UPLOADED`.
5. Automatic Memory creation for verified submissions carrying a media UUID.
6. Community moderation via AI; public posts remain hidden until approved. Resolved-report threshold auto-suspends users.
7. Levels and badges with `DIAMONDS_AWARDED -> XP_AWARDED -> LEVEL_UP/BADGE_AWARDED`.
8. Stats, leaderboard, notifications and streak updates are separate event consumers.
9. `NOTIFICATION_REQUESTED -> NOTIFICATION_SENT`.
10. Calendar reminder scheduler.
11. Chat `since_timestamp` polling.
12. Login can register a device token; logout deactivates device tokens.
13. Analytics funnel endpoint.
14. Added deployment files and tests.

## Event map
SNICK_SUBMITTED -> AI_VERIFICATION_REQUESTED (photo) -> SNICK_VERIFIED
-> DIAMONDS_AWARDED
-> XP_AWARDED
-> LEVEL_UP / BADGE_AWARDED
-> STATS_UPDATED
-> LEADERBOARD_UPDATED
-> NOTIFICATION_REQUESTED
-> NOTIFICATION_SENT

SNICK_VERIFIED -> MEMORY_CREATED (when media is linked)
SNICK_VERIFIED -> STREAK_UPDATED
MEDIA_UPLOADED -> thumbnail processing
COMMUNITY_POSTED -> COMMUNITY_POST_APPROVED
REPORT_RESOLVED -> suspension check
CALENDAR_REMINDER_DUE -> NOTIFICATION_REQUESTED

## Explicit scope
OTP/password recovery is intentionally not implemented.
WebSocket realtime chat is intentionally out of scope; polling is supported.
The supplied frontend contains Dart feature code but does not contain a Flutter `pubspec.yaml`, `android/` project, or application entry point, so an APK cannot be truthfully claimed as compiled from this archive. The backend is packaged for deployment.
