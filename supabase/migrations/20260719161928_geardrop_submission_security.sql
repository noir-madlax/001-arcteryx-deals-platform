-- Harden public submission paths used by GearDrop's app and static website.
-- Direct table access stays private; anonymous clients can only call validated,
-- rate-limited RPC functions with server-derived product metadata.

create schema if not exists private;
revoke all on schema private from public;
revoke all on schema private from anon, authenticated;

create table if not exists private.public_request_limit_secrets (
  id smallint primary key check (id = 1),
  secret bytea not null,
  created_at timestamptz not null default pg_catalog.now()
);

insert into private.public_request_limit_secrets (id, secret)
values (1, extensions.gen_random_bytes(32))
on conflict (id) do nothing;

create table if not exists private.public_request_limits (
  bucket text not null,
  subject_hash text not null,
  request_count integer not null default 1 check (request_count > 0),
  window_started_at timestamptz not null default pg_catalog.now(),
  primary key (bucket, subject_hash)
);

revoke all on table private.public_request_limit_secrets from public, anon, authenticated;
revoke all on table private.public_request_limits from public, anon, authenticated;

create or replace function private.consume_public_request_quota(
  p_bucket text,
  p_subject text,
  p_limit integer,
  p_window interval
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_secret bytea;
  v_subject_hash text;
  v_request_count integer;
begin
  if p_bucket is null or p_subject is null or p_limit < 1 or p_window <= interval '0 seconds' then
    raise exception using errcode = '22023', message = 'invalid_rate_limit_configuration';
  end if;

  select secret
    into strict v_secret
    from private.public_request_limit_secrets
   where id = 1;

  v_subject_hash := pg_catalog.encode(
    extensions.hmac(
      pg_catalog.convert_to(pg_catalog.left(p_subject, 512), 'UTF8'),
      v_secret,
      'sha256'
    ),
    'hex'
  );

  -- Bound storage of pseudonymous abuse-prevention fingerprints.
  delete from private.public_request_limits
   where window_started_at < pg_catalog.now() - interval '1 day';

  insert into private.public_request_limits as limits (
    bucket,
    subject_hash,
    request_count,
    window_started_at
  )
  values (p_bucket, v_subject_hash, 1, pg_catalog.now())
  on conflict (bucket, subject_hash) do update
    set request_count = case
          when limits.window_started_at <= pg_catalog.now() - p_window then 1
          else limits.request_count + 1
        end,
        window_started_at = case
          when limits.window_started_at <= pg_catalog.now() - p_window then pg_catalog.now()
          else limits.window_started_at
        end
  returning request_count into v_request_count;

  return v_request_count <= p_limit;
end;
$$;

revoke all on function private.consume_public_request_quota(text, text, integer, interval) from public, anon, authenticated;

-- Keep the timestamped migration chain self-contained. Older installations may
-- already have this table from dealers/supabase_migration_price_alerts.sql;
-- clean environments must not depend on that manually executed SQL file.
create table if not exists public.price_alerts (
  id serial primary key,
  email text not null,
  sku_id text not null,
  target_price numeric,
  last_price_seen numeric,
  currency text,
  region text,
  product_name text,
  product_url text,
  image_url text,
  notified_at timestamptz,
  unsubscribe_token text unique not null,
  created_at timestamptz default pg_catalog.now()
);

create index if not exists price_alerts_sku_idx
  on public.price_alerts (sku_id);
create index if not exists price_alerts_email_idx
  on public.price_alerts (email);
create index if not exists price_alerts_pending_idx
  on public.price_alerts (sku_id)
  where notified_at is null;

-- Normalize existing rows before installing the active-subscription uniqueness guard.
update public.price_alerts
   set email = pg_catalog.lower(pg_catalog.btrim(email))
 where email is distinct from pg_catalog.lower(pg_catalog.btrim(email));

with ranked as (
  select id,
         pg_catalog.row_number() over (
           partition by pg_catalog.lower(email), sku_id
           order by created_at desc nulls last, id desc
         ) as position
    from public.price_alerts
   where notified_at is null
)
delete from public.price_alerts alerts
 using ranked
 where alerts.id = ranked.id
   and ranked.position > 1;

create unique index if not exists price_alerts_one_active_per_email_sku_idx
  on public.price_alerts ((pg_catalog.lower(email)), sku_id)
  where notified_at is null;

alter table public.price_alerts enable row level security;
drop policy if exists anon_insert on public.price_alerts;
drop policy if exists public_insert on public.price_alerts;
drop policy if exists authenticated_insert on public.price_alerts;
drop policy if exists service_role_full on public.price_alerts;

revoke all on table public.price_alerts from public, anon, authenticated;
grant select, insert, update, delete on table public.price_alerts to service_role;
revoke all on sequence public.price_alerts_id_seq from public, anon, authenticated;
grant usage, select, update on sequence public.price_alerts_id_seq to service_role;

create or replace function public.register_price_alert(
  p_email text,
  p_sku_id text,
  p_target_price numeric default null
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email text := pg_catalog.lower(pg_catalog.btrim(p_email));
  v_sku_id text := pg_catalog.btrim(p_sku_id);
  v_headers jsonb := coalesce(
    nullif(pg_catalog.current_setting('request.headers', true), ''),
    '{}'
  )::jsonb;
  v_ip text;
  v_product public.products%rowtype;
  v_alert_id integer;
begin
  if v_email is null
     or pg_catalog.char_length(v_email) > 254
     or v_email !~* '^[A-Z0-9.!#$%&''*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$' then
    raise exception using errcode = '22023', message = 'invalid_email';
  end if;

  if v_sku_id is null or v_sku_id = '' or pg_catalog.char_length(v_sku_id) > 200 then
    raise exception using errcode = '22023', message = 'invalid_sku';
  end if;

  if p_target_price is not null and (p_target_price <= 0 or p_target_price > 1000000) then
    raise exception using errcode = '22023', message = 'invalid_target_price';
  end if;

  v_ip := coalesce(
    nullif(pg_catalog.btrim(pg_catalog.split_part(v_headers ->> 'x-forwarded-for', ',', 1)), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'cf-connecting-ip'), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'x-real-ip'), ''),
    'unknown:' || v_email
  );

  if not private.consume_public_request_quota('price-alert-ip', v_ip, 10, interval '15 minutes')
     or not private.consume_public_request_quota('price-alert-email', v_email, 5, interval '15 minutes') then
    raise sqlstate 'PT429' using message = 'too_many_requests';
  end if;

  select *
    into v_product
    from public.products
   where sku_id = v_sku_id
     and status = 'active';

  if not found then
    raise exception using errcode = '22023', message = 'product_not_available';
  end if;

  if p_target_price is not null and p_target_price >= v_product.sale_price then
    raise exception using errcode = '22023', message = 'target_must_be_below_current_price';
  end if;

  insert into public.price_alerts as alerts (
    email,
    sku_id,
    target_price,
    last_price_seen,
    currency,
    region,
    product_name,
    product_url,
    image_url,
    unsubscribe_token,
    created_at
  )
  values (
    v_email,
    v_product.sku_id,
    p_target_price,
    v_product.sale_price,
    v_product.currency,
    v_product.region,
    coalesce(v_product.full_name, v_product.model, v_product.sku_id),
    coalesce(v_product.url, ''),
    coalesce(v_product.image_url, ''),
    pg_catalog.encode(extensions.gen_random_bytes(32), 'hex'),
    pg_catalog.now()
  )
  on conflict ((pg_catalog.lower(email)), sku_id) where notified_at is null
  do update set
    target_price = excluded.target_price,
    last_price_seen = excluded.last_price_seen,
    currency = excluded.currency,
    region = excluded.region,
    product_name = excluded.product_name,
    product_url = excluded.product_url,
    image_url = excluded.image_url,
    unsubscribe_token = excluded.unsubscribe_token,
    created_at = excluded.created_at
  returning id into v_alert_id;

  return v_alert_id;
