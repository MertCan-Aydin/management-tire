"""
VPS'te çalıştırın:
  psql -U mgmt_user -d management_db -f migration_v2.sql
"""

-- Suppliers: soft-delete, Numeric
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE suppliers ALTER COLUMN current_debt TYPE NUMERIC(12,2) USING current_debt::NUMERIC;

-- Products: soft-delete, Numeric
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE products ALTER COLUMN price      TYPE NUMERIC(12,2) USING price::NUMERIC;
ALTER TABLE products ALTER COLUMN cost_price TYPE NUMERIC(12,2) USING cost_price::NUMERIC;

-- Product batches: Numeric
ALTER TABLE product_batches ALTER COLUMN cost_price TYPE NUMERIC(12,2) USING cost_price::NUMERIC;

-- Sales: yeni kolonlar
ALTER TABLE sales ADD COLUMN IF NOT EXISTS total_cost NUMERIC(12,2) DEFAULT 0;
ALTER TABLE sales ALTER COLUMN total_amount TYPE NUMERIC(12,2) USING total_amount::NUMERIC;
ALTER TABLE sales ALTER COLUMN discount     TYPE NUMERIC(12,2) USING discount::NUMERIC;

-- Sale items: maliyet ve snapshot
ALTER TABLE sale_items ADD COLUMN IF NOT EXISTS unit_cost         NUMERIC(12,2) DEFAULT 0;
ALTER TABLE sale_items ADD COLUMN IF NOT EXISTS product_name_snap VARCHAR(255);
ALTER TABLE sale_items ALTER COLUMN unit_price TYPE NUMERIC(12,2) USING unit_price::NUMERIC;
-- Mevcut kayıtlar için snapshot doldur
UPDATE sale_items si
SET product_name_snap = p.name
FROM products p
WHERE si.product_id = p.id AND si.product_name_snap IS NULL;

-- Purchases: snapshot
ALTER TABLE purchases ALTER COLUMN total_amount TYPE NUMERIC(12,2) USING total_amount::NUMERIC;
ALTER TABLE purchase_items ADD COLUMN IF NOT EXISTS product_name_snap VARCHAR(255);
ALTER TABLE purchase_items ALTER COLUMN unit_price TYPE NUMERIC(12,2) USING unit_price::NUMERIC;
UPDATE purchase_items pi
SET product_name_snap = p.name
FROM products p
WHERE pi.product_id = p.id AND pi.product_name_snap IS NULL;

-- Expenses: Numeric
ALTER TABLE expenses ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::NUMERIC;

-- Supplier payments: Numeric
ALTER TABLE supplier_payments ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::NUMERIC;

-- Cancellation logs: yeni kolon
ALTER TABLE cancellation_logs ADD COLUMN IF NOT EXISTS cost_amount NUMERIC(12,2);
ALTER TABLE cancellation_logs ALTER COLUMN refund_amount TYPE NUMERIC(12,2) USING refund_amount::NUMERIC;

-- Mevcut satışlar için total_cost backfill (yaklaşık — gerçek FIFO geçmişe dönük hesaplanamaz)
-- Maliyet = ürünün mevcut cost_price * satılan miktar
UPDATE sales s
SET total_cost = COALESCE((
    SELECT SUM(si.quantity * p.cost_price)
    FROM sale_items si
    JOIN products p ON p.id = si.product_id
    WHERE si.sale_id = s.id AND si.is_cancelled = FALSE
), 0)
WHERE s.total_cost = 0;

SELECT 'Migration tamamlandi!' as result;
