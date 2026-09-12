-- SnickyLink architecture hardening
-- Run against an existing PostgreSQL database before/after deploying the patched app.
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user';

CREATE TABLE IF NOT EXISTS user_devices (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  device_token VARCHAR NOT NULL UNIQUE,
  platform VARCHAR NOT NULL DEFAULT 'unknown',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_seen_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT uq_user_device_token UNIQUE (user_id, device_token)
);
CREATE INDEX IF NOT EXISTS ix_user_devices_user_id ON user_devices(user_id);

CREATE TABLE IF NOT EXISTS domain_events (
  id UUID PRIMARY KEY,
  event_type VARCHAR NOT NULL,
  aggregate_type VARCHAR NOT NULL,
  aggregate_id VARCHAR NOT NULL,
  actor_user_id UUID,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  processed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_domain_events_event_type ON domain_events(event_type);
CREATE INDEX IF NOT EXISTS ix_domain_events_aggregate_id ON domain_events(aggregate_id);
CREATE INDEX IF NOT EXISTS ix_domain_events_processed ON domain_events(processed);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY,
  actor_user_id UUID,
  action VARCHAR NOT NULL,
  entity_type VARCHAR,
  entity_id VARCHAR,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs(entity_id);

CREATE TABLE IF NOT EXISTS stickers (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  image_url VARCHAR NOT NULL,
  category VARCHAR,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Durable event-worker fields. Existing rows remain pending and will be delivered.
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'PENDING';
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS dead_lettered_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_domain_events_status_dispatch ON domain_events(status, processed, next_attempt_at);