end;
$$;

revoke all on function public.register_price_alert(text, text, numeric) from public;
grant execute on function public.register_price_alert(text, text, numeric) to anon, authenticated, service_role;

create or replace function public.unsubscribe_alert(token text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_token text := pg_catalog.btrim(token);
  v_headers jsonb := coalesce(
    nullif(pg_catalog.current_setting('request.headers', true), ''),
    '{}'
  )::jsonb;
  v_ip text;
  v_deleted integer;
begin
  if v_token is null
     or pg_catalog.char_length(v_token) > 64
     or v_token !~* '^(?:[0-9a-f]{64}|[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$' then
    return 0;
  end if;

  v_ip := coalesce(
    nullif(pg_catalog.btrim(pg_catalog.split_part(v_headers ->> 'x-forwarded-for', ',', 1)), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'cf-connecting-ip'), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'x-real-ip'), ''),
    'unknown:' || pg_catalog.left(v_token, 12)
  );

  if not private.consume_public_request_quota('price-alert-unsubscribe-ip', v_ip, 30, interval '1 hour') then
    raise sqlstate 'PT429' using message = 'too_many_requests';
  end if;

  delete from public.price_alerts where unsubscribe_token = v_token;
  get diagnostics v_deleted = row_count;
  return v_deleted;
