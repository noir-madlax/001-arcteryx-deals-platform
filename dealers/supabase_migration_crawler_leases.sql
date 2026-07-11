-- Distributed crawler coordination. Apply before enabling multi-node schedules.

CREATE TABLE IF NOT EXISTS crawler_leases (
  scope text PRIMARY KEY,
  lease_owner text NOT NULL,
  lease_until timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'idle'
    CHECK (status IN ('idle', 'running', 'success', 'failed')),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  message text
);

ALTER TABLE crawler_leases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public_read_crawler_leases" ON crawler_leases;
CREATE POLICY "public_read_crawler_leases"
  ON crawler_leases FOR SELECT
  TO anon, authenticated
  USING (true);

GRANT SELECT ON TABLE crawler_leases TO anon, authenticated;

CREATE OR REPLACE FUNCTION claim_crawler_lease(
  p_scope text,
  p_owner text,
  p_ttl_minutes integer DEFAULT 240
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  affected integer := 0;
BEGIN
  INSERT INTO crawler_leases (
    scope, lease_owner, lease_until, status, started_at, completed_at, updated_at, message
  ) VALUES (
    p_scope, p_owner, now() + make_interval(mins => p_ttl_minutes),
    'running', now(), NULL, now(), NULL
  )
  ON CONFLICT (scope) DO UPDATE SET
    lease_owner = EXCLUDED.lease_owner,
    lease_until = EXCLUDED.lease_until,
    status = 'running',
    started_at = now(),
    completed_at = NULL,
    updated_at = now(),
    message = NULL
  WHERE crawler_leases.lease_until <= now()
     OR crawler_leases.lease_owner = p_owner;

  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected > 0;
END;
$$;

CREATE OR REPLACE FUNCTION finish_crawler_lease(
  p_scope text,
  p_owner text,
  p_status text,
  p_message text DEFAULT NULL
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  affected integer := 0;
BEGIN
  IF p_status NOT IN ('success', 'failed') THEN
    RAISE EXCEPTION 'invalid crawler status: %', p_status;
  END IF;

  UPDATE crawler_leases SET
    lease_until = now(),
    status = p_status,
    completed_at = now(),
    updated_at = now(),
    message = left(p_message, 500)
  WHERE scope = p_scope AND lease_owner = p_owner;

  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected > 0;
END;
$$;

REVOKE ALL ON FUNCTION claim_crawler_lease(text, text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION finish_crawler_lease(text, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION claim_crawler_lease(text, text, integer) TO service_role;
GRANT EXECUTE ON FUNCTION finish_crawler_lease(text, text, text, text) TO service_role;
