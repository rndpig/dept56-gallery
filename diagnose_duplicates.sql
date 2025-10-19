-- DUPLICATE HOUSE DIAGNOSTIC SCRIPT
-- Run this in Supabase SQL Editor to diagnose the duplicate houses issue

-- 1. Find exact duplicate house names with their IDs
SELECT 
  name,
  COUNT(*) as duplicate_count,
  string_agg(id::text, ', ') as house_ids,
  string_agg(created_at::text, ' | ') as created_dates
FROM houses
GROUP BY name
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, name;

-- 2. Show full details of duplicate houses
SELECT 
  h1.id as id1,
  h1.name,
  h1.created_at as created1,
  h1.sku as sku1,
  h2.id as id2,
  h2.created_at as created2,
  h2.sku as sku2
FROM houses h1
INNER JOIN houses h2 
  ON h1.name = h2.name 
  AND h1.id < h2.id
ORDER BY h1.name;

-- 3. Count accessories linked to each duplicate
SELECT 
  h.id,
  h.name,
  h.created_at,
  COUNT(hal.id) as accessory_count
FROM houses h
LEFT JOIN house_accessory_links hal ON h.id = hal.house_id
WHERE h.name IN (
  SELECT name 
  FROM houses 
  GROUP BY name 
  HAVING COUNT(*) > 1
)
GROUP BY h.id, h.name, h.created_at
ORDER BY h.name, h.created_at;

-- 4. Specific check for "Alfie's Toy School For Elves Early Release"
SELECT 
  h.id,
  h.name,
  h.year,
  h.retired_year,
  h.purchased_year,
  h.sku,
  h.price,
  h.collection,
  h.series,
  h.created_at,
  h.updated_at,
  COUNT(hal.id) as accessory_count
FROM houses h
LEFT JOIN house_accessory_links hal ON h.id = hal.house_id
WHERE h.name LIKE '%Alfie%Toy School%'
GROUP BY h.id, h.name, h.year, h.retired_year, h.purchased_year, h.sku, h.price, h.collection, h.series, h.created_at, h.updated_at
ORDER BY h.created_at;
