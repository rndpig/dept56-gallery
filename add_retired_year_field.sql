-- Add retired_year field to houses and accessories tables
-- Run this in Supabase SQL Editor

ALTER TABLE houses ADD COLUMN IF NOT EXISTS retired_year INTEGER;
ALTER TABLE accessories ADD COLUMN IF NOT EXISTS retired_year INTEGER;

-- Add comment to document the field
COMMENT ON COLUMN houses.retired_year IS 'Year the house was retired from production';
COMMENT ON COLUMN accessories.retired_year IS 'Year the accessory was retired from production';
