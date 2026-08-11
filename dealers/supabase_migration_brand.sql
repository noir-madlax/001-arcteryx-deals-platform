-- GearDrop multi-brand migration. Apply before deploying code that selects
-- products.brand. Existing rows predate multi-brand support and are Arc'teryx.

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS brand text DEFAULT 'arcteryx';

UPDATE products
  SET brand = 'arcteryx'
  WHERE brand IS NULL OR btrim(brand) = '';

ALTER TABLE products
  ALTER COLUMN brand SET DEFAULT 'arcteryx',
  ALTER COLUMN brand SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'products'::regclass
      AND conname = 'products_brand_supported_check'
  ) THEN
    ALTER TABLE products
      ADD CONSTRAINT products_brand_supported_check
      CHECK (brand IN ('arcteryx', 'burton', 'patagonia'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS products_brand_idx ON products(brand);

SELECT brand, COUNT(*) FROM products GROUP BY brand ORDER BY brand;
