-- Complete Schema Migration for Department 56 Gallery
-- This script:
-- 1. Drops RLS policies that depend on user_id
-- 2. Removes user_id columns from houses and accessories tables
-- 3. Adds house_id column to accessories table for direct parent relationship
-- Run this in your Supabase SQL Editor

-- ============================================
-- Step 1: Drop RLS policies for houses table
-- ============================================
DROP POLICY IF EXISTS "Users can view own houses" ON houses;
DROP POLICY IF EXISTS "Users can insert own houses" ON houses;
DROP POLICY IF EXISTS "Users can update own houses" ON houses;
DROP POLICY IF EXISTS "Users can delete own houses" ON houses;

-- ============================================
-- Step 2: Drop RLS policies for accessories table
-- ============================================
DROP POLICY IF EXISTS "Users can view own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can insert own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can update own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can delete own accessories" ON accessories;

-- ============================================
-- Step 3: Drop RLS policies for related tables that depend on houses.user_id
-- ============================================
DROP POLICY IF EXISTS "Users can view own house_accessory_links" ON house_accessory_links;
DROP POLICY IF EXISTS "Users can insert own house_accessory_links" ON house_accessory_links;
DROP POLICY IF EXISTS "Users can delete own house_accessory_links" ON house_accessory_links;

DROP POLICY IF EXISTS "Users can view own house_collections" ON house_collections;
DROP POLICY IF EXISTS "Users can insert own house_collections" ON house_collections;
DROP POLICY IF EXISTS "Users can delete own house_collections" ON house_collections;

DROP POLICY IF EXISTS "Users can view own accessory_collections" ON accessory_collections;
DROP POLICY IF EXISTS "Users can insert own accessory_collections" ON accessory_collections;
DROP POLICY IF EXISTS "Users can delete own accessory_collections" ON accessory_collections;

DROP POLICY IF EXISTS "Users can view own house_tags" ON house_tags;
DROP POLICY IF EXISTS "Users can insert own house_tags" ON house_tags;
DROP POLICY IF EXISTS "Users can update own house_tags" ON house_tags;
DROP POLICY IF EXISTS "Users can delete own house_tags" ON house_tags;

DROP POLICY IF EXISTS "Users can view own accessory_tags" ON accessory_tags;
DROP POLICY IF EXISTS "Users can insert own accessory_tags" ON accessory_tags;
DROP POLICY IF EXISTS "Users can update own accessory_tags" ON accessory_tags;
DROP POLICY IF EXISTS "Users can delete own accessory_tags" ON accessory_tags;

-- ============================================
-- Step 4: Remove user_id columns
-- ============================================
ALTER TABLE houses DROP COLUMN IF EXISTS user_id;
ALTER TABLE accessories DROP COLUMN IF EXISTS user_id;

-- ============================================
-- Step 5: Add house_id column to accessories
-- ============================================
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS house_id UUID REFERENCES houses(id) ON DELETE CASCADE;

-- ============================================
-- Step 6: Create index for better performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_accessories_house_id ON accessories(house_id);

-- ============================================
-- Step 7: Add helpful comments
-- ============================================
COMMENT ON COLUMN accessories.house_id IS 'Direct reference to the parent house. An accessory belongs to one house.';
COMMENT ON TABLE houses IS 'Department 56 collectible houses';
COMMENT ON TABLE accessories IS 'Department 56 accessories that belong to houses';

-- ============================================
-- Step 8: Disable RLS (since we're using service role key)
-- ============================================
-- Note: You're using the service role key which bypasses RLS anyway
-- We'll disable RLS since this is a single-user application
ALTER TABLE houses DISABLE ROW LEVEL SECURITY;
ALTER TABLE accessories DISABLE ROW LEVEL SECURITY;
ALTER TABLE house_accessory_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE house_collections DISABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_collections DISABLE ROW LEVEL SECURITY;
ALTER TABLE house_tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_tags DISABLE ROW LEVEL SECURITY;

-- Display success message
SELECT 
  'Schema migration complete!' AS status,
  'Tables updated: houses, accessories' AS details,
  'Changes: removed user_id columns, added house_id to accessories, disabled RLS' AS changes;