end;
$$;

revoke all on function public.unsubscribe_alert(text) from public;
grant execute on function public.unsubscribe_alert(text) to anon, authenticated, service_role;

create table if not exists public.support_requests (
  id uuid primary key default extensions.gen_random_uuid(),
  email text not null,
  subject text not null,
  message text not null,
  locale text not null default 'en',
  status text not null default 'new' check (status in ('new', 'in_progress', 'resolved', 'closed')),
  created_at timestamptz not null default pg_catalog.now(),
  updated_at timestamptz not null default pg_catalog.now()
);

create index if not exists support_requests_status_created_idx
  on public.support_requests (status, created_at desc);

alter table public.support_requests enable row level security;
revoke all on table public.support_requests from public, anon, authenticated;
grant select, insert, update, delete on table public.support_requests to service_role;

create or replace function public.submit_support_request(
  p_email text,
  p_subject text,
  p_message text,
  p_locale text default 'en',
  p_website text default ''
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email text := pg_catalog.lower(pg_catalog.btrim(p_email));
  v_subject text := pg_catalog.btrim(p_subject);
  v_message text := pg_catalog.btrim(p_message);
  v_locale text := coalesce(nullif(pg_catalog.btrim(p_locale), ''), 'en');
  v_headers jsonb := coalesce(
    nullif(pg_catalog.current_setting('request.headers', true), ''),
    '{}'
  )::jsonb;
  v_ip text;
  v_request_id uuid;
begin
  -- Honeypot submissions receive a non-actionable success response.
  if coalesce(pg_catalog.btrim(p_website), '') <> '' then
    return extensions.gen_random_uuid();
  end if;

  if v_email is null
     or pg_catalog.char_length(v_email) > 254
     or v_email !~* '^[A-Z0-9.!#$%&''*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$' then
    raise exception using errcode = '22023', message = 'invalid_email';
  end if;

  if v_subject is null or pg_catalog.char_length(v_subject) < 3 or pg_catalog.char_length(v_subject) > 120 then
    raise exception using errcode = '22023', message = 'invalid_subject';
  end if;

  if v_message is null or pg_catalog.char_length(v_message) < 10 or pg_catalog.char_length(v_message) > 4000 then
    raise exception using errcode = '22023', message = 'invalid_message';
  end if;

  if pg_catalog.char_length(v_locale) > 24 or v_locale !~ '^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$' then
    v_locale := 'en';
  end if;

  v_ip := coalesce(
    nullif(pg_catalog.btrim(pg_catalog.split_part(v_headers ->> 'x-forwarded-for', ',', 1)), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'cf-connecting-ip'), ''),
    nullif(pg_catalog.btrim(v_headers ->> 'x-real-ip'), ''),
    'unknown:' || v_email
  );

  if not private.consume_public_request_quota('support-ip', v_ip, 8, interval '1 hour')
     or not private.consume_public_request_quota('support-email', v_email, 3, interval '1 hour') then
    raise sqlstate 'PT429' using message = 'too_many_requests';
  end if;

  insert into public.support_requests (email, subject, message, locale)
  values (v_email, v_subject, v_message, v_locale)
  returning id into v_request_id;

  return v_request_id;
end;
$$;

revoke all on function public.submit_support_request(text, text, text, text, text) from public;
grant execute on function public.submit_support_request(text, text, text, text, text) to anon, authenticated, service_role;

comment on function public.register_price_alert(text, text, numeric)
  is 'Validated, rate-limited public price-alert registration; product metadata and token are server-derived.';
comment on function public.submit_support_request(text, text, text, text, text)
  is 'Validated, rate-limited public support form intake.';
