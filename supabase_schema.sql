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

-- 4. Quick sanity check
SELECT COUNT(*) AS row_count FROM products;
