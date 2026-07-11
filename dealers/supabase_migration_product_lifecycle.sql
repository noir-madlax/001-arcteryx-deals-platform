-- Product lifecycle state for safe crawler reconciliation.
-- Apply before deploying the matching supabase_sync.py version.

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS last_seen_at timestamptz,
  ADD COLUMN IF NOT EXISTS missing_runs integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS url_http_status integer,
  ADD COLUMN IF NOT EXISTS url_checked_at timestamptz;

UPDATE products
SET
  status = COALESCE(NULLIF(status, ''), 'active'),
  last_seen_at = COALESCE(last_seen_at, last_updated, created_at),
  missing_runs = COALESCE(missing_runs, 0);

-- Bootstrap old Outlet rows conservatively: hide rows that have not been seen
-- for 72 hours, but keep them recoverable. A complete future crawl can reactivate
-- them; a second complete miss moves them to inactive.
UPDATE products
SET status = 'missing', missing_runs = GREATEST(missing_runs, 1)
WHERE COALESCE(dealer, 'arcteryx_outlet') = 'arcteryx_outlet'
  AND status = 'active'
  AND last_seen_at < NOW() - INTERVAL '72 hours';

ALTER TABLE products DROP CONSTRAINT IF EXISTS products_status_check;
ALTER TABLE products
  ADD CONSTRAINT products_status_check
  CHECK (status IN ('active', 'missing', 'inactive', 'unavailable'));

ALTER TABLE products DROP CONSTRAINT IF EXISTS products_missing_runs_check;
ALTER TABLE products
  ADD CONSTRAINT products_missing_runs_check CHECK (missing_runs >= 0);

CREATE INDEX IF NOT EXISTS products_status_idx ON products(status);
CREATE INDEX IF NOT EXISTS products_last_seen_at_idx ON products(last_seen_at);
CREATE INDEX IF NOT EXISTS products_url_check_idx ON products(status, url_checked_at);

-- Database-level safety net for current and older clients. Service-role jobs
-- bypass RLS and retain full lifecycle visibility for reconciliation/audit.
DROP POLICY IF EXISTS "public_read" ON products;
DROP POLICY IF EXISTS "public_read_active_products" ON products;
CREATE POLICY "public_read_active_products"
  ON products FOR SELECT
  TO anon, authenticated
  USING (status = 'active');

SELECT status, COUNT(*) FROM products GROUP BY status ORDER BY status;
