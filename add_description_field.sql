-- Migration to add description field and remove purchased_on field
-- Run this in Supabase SQL Editor

-- Add description column to houses table
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add description column to accessories table
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Drop purchased_on column from houses table (if you want to keep the data, skip this)
-- ALTER TABLE houses DROP COLUMN IF EXISTS purchased_on;

-- Drop purchased_on column from accessories table (if you want to keep the data, skip this)
-- ALTER TABLE accessories DROP COLUMN IF EXISTS purchased_on;

-- Note: The DROP COLUMN statements are commented out to preserve existing data
-- Uncomment them if you want to permanently remove the purchased_on field
