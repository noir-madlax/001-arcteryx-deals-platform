-- 降价提醒订阅表
-- 在 Supabase Studio → SQL Editor 里执行一次

CREATE TABLE IF NOT EXISTS price_alerts (
    id                  SERIAL PRIMARY KEY,
    email               TEXT NOT NULL,
    sku_id              TEXT NOT NULL,           -- 关联 products.sku_id
    target_price        NUMERIC,                  -- 触发阈值 (本币种); NULL = 任意下跌都通知
    last_price_seen     NUMERIC,                  -- 订阅时的价格快照
    currency            TEXT,                     -- 'USD' / 'EUR' / ...
    region              TEXT,                     -- 订阅时的国家代码
    product_name        TEXT,                     -- 冗余存一份, 邮件用
    product_url         TEXT,
    image_url           TEXT,
    notified_at         TIMESTAMPTZ,              -- 已发邮件就标时间, NULL = 待触发
    unsubscribe_token   TEXT UNIQUE NOT NULL,     -- 退订 URL 用; 防止他人无授权取消
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS price_alerts_sku_idx     ON price_alerts(sku_id);
CREATE INDEX IF NOT EXISTS price_alerts_email_idx   ON price_alerts(email);
CREATE INDEX IF NOT EXISTS price_alerts_pending_idx ON price_alerts(sku_id) WHERE notified_at IS NULL;

-- RLS: 匿名 anon key 可以 INSERT 自己的订阅, 但不能读他人订阅
ALTER TABLE price_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS anon_insert ON price_alerts;
CREATE POLICY anon_insert ON price_alerts FOR INSERT TO anon WITH CHECK (true);

-- 不允许 anon 读, 由 service_role (EC2 cron) 读取
DROP POLICY IF EXISTS service_role_full ON price_alerts;
CREATE POLICY service_role_full ON price_alerts FOR ALL TO service_role USING (true);

-- 退订: 提供 SECURITY DEFINER 函数, 只删 token 匹配的那一行, 返回删除数量
-- (避免 anon 拿到全表 DELETE 权)
CREATE OR REPLACE FUNCTION unsubscribe_alert(token TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    n INTEGER;
BEGIN
    DELETE FROM price_alerts WHERE unsubscribe_token = token;
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;

GRANT EXECUTE ON FUNCTION unsubscribe_alert(TEXT) TO anon;

-- 验证
SELECT 'price_alerts created' AS status, COUNT(*) FROM price_alerts;
