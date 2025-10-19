-- Deployment Verification Queries
-- Run these in Supabase SQL Editor to verify the deployment

-- ============================================
-- RECORD COUNTS
-- ============================================

SELECT 'houses' as table_name, COUNT(*) as total_records FROM houses
UNION ALL
SELECT 'accessories', COUNT(*) FROM accessories
UNION ALL
SELECT 'house_accessory_links', COUNT(*) FROM house_accessory_links;

-- ============================================
-- IMAGES LINKED
-- ============================================

SELECT 
  'Houses with images' as metric,
  COUNT(*) as count
FROM houses
WHERE photo_url IS NOT NULL

UNION ALL

SELECT 
  'Houses without images',
  COUNT(*)
FROM houses
WHERE photo_url IS NULL

UNION ALL

SELECT 
  'Accessories with images',
  COUNT(*)
FROM accessories
WHERE photo_url IS NOT NULL

UNION ALL

SELECT 
  'Accessories without images',
  COUNT(*)
FROM accessories
WHERE photo_url IS NULL;

-- ============================================
-- DATA COMPLETENESS
-- ============================================

SELECT 
  'Houses with SKU' as metric,
  COUNT(*) as count
FROM houses
WHERE sku IS NOT NULL

UNION ALL

SELECT 
  'Houses with price',
  COUNT(*)
FROM houses
WHERE price IS NOT NULL

UNION ALL

SELECT 
  'Houses with collection',
  COUNT(*)
FROM houses
WHERE collection IS NOT NULL

UNION ALL

SELECT 
  'Houses with series',
  COUNT(*)
FROM houses
WHERE series IS NOT NULL

UNION ALL

SELECT 
  'Houses with retired_year',
  COUNT(*)
FROM houses
WHERE retired_year IS NOT NULL;

-- ============================================
-- SAMPLE DATA WITH IMAGES
-- ============================================

-- Sample houses with images
SELECT 
  name,
  sku,
  price,
  year,
  retired_year,
  collection,
  series,
  CASE 
    WHEN photo_url IS NOT NULL THEN '✅ Has Image'
    ELSE '❌ No Image'
  END as image_status
FROM houses
WHERE photo_url IS NOT NULL
ORDER BY name
LIMIT 10;

-- ============================================
-- SAMPLE LINKED DATA
-- ============================================

-- Houses with their accessories
SELECT 
  h.name as house_name,
  h.year as house_year,
  h.collection,
  a.name as accessory_name,
  CASE 
    WHEN h.photo_url IS NOT NULL THEN '✅'
    ELSE '❌'
  END as house_image,
  CASE 
    WHEN a.photo_url IS NOT NULL THEN '✅'
    ELSE '❌'
  END as accessory_image
FROM houses h
JOIN house_accessory_links hal ON h.id = hal.house_id
JOIN accessories a ON a.id = hal.accessory_id
ORDER BY h.name
LIMIT 20;

-- ============================================
-- COLLECTIONS SUMMARY
-- ============================================

SELECT 
  COALESCE(collection, 'No Collection') as collection_name,
  COUNT(*) as house_count
FROM houses
GROUP BY collection
ORDER BY house_count DESC
LIMIT 10;

-- ============================================
-- YEAR RANGE ANALYSIS
-- ============================================

SELECT 
  MIN(year) as earliest_year,
  MAX(year) as latest_year,
  MAX(retired_year) as last_retired_year,
  COUNT(DISTINCT year) as unique_years
FROM houses
WHERE year IS NOT NULL;

-- ============================================
-- PRICE STATISTICS
-- ============================================

SELECT 
  COUNT(*) as items_with_price,
  MIN(price) as lowest_price,
  MAX(price) as highest_price,
  ROUND(AVG(price)::numeric, 2) as average_price
FROM houses
WHERE price IS NOT NULL;
