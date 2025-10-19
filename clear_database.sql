-- Clear all data from Supabase database
-- WARNING: This will delete ALL data from the database
-- Date: October 18, 2025

-- ============================================
-- DISABLE TRIGGERS (to avoid cascading issues)
-- ============================================
SET session_replication_role = 'replica';

-- ============================================
-- DELETE ALL DATA (order matters due to foreign keys)
-- ============================================

-- Delete tag links first
DELETE FROM house_tags;
DELETE FROM accessory_tags;

-- Delete collection links
DELETE FROM house_collections;
DELETE FROM accessory_collections;

-- Delete house-accessory links
DELETE FROM house_accessory_links;

-- Delete main tables
DELETE FROM houses;
DELETE FROM accessories;
DELETE FROM collections;
DELETE FROM tags;

-- ============================================
-- RE-ENABLE TRIGGERS
-- ============================================
SET session_replication_role = 'origin';

-- ============================================
-- VERIFICATION
-- ============================================
-- Run these to verify all data is cleared:

SELECT 'houses' as table_name, COUNT(*) as row_count FROM houses
UNION ALL
SELECT 'accessories', COUNT(*) FROM accessories
UNION ALL
SELECT 'collections', COUNT(*) FROM collections
UNION ALL
SELECT 'tags', COUNT(*) FROM tags
UNION ALL
SELECT 'house_accessory_links', COUNT(*) FROM house_accessory_links
UNION ALL
SELECT 'house_collections', COUNT(*) FROM house_collections
UNION ALL
SELECT 'accessory_collections', COUNT(*) FROM accessory_collections
UNION ALL
SELECT 'house_tags', COUNT(*) FROM house_tags
UNION ALL
SELECT 'accessory_tags', COUNT(*) FROM accessory_tags;

-- All counts should be 0
