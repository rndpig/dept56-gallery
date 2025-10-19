-- Add SKU field to houses and accessories tables
-- Run this in Supabase SQL Editor

ALTER TABLE houses ADD COLUMN IF NOT EXISTS sku TEXT;
ALTER TABLE accessories ADD COLUMN IF NOT EXISTS sku TEXT;

-- Optional: Add comment to document the field
COMMENT ON COLUMN houses.sku IS 'SKU or item number for the house';
COMMENT ON COLUMN accessories.sku IS 'SKU or item number for the accessory';
