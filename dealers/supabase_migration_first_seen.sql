-- 加 first_seen 列，用于"今日上新"弹窗
-- 在 Supabase Studio → SQL Editor 里执行一次

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS first_seen timestamptz DEFAULT now();

-- 关键：把已有的 ~2000 行回填到一个**远过去的日期**，
-- 避免因为 ALTER TABLE 让所有行 first_seen 都变成今天，
-- 导致首次启用时弹窗炸出 2000 件"上新"
UPDATE products
  SET first_seen = TIMESTAMPTZ '2025-01-01 00:00:00+00'
  WHERE first_seen >= NOW() - INTERVAL '1 hour';

CREATE INDEX IF NOT EXISTS products_first_seen_idx
  ON products(first_seen DESC);

-- 验证
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE first_seen >= CURRENT_DATE) AS today_new,
    MIN(first_seen) AS earliest,
    MAX(first_seen) AS latest
FROM products;
