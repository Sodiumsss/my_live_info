-- 艺人
create table if not exists artists (
  id uuid primary key default gen_random_uuid(),
  canonical_name text unique not null,
  created_at timestamptz not null default now()
);

-- 别名
create table if not exists artist_aliases (
  alias text primary key,
  artist_id uuid not null references artists(id) on delete cascade,
  source text not null check (source in ('manual','llm')),
  created_at timestamptz not null default now()
);
create index if not exists idx_artist_aliases_artist on artist_aliases(artist_id);

-- 演唱会
create table if not exists concerts (
  id uuid primary key default gen_random_uuid(),
  artist_id uuid not null references artists(id) on delete cascade,
  city text not null,
  show_date date not null,
  venue text,
  status text not null check (status in ('unverified','verified')),
  sale_status text not null check (sale_status in ('announced','on_sale','sold_out','unknown')),
  sale_open_at timestamptz,
  source_url text,
  source_performance_id text,
  llm_sources jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  unique (artist_id, city, show_date)
);
create index if not exists idx_concerts_artist on concerts(artist_id);

-- 快照
create table if not exists concert_snapshots (
  id bigserial primary key,
  concert_id uuid not null references concerts(id) on delete cascade,
  status text not null,
  sale_status text not null,
  sale_open_at timestamptz,
  snapshot_at timestamptz not null default now()
);
create index if not exists idx_snapshots_concert on concert_snapshots(concert_id, snapshot_at desc);

-- 用户
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text,
  feishu_webhook text,
  notify_on_status_change boolean not null default true,
  created_at timestamptz not null default now()
);

-- 订阅
create table if not exists subscriptions (
  user_id uuid not null references users(id) on delete cascade,
  artist_id uuid not null references artists(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, artist_id)
);
create index if not exists idx_subscriptions_artist on subscriptions(artist_id);
