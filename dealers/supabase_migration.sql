-- 给 products 表加 dealer 列，区分 outlet 与各经销商
-- 在 Supabase Studio → SQL Editor 里执行一次

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS dealer text DEFAULT 'arcteryx_outlet';

-- 把已有数据全部归到 outlet
UPDATE products
  SET dealer = 'arcteryx_outlet'
  WHERE dealer IS NULL OR dealer = '';

-- dealer 字段加索引（前端按 dealer 过滤用）
CREATE INDEX IF NOT EXISTS products_dealer_idx ON products(dealer);

-- 完成后 SELECT 验证
SELECT dealer, COUNT(*) FROM products GROUP BY dealer ORDER BY 2 DESC;
