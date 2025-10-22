-- URGENT: Check what happened with Donder and other approvals
-- Run this in Supabase SQL Editor

-- 1. Check ALL approval history (not just undone ones)
SELECT 
  id,
  original_house_id,
  original_name,
  new_name,
  new_sku,
  approved_by,
  approved_at,
  undone_at,
  undone_by
FROM approval_history
ORDER BY approved_at DESC;

-- 2. Check staged_houses status for all items
SELECT 
  id,
  name,
  item_number as sku,
  status,
  reviewed_at,
  reviewed_by,
  overall_confidence_score
FROM staged_houses
ORDER BY created_at DESC
LIMIT 20;

-- 3. Search for Reindeer/Donder in houses table
SELECT 
  id,
  name,
  year,
  sku,
  user_id,
  created_at,
  updated_at
FROM houses
WHERE 
  name ILIKE '%reindeer%' 
  OR name ILIKE '%donder%'
  OR sku = '808928';

-- 4. Search in accessories table too
SELECT 
  id,
  name,
  user_id,
  created_at,
  updated_at
FROM accessories
WHERE 
  name ILIKE '%reindeer%' 
  OR name ILIKE '%donder%';
