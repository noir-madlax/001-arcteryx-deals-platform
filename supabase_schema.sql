-- ============================================================
--  Arc'teryx Deals Platform — Supabase Schema
--  Run this in Supabase SQL Editor (once)
-- ============================================================

-- 1. Products table
CREATE TABLE IF NOT EXISTS products (
  id             BIGSERIAL PRIMARY KEY,
  sku_id         TEXT        NOT NULL UNIQUE,
  model          TEXT,
  full_name      TEXT,
  color          TEXT,
  sizes          JSONB       DEFAULT '[]',
  size_stock     JSONB       DEFAULT '{}',
  original_price NUMERIC,
  sale_price     NUMERIC     NOT NULL,
  discount_pct   INTEGER,
  currency       TEXT,
  symbol         TEXT,
  gender         TEXT,
  region         TEXT,
  region_name    TEXT,
  category       TEXT,
  url            TEXT,
  image_url      TEXT,
  images         JSONB       DEFAULT '[]',
  description    TEXT,
  last_updated   TIMESTAMPTZ,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Index for common filter queries
CREATE INDEX IF NOT EXISTS idx_products_region    ON products (region);
CREATE INDEX IF NOT EXISTS idx_products_gender    ON products (gender);
CREATE INDEX IF NOT EXISTS idx_products_category  ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_sale_price ON products (sale_price);
CREATE INDEX IF NOT EXISTS idx_products_discount  ON products (discount_pct);

-- 3. Row Level Security — allow anonymous read, block writes
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read" ON products;
CREATE POLICY "public_read"
  ON products FOR SELECT
  USING (true);

-- service_role key bypasses RLS automatically, so no write policy needed
-- (scraper uses service_role key, frontend uses anon key)

-- 4. Price history (append-only log, preserved even after product is removed)
CREATE TABLE IF NOT EXISTS price_history (
  id             BIGSERIAL PRIMARY KEY,
  sku_id         TEXT        NOT NULL,
  original_price NUMERIC,
  sale_price     NUMERIC     NOT NULL,
  discount_pct   INTEGER,
  currency       TEXT,
  recorded_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_sku_recorded
  ON price_history (sku_id, recorded_at DESC);

ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public_read_price_history" ON price_history;
CREATE POLICY "public_read_price_history"
  ON price_history FOR SELECT
  TO anon, authenticated
  USING (true);

-- 关键: Supabase PostgREST 要 GRANT + RLS policy 都通过才能读. 之前漏 GRANT
-- 导致 anon 401, 详情页价格历史折线图全部空白. 修复 2026-06-11.
GRANT SELECT ON TABLE price_history TO anon, authenticated;

-- 5. Quick sanity check
SELECT COUNT(*) AS row_count FROM products;
