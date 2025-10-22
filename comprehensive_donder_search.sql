-- Direct database query to find Donder/Reindeer anywhere
-- This will search across all tables and all users

-- 1. Search houses table (all users)
SELECT 
  'houses' as table_name,
  id,
  user_id,
  name,
  year,
  sku,
  notes,
  created_at
FROM houses
WHERE 
  name ILIKE '%donder%' 
  OR name ILIKE '%reindeer%'
  OR sku = '808928'
  OR notes ILIKE '%donder%'
  OR notes ILIKE '%reindeer%'
ORDER BY created_at DESC;

-- 2. Search accessories table (all users)
SELECT 
  'accessories' as table_name,
  id,
  user_id,
  name,
  notes,
  created_at
FROM accessories
WHERE 
  name ILIKE '%donder%' 
  OR name ILIKE '%reindeer%'
  OR notes ILIKE '%donder%'
  OR notes ILIKE '%reindeer%'
ORDER BY created_at DESC;

-- 3. Search staged_houses (pending, approved, rejected)
SELECT 
  'staged_houses' as table_name,
  id,
  original_house_id,
  name,
  item_number as sku,
  status,
  overall_confidence_score,
  created_at
FROM staged_houses
WHERE 
  name ILIKE '%donder%' 
  OR name ILIKE '%reindeer%'
  OR item_number = '808928'
ORDER BY created_at DESC;

-- 4. Search approval_history
SELECT 
  'approval_history' as table_name,
  id,
  original_house_id,
  original_name,
  new_name,
  new_sku,
  approved_by,
  approved_at,
  undone_at
FROM approval_history
WHERE 
  original_name ILIKE '%donder%' 
  OR original_name ILIKE '%reindeer%'
  OR new_name ILIKE '%donder%'
  OR new_name ILIKE '%reindeer%'
  OR new_sku = '808928'
ORDER BY approved_at DESC;

-- 5. Count total records in each table for context
SELECT 'Total houses' as info, COUNT(*) as count FROM houses
UNION ALL
SELECT 'Total accessories', COUNT(*) FROM accessories
UNION ALL
SELECT 'Total staged (pending)', COUNT(*) FROM staged_houses WHERE status = 'pending'
UNION ALL
SELECT 'Total staged (approved)', COUNT(*) FROM staged_houses WHERE status = 'approved'
UNION ALL
SELECT 'Total approval history', COUNT(*) FROM approval_history;
