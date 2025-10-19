-- Add price field to houses and accessories tables
-- Run this in Supabase SQL Editor

ALTER TABLE houses ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);
ALTER TABLE accessories ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);

-- Add comment to document the field
COMMENT ON COLUMN houses.price IS 'Purchase or retail price of the house';
COMMENT ON COLUMN accessories.price IS 'Purchase or retail price of the accessory';
