-- SnickyLink: Supabase Postgres schema (Phase 1 of Render -> Supabase migration)
-- Translated from backend/app/models/*.py (the FastAPI backend on Render).
--
-- Key differences from the FastAPI schema:
--   * `users` (id, email, hashed_password, role, suspended...) is replaced by
--     `profiles`, linked 1:1 to Supabase's built-in `auth.users`. Supabase
--     Auth owns email + password now -- we never store a password hash
--     ourselves.
--   * `password_reset_tokens` is dropped -- Supabase Auth's built-in
--     "forgot password" email flow replaces it entirely.
--   * Every table has Row Level Security enabled. Tables that encode
--     trust-sensitive logic (pairing, diamond crediting, submission
--     verification, moderation status) get NO client-facing write
--     policies at all -- only Postgres's `service_role` (used from Edge
--     Functions in Phase 4, never shipped in the app) can write to them.
--     This is the same trust boundary your FastAPI endpoints used to
--     enforce in Python; RLS is now the enforcement point instead.

-- =========================================================================
-- Extensions
-- =========================================================================
create extension if not exists "pgcrypto"; -- gen_random_uuid()

-- =========================================================================
-- Enums (mirroring the Python enums in backend/app/models)
-- =========================================================================
create type snick_pillar as enum ('growth', 'connection', 'impact', 'wellness');
create type daily_snick_state as enum ('LOCKED', 'ACTIVE', 'SUBMITTED', 'VERIFIED', 'FAILED', 'EXPIRED');
create type submission_type as enum ('text', 'photo', 'partner_confirmation');
create type reward_reason as enum ('snick_verified', 'streak_bonus');
create type post_visibility as enum ('private_couple', 'community');

-- =========================================================================
-- profiles (replaces `users`)
-- =========================================================================
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  role text not null default 'user',
  suspended boolean not null default false,
  suspended_at timestamptz,
  suspension_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Auto-create a profile row whenever someone signs up via Supabase Auth.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- =========================================================================
-- couples / couple_members / invites
-- =========================================================================
create table public.couples (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.couple_members (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  couple_id uuid not null references public.couples (id) on delete cascade,
  joined_at timestamptz not null default now()
);
create index idx_couple_members_couple on public.couple_members (couple_id);

create table public.invites (
  id uuid primary key default gen_random_uuid(),
  inviter_id uuid not null references public.profiles (id),
  token text not null unique,
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_invites_token on public.invites (token);

-- Helper: the caller's couple_id, or null if unpaired.
-- security definer so this can be safely called from policies on
-- couple_members itself without recursive-RLS issues.
create function public.current_couple_id()
returns uuid
language sql
stable
security definer set search_path = public
as $$
  select couple_id from public.couple_members where user_id = auth.uid() limit 1;
$$;

-- =========================================================================
-- chat_keys / chat_messages (E2EE -- server only ever sees ciphertext)
-- =========================================================================
create table public.chat_keys (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  public_key text not null,
  key_version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.media (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  owner_id uuid not null references public.profiles (id),
  storage_path text not null, -- Supabase Storage object path (bucket handled in app code)
  mime_type text not null,
  size_bytes integer not null,
  thumbnail_url text,
  processed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_media_couple on public.media (couple_id);

create table public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  sender_id uuid not null references public.profiles (id),
  encrypted_content text not null,
  expires_at timestamptz, -- null = permanent
  media_id uuid references public.media (id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_chat_messages_couple on public.chat_messages (couple_id);

-- =========================================================================
-- memories / calendar_events
-- =========================================================================
create table public.memories (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  creator_id uuid not null references public.profiles (id),
  media_id uuid not null references public.media (id),
  title text not null,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_memories_couple on public.memories (couple_id);

create table public.calendar_events (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  title text not null,
  description text,
  event_date timestamptz not null,
  is_all_day boolean not null default false,
  is_anniversary boolean not null default false,
  memory_id uuid references public.memories (id),
  created_by_user_id uuid not null references public.profiles (id),
  reminder_sent boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_calendar_events_couple on public.calendar_events (couple_id);
create index idx_calendar_events_date on public.calendar_events (event_date);

-- =========================================================================
-- community: posts / reactions / reports / blocks
-- =========================================================================
create table public.community_posts (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  creator_id uuid not null references public.profiles (id),
  content text not null,
  media_id uuid references public.media (id),
  visibility post_visibility not null default 'private_couple',
  moderation_status text not null default 'PENDING',
  moderation_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_community_posts_couple on public.community_posts (couple_id);
create index idx_community_posts_visibility on public.community_posts (visibility);

create table public.post_reactions (
  post_id uuid not null references public.community_posts (id) on delete cascade,
  user_id uuid not null references public.profiles (id),
  reaction_type text not null,
  primary key (post_id, user_id)
);

create table public.post_reports (
  id uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references public.profiles (id),
  post_id uuid not null references public.community_posts (id) on delete cascade,
  reason text not null,
  status text not null default 'PENDING',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.user_blocks (
  blocker_id uuid not null references public.profiles (id),
  blocked_id uuid not null references public.profiles (id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (blocker_id, blocked_id)
);

-- =========================================================================
-- snicks / daily_snicks / submissions / diamonds / stats
-- =========================================================================
create table public.snicks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text not null,
  category text,
  difficulty integer not null default 1,
  pillar snick_pillar not null,
  requires_photo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.daily_snicks (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  snick_id uuid not null references public.snicks (id),
  assigned_date timestamptz not null,
  order_index integer not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  state daily_snick_state not null default 'LOCKED',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_daily_snicks_couple on public.daily_snicks (couple_id);
create index idx_daily_snicks_date on public.daily_snicks (assigned_date);

create table public.snick_submissions (
  id uuid primary key default gen_random_uuid(),
  daily_snick_id uuid not null references public.daily_snicks (id) on delete cascade,
  submitted_by_user_id uuid not null references public.profiles (id),
  submission_type submission_type not null,
  content text,
  media_id uuid references public.media (id),
  submitted_at timestamptz not null default now(),
  confirmed_by_user_id uuid references public.profiles (id),
  confirmed_at timestamptz,
  status text,
  ai_confidence_score double precision,
  ai_verification_result text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_snick_submissions_daily_snick on public.snick_submissions (daily_snick_id);

create table public.diamond_transactions (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples (id) on delete cascade,
  user_id uuid references public.profiles (id),
  amount integer not null,
  reason reward_reason not null,
  source_event_id text not null unique, -- idempotency key, unchanged from FastAPI model
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_diamond_transactions_couple on public.diamond_transactions (couple_id);

create table public.couple_stats (
  couple_id uuid primary key references public.couples (id) on delete cascade,
  total_diamonds integer not null default 0,
  snicks_completed integer not null default 0,
  completion_rate double precision not null default 0.0,
  current_streak integer not null default 0,
  longest_streak integer not null default 0,
  last_updated_at timestamptz not null default now()
);

-- =========================================================================
-- gamification: levels / badges
-- =========================================================================
create table public.levels (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  threshold integer not null unique,
  sort_order integer not null default 0
);

create table public.user_levels (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  level_id uuid not null references public.levels (id),
  awarded_at timestamptz not null default now()
);

create table public.badges (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  criteria text not null,
  threshold integer not null default 0,
  is_active boolean not null default true
);

create table public.user_badges (
  user_id uuid not null references public.profiles (id) on delete cascade,
  badge_id uuid not null references public.badges (id),
  awarded_at timestamptz not null default now(),
  primary key (user_id, badge_id)
);

-- =========================================================================
-- stickers / devices / notifications
-- =========================================================================
create table public.stickers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  image_url text not null,
  category text,
  is_active boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.user_devices (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  device_token text not null unique,
  platform text not null default 'unknown',
  is_active boolean not null default true,
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (user_id, device_token)
);
create index idx_user_devices_user on public.user_devices (user_id);

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  title text not null,
  message text not null,
  type text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_notifications_user on public.notifications (user_id);

-- =========================================================================
-- analytics_events / audit_logs
-- (domain_events / event_deliveries from the FastAPI event-bus are
--  intentionally NOT ported -- that bus is being replaced by Edge
--  Functions + pg_cron in Phase 4, so there's no consumer left to read
--  them. audit_logs is kept for compliance/audit-trail purposes.)
-- =========================================================================
create table public.analytics_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles (id),
  couple_id uuid references public.couples (id),
  event_name text not null,
  properties jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_analytics_events_user on public.analytics_events (user_id);
create index idx_analytics_events_couple on public.analytics_events (couple_id);

create table public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid,
  action text not null,
  entity_type text,
  entity_id text,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- =========================================================================
-- Row Level Security
-- =========================================================================
alter table public.profiles enable row level security;
alter table public.couples enable row level security;
alter table public.couple_members enable row level security;
alter table public.invites enable row level security;
alter table public.chat_keys enable row level security;
alter table public.media enable row level security;
alter table public.chat_messages enable row level security;
alter table public.memories enable row level security;
alter table public.calendar_events enable row level security;
alter table public.community_posts enable row level security;
alter table public.post_reactions enable row level security;
alter table public.post_reports enable row level security;
alter table public.user_blocks enable row level security;
alter table public.snicks enable row level security;
alter table public.daily_snicks enable row level security;
alter table public.snick_submissions enable row level security;
alter table public.diamond_transactions enable row level security;
alter table public.couple_stats enable row level security;
alter table public.levels enable row level security;
alter table public.user_levels enable row level security;
alter table public.badges enable row level security;
alter table public.user_badges enable row level security;
alter table public.stickers enable row level security;
alter table public.user_devices enable row level security;
alter table public.notifications enable row level security;
alter table public.analytics_events enable row level security;
alter table public.audit_logs enable row level security;

-- --- profiles: see your own + your partner's; edit only your own row ---
create policy "profiles_select_self_or_partner"
  on public.profiles for select
  using (id = auth.uid() or id in (
    select user_id from public.couple_members where couple_id = public.current_couple_id()
  ));
create policy "profiles_update_self"
  on public.profiles for update
  using (id = auth.uid())
  with check (id = auth.uid());
-- No client insert/delete policy: rows are created only by the
-- handle_new_user() trigger (security definer) on signup.

-- --- couples / couple_members / invites: read-only to clients ---
-- Pairing must go through the Phase 4 `redeem-invite` Edge Function
-- (using the service role), never a direct client insert -- otherwise a
-- user could insert themselves into an arbitrary couple_id.
create policy "couples_select_members"
  on public.couples for select
  using (id = public.current_couple_id());

create policy "couple_members_select_self_or_partner"
  on public.couple_members for select
  using (user_id = auth.uid() or couple_id = public.current_couple_id());

create policy "invites_select_own"
  on public.invites for select
  using (inviter_id = auth.uid());
-- Redeeming (reading someone else's invite by token, then marking it
-- used) also happens inside the Edge Function via service role, since it
-- inherently requires reading a row you don't "own" yet.

-- --- chat_keys: only the owner can read/write their own public key ---
create policy "chat_keys_select_self_or_partner"
  on public.chat_keys for select
  using (user_id = auth.uid() or user_id in (
    select user_id from public.couple_members where couple_id = public.current_couple_id()
  ));
create policy "chat_keys_upsert_self"
  on public.chat_keys for insert
  with check (user_id = auth.uid());
create policy "chat_keys_update_self"
  on public.chat_keys for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- --- media: couple members can read; owner can insert their own ---
create policy "media_select_couple"
  on public.media for select
  using (couple_id = public.current_couple_id());
create policy "media_insert_own"
  on public.media for insert
  with check (owner_id = auth.uid() and couple_id = public.current_couple_id());

-- --- chat_messages: couple members read; sender inserts their own ---
create policy "chat_messages_select_couple"
  on public.chat_messages for select
  using (couple_id = public.current_couple_id());
create policy "chat_messages_insert_own"
  on public.chat_messages for insert
  with check (sender_id = auth.uid() and couple_id = public.current_couple_id());

-- --- memories: couple members read; either partner can create ---
create policy "memories_select_couple"
  on public.memories for select
  using (couple_id = public.current_couple_id());
create policy "memories_insert_own"
  on public.memories for insert
  with check (creator_id = auth.uid() and couple_id = public.current_couple_id());

-- --- calendar_events: couple members read/write ---
create policy "calendar_events_select_couple"
  on public.calendar_events for select
  using (couple_id = public.current_couple_id());
create policy "calendar_events_insert_own"
  on public.calendar_events for insert
  with check (created_by_user_id = auth.uid() and couple_id = public.current_couple_id());
create policy "calendar_events_update_couple"
  on public.calendar_events for update
  using (couple_id = public.current_couple_id())
  with check (couple_id = public.current_couple_id());

-- --- community_posts: own-couple posts always visible to the couple;
--     COMMUNITY-visibility posts visible to everyone once approved ---
create policy "community_posts_select"
  on public.community_posts for select
  using (
    couple_id = public.current_couple_id()
    or (visibility = 'community' and moderation_status = 'APPROVED')
  );
create policy "community_posts_insert_own"
  on public.community_posts for insert
  with check (creator_id = auth.uid() and couple_id = public.current_couple_id());
-- moderation_status changes are service-role only (Phase 4 moderation
-- Edge Function) -- no client update policy.

create policy "post_reactions_select"
  on public.post_reactions for select
  using (true); -- reactions are only meaningful on already-visible posts
create policy "post_reactions_insert_own"
  on public.post_reactions for insert
  with check (user_id = auth.uid());
create policy "post_reactions_delete_own"
  on public.post_reactions for delete
  using (user_id = auth.uid());

create policy "post_reports_insert_own"
  on public.post_reports for insert
  with check (reporter_id = auth.uid());
create policy "post_reports_select_own"
  on public.post_reports for select
  using (reporter_id = auth.uid());

create policy "user_blocks_select_own"
  on public.user_blocks for select
  using (blocker_id = auth.uid());
create policy "user_blocks_insert_own"
  on public.user_blocks for insert
  with check (blocker_id = auth.uid());
create policy "user_blocks_delete_own"
  on public.user_blocks for delete
  using (blocker_id = auth.uid());

-- --- snicks: public reference data, readable by any signed-in user ---
create policy "snicks_select_all"
  on public.snicks for select
  using (auth.role() = 'authenticated');

-- --- daily_snicks: couple members read only (assignment is Edge Function/service role) ---
create policy "daily_snicks_select_couple"
  on public.daily_snicks for select
  using (couple_id = public.current_couple_id());

-- --- snick_submissions: couple can read; submitter can insert.
--     Verification/approval fields are service-role only. ---
create policy "snick_submissions_select_couple"
  on public.snick_submissions for select
  using (daily_snick_id in (
    select id from public.daily_snicks where couple_id = public.current_couple_id()
  ));
create policy "snick_submissions_insert_own"
  on public.snick_submissions for insert
  with check (
    submitted_by_user_id = auth.uid()
    and daily_snick_id in (
      select id from public.daily_snicks where couple_id = public.current_couple_id()
    )
  );

-- --- diamond_transactions / couple_stats: read-only to clients ---
create policy "diamond_transactions_select_couple"
  on public.diamond_transactions for select
  using (couple_id = public.current_couple_id());
create policy "couple_stats_select_couple"
  on public.couple_stats for select
  using (couple_id = public.current_couple_id());

-- --- levels / badges: public reference data ---
create policy "levels_select_all"
  on public.levels for select
  using (auth.role() = 'authenticated');
create policy "badges_select_all"
  on public.badges for select
  using (auth.role() = 'authenticated');
create policy "user_levels_select_self_or_partner"
  on public.user_levels for select
  using (user_id = auth.uid() or user_id in (
    select user_id from public.couple_members where couple_id = public.current_couple_id()
  ));
create policy "user_badges_select_self_or_partner"
  on public.user_badges for select
  using (user_id = auth.uid() or user_id in (
    select user_id from public.couple_members where couple_id = public.current_couple_id()
  ));

-- --- stickers: public reference data ---
create policy "stickers_select_all"
  on public.stickers for select
  using (auth.role() = 'authenticated');

-- --- user_devices: only the owning user ---
create policy "user_devices_select_own"
  on public.user_devices for select
  using (user_id = auth.uid());
create policy "user_devices_insert_own"
  on public.user_devices for insert
  with check (user_id = auth.uid());
create policy "user_devices_update_own"
  on public.user_devices for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid());
create policy "user_devices_delete_own"
  on public.user_devices for delete
  using (user_id = auth.uid());

-- --- notifications: only the owning user; server (service role) creates them ---
create policy "notifications_select_own"
  on public.notifications for select
  using (user_id = auth.uid());
create policy "notifications_update_own"
  on public.notifications for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid()); -- e.g. marking is_read = true

-- --- analytics_events: client can log its own events; no read-back needed ---
create policy "analytics_events_insert_own"
  on public.analytics_events for insert
  with check (user_id = auth.uid() or user_id is null);

-- --- audit_logs: no client access at all (service role / dashboard only) ---
-- Intentionally no policies -- RLS with zero policies means zero client
-- access, which is what we want here.

-- =========================================================================
-- NOTE ON WRITE PATHS WITH NO CLIENT POLICY ABOVE
-- The following are correct on purpose, not omissions -- they must go
-- through Phase 4 Edge Functions using the service role key, exactly
-- mirroring which endpoints your FastAPI backend kept server-authoritative:
--   couples / couple_members  (insert)      -> redeem-invite function
--   invites                   (update used_at) -> redeem-invite function
--   daily_snicks               (insert/update) -> generate-daily-snicks, verify-snick
--   snick_submissions          (update: status, confirmed_*, ai_*) -> verify-snick
--   diamond_transactions        (insert)     -> verify-snick / streak-bonus function
--   couple_stats                (update)     -> verify-snick / streak-bonus function
--   community_posts             (moderation_status update) -> moderate-post function
--   post_reports                (status update) -> moderate-post function
--   user_levels / user_badges   (insert)     -> award-level / award-badge function
--   notifications                (insert)    -> whichever function triggers it
-- =========================================================================
