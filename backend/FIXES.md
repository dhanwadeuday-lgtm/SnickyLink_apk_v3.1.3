# SnickyLink backend — event worker + verification pass

## Implemented in this pass

### 1. Durable asynchronous event worker
- `EventBus.publish()` is now **outbox-only**: it persists `domain_events` + `audit_logs` and never executes handlers inside the request transaction.
- Added `app/services/event_worker.py`.
- APScheduler polls pending events every 10 seconds.
- PostgreSQL `FOR UPDATE SKIP LOCKED` claims events safely across concurrent API processes.
- Per-handler `try/except` isolation prevents one consumer failure from rolling back unrelated consumers.
- Failed handlers retry with exponential backoff up to 5 attempts.
- Events that repeatedly fail, or have no registered consumer, enter `DEAD_LETTER` with `last_error` and `dead_lettered_at` for inspection/replay tooling.
- Stale `PROCESSING` events are eligible for recovery after 10 minutes.

### 2. Verification
- Photo/AI approval publishes `SNICK_VERIFIED` to the durable event bus; diamond awarding is no longer performed inline.
- Partner review now has a real decision flow:
  - `POST /snicks/submissions/{submission_id}/decision` with `{ "approved": true|false }`
  - Approval sets the daily snick to `VERIFIED` and publishes `SNICK_VERIFIED`.
  - Rejection sets the submission to `REJECTED` and daily snick to `FAILED`.
  - Existing `/confirm` remains as a backwards-compatible approval endpoint.
- A `SNICK_VERIFIED` consumer awards diamonds idempotently through the existing ledger.
- **Text verification is intentionally not finalized yet** because the business rule is ambiguous (minimum length / partner review / timeout / AI auto-approval). See the pending question in the response.

## Domain events added/consumed in this pass

| Event | Produced by | Consumed by |
|---|---|---|
| `SNICK_SUBMITTED` | `SnickService.submit_snick` | Outbox worker (currently no consumer; retained/audited) |
| `SNICK_VERIFIED` | AI verification + partner approval | Diamond reward handler |
| `DIAMONDS_AWARDED` | `RewardService.award_diamonds` | Future gamification/levels-badges pass |

## Database migration
Run the updated `migrations/001_architecture_hardening.sql` against an existing database. It adds event status, retry, error, processing, and dead-letter columns.

## Testing
The extracted project had no existing test suite, so no pre-existing tests were modified. Python syntax was validated with `python -m compileall`.
