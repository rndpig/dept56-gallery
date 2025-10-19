-- FIX DUPLICATE HOUSES SCRIPT
-- This script will remove duplicate houses, keeping the record WITH ACCESSORIES
-- If multiple have accessories, keeps the one with the most accessories
-- If none have accessories, keeps the oldest record

-- IMPORTANT: Run diagnose_duplicates.sql first to see what will be affected!
-- BACKUP YOUR DATA BEFORE RUNNING THIS!

-- Step 1: Create a temporary table with houses to keep (prioritizing those with accessories)
CREATE TEMP TABLE houses_to_keep AS
WITH house_accessory_counts AS (
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
)
SELECT DISTINCT ON (name) 
  id,
  name,
  created_at,
  accessory_count
FROM house_accessory_counts
ORDER BY 
  name, 
  accessory_count DESC,  -- Prioritize houses with more accessories
  created_at ASC;        -- If same accessory count, keep oldest

-- Step 2: Create a temporary table with houses to delete (newer duplicates)
CREATE TEMP TABLE houses_to_delete AS
SELECT h.id, h.name, h.created_at
FROM houses h
WHERE h.name IN (
  SELECT name 
  FROM houses 
  GROUP BY name 
  HAVING COUNT(*) > 1
)
AND h.id NOT IN (SELECT id FROM houses_to_keep);

-- Step 3: Show what will be deleted (REVIEW THIS!)
SELECT 
  htd.id as duplicate_id,
  htd.name,
  htd.created_at as duplicate_created,
  htk.id as kept_id,
  htk.created_at as kept_created,
  htk.accessory_count as kept_accessory_count
FROM houses_to_delete htd
JOIN houses_to_keep htk ON htd.name = htk.name
ORDER BY htd.name;

-- Step 3b: Show summary of what will be kept
SELECT 
  htk.id as kept_id,
  htk.name,
  htk.created_at as kept_created,
  htk.accessory_count as kept_accessory_count,
  'KEEPING THIS ONE' as action
FROM houses_to_keep htk
ORDER BY htk.name;

-- Step 4: Transfer house_accessory_links from duplicates to kept record
-- Only add links that don't already exist
WITH links_to_transfer AS (
  SELECT DISTINCT
    htk.id as new_house_id,
    hal.accessory_id
  FROM house_accessory_links hal
  JOIN houses_to_delete htd ON hal.house_id = htd.id
  JOIN houses_to_keep htk ON htd.name = htk.name
  WHERE NOT EXISTS (
    SELECT 1 
    FROM house_accessory_links hal2 
    WHERE hal2.house_id = htk.id 
    AND hal2.accessory_id = hal.accessory_id
  )
)
INSERT INTO house_accessory_links (house_id, accessory_id)
SELECT new_house_id, accessory_id FROM links_to_transfer;

-- Step 5: Transfer house_collections from duplicates to kept record
WITH collections_to_transfer AS (
  SELECT DISTINCT
    htk.id as new_house_id,
    hc.collection_id
  FROM house_collections hc
  JOIN houses_to_delete htd ON hc.house_id = htd.id
  JOIN houses_to_keep htk ON htd.name = htk.name
  WHERE NOT EXISTS (
    SELECT 1 
    FROM house_collections hc2 
    WHERE hc2.house_id = htk.id 
    AND hc2.collection_id = hc.collection_id
  )
)
INSERT INTO house_collections (house_id, collection_id)
SELECT new_house_id, collection_id FROM collections_to_transfer;

-- Step 6: Transfer house_tags from duplicates to kept record
WITH tags_to_transfer AS (
  SELECT DISTINCT
    htk.id as new_house_id,
    ht.tag_id,
    ht.source,
    ht.confidence,
    ht.reviewed
  FROM house_tags ht
  JOIN houses_to_delete htd ON ht.house_id = htd.id
  JOIN houses_to_keep htk ON htd.name = htk.name
  WHERE NOT EXISTS (
    SELECT 1 
    FROM house_tags ht2 
    WHERE ht2.house_id = htk.id 
    AND ht2.tag_id = ht.tag_id
  )
)
INSERT INTO house_tags (house_id, tag_id, source, confidence, reviewed)
SELECT new_house_id, tag_id, source, confidence, reviewed FROM tags_to_transfer;

-- Step 7: Delete the duplicate houses (CASCADE will handle related records)
DELETE FROM houses
WHERE id IN (SELECT id FROM houses_to_delete);

-- Step 8: Verify the fix
SELECT 
  name,
  COUNT(*) as count
FROM houses
GROUP BY name
HAVING COUNT(*) > 1;

-- Step 9: Show summary
SELECT 
  'Total duplicate names removed' as summary,
  COUNT(DISTINCT name) as count
FROM houses_to_delete;

SELECT 
  'Total duplicate house records deleted' as summary,
  COUNT(*) as count
FROM houses_to_delete;
