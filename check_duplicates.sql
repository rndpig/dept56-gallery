-- Check for duplicate house records
-- Run this in Supabase SQL Editor

-- Check for duplicate house IDs
SELECT id, COUNT(*) as count
FROM houses
GROUP BY id
HAVING COUNT(*) > 1;

-- Check for houses with the exact same name
SELECT name, COUNT(*) as count, array_agg(id) as house_ids
FROM houses
GROUP BY name
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- Check for houses with similar names (potential duplicates)
SELECT h1.id as id1, h1.name as name1, h2.id as id2, h2.name as name2
FROM houses h1
JOIN houses h2 ON h1.name = h2.name AND h1.id < h2.id
ORDER BY h1.name;

-- Count total houses
SELECT COUNT(*) as total_houses FROM houses;

-- Check specific house: "Alfie's Toy School For Elves Early Release"
SELECT id, name, year, retired_year, purchased_year, sku, collection, series, created_at
FROM houses
WHERE name LIKE '%Alfie%Toy School%'
ORDER BY created_at;
