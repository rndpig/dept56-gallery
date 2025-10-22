-- Find the Donder item in your database
-- Run this in Supabase SQL Editor to locate it

-- Search by SKU
SELECT id, name, year, sku, notes, photo_url, created_at, updated_at
FROM houses
WHERE sku = '808928';

-- Also search by name (in case it's in accessories)
SELECT id, name, notes, photo_url, created_at, updated_at
FROM accessories
WHERE name ILIKE '%donder%' OR name ILIKE '%reindeer%';

-- Check the approval history to see what changed
SELECT 
  original_name,
  new_name,
  original_sku,
  new_sku,
  approved_at,
  approved_by
FROM approval_history
WHERE new_name = 'Donder' OR original_name ILIKE '%donder%';
