-- SnickyLink production hardening / V1.1 migration. Idempotent for PostgreSQL.
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason VARCHAR;
ALTER TABLE media ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;
ALTER TABLE media ADD COLUMN IF NOT EXISTS processed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS moderation_status VARCHAR NOT NULL DEFAULT 'PENDING';
ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS moderation_reason VARCHAR;
ALTER TABLE calendar_events ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'PENDING';
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ;
ALTER TABLE domain_events ADD COLUMN IF NOT EXISTS dead_lettered_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS event_deliveries (
  id UUID PRIMARY KEY,
  event_id UUID NOT NULL REFERENCES domain_events(id) ON DELETE CASCADE,
  handler_name VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'DELIVERED',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  next_attempt_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  CONSTRAINT uq_event_handler UNIQUE(event_id, handler_name)
);
CREATE INDEX IF NOT EXISTS ix_event_deliveries_retry ON event_deliveries(status, next_attempt_at);

CREATE TABLE IF NOT EXISTS levels (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL UNIQUE,
  threshold INTEGER NOT NULL UNIQUE,
  sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS user_levels (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  level_id UUID NOT NULL REFERENCES levels(id),
  awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS badges (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL UNIQUE,
  criteria TEXT NOT NULL,
  threshold INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS user_badges (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id UUID NOT NULL REFERENCES badges(id),
  awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(user_id, badge_id)
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_password_reset_active ON password_reset_tokens(user_id, expires_at, used_at);

-- Baseline gamification thresholds.
INSERT INTO levels (id,name,threshold,sort_order) VALUES
(gen_random_uuid(),'Starter',0,0),
(gen_random_uuid(),'Spark',50,50),
(gen_random_uuid(),'Flame',150,150),
(gen_random_uuid(),'Soulmate',500,500),
(gen_random_uuid(),'Forever',1000,1000)
ON CONFLICT DO NOTHING;
INSERT INTO badges (id,name,threshold,criteria) VALUES
(gen_random_uuid(),'First Snick',10,'Earn at least 10 diamonds'),
(gen_random_uuid(),'Century',100,'Earn at least 100 diamonds'),
(gen_random_uuid(),'Committed',500,'Earn at least 500 diamonds')
ON CONFLICT DO NOTHING;

-- Upgrade an already-created event_deliveries table from the earlier V1 schema.
ALTER TABLE event_deliveries ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'DELIVERED';
ALTER TABLE event_deliveries ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE event_deliveries ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE event_deliveries ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ;
ALTER TABLE event_deliveries ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS uq_event_handler ON event_deliveries(event_id, handler_name);
