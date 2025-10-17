#!/usr/bin/env python3
"""
Display the complete SQL migration that needs to be run in Supabase dashboard.
"""

print("=" * 70)
print("📋 COMPLETE DATABASE SCHEMA MIGRATION")
print("=" * 70)
print()
print("⚠️  IMPORTANT: Please run this SQL in your Supabase SQL Editor")
print("   https://supabase.com/dashboard/project/xctottgirqkkmjmutoon")
print("   Navigate to: SQL Editor → New Query")
print()
print("=" * 70)
print()

sql = """-- Complete Schema Migration for Department 56 Gallery
-- This script:
-- 1. Removes user_id columns from houses and accessories tables
-- 2. Adds house_id column to accessories table for direct parent relationship

-- Step 1: Remove user_id columns
ALTER TABLE houses DROP COLUMN IF EXISTS user_id;
ALTER TABLE accessories DROP COLUMN IF EXISTS user_id;

-- Step 2: Add house_id column to accessories
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS house_id UUID REFERENCES houses(id) ON DELETE CASCADE;

-- Step 3: Create index for better performance
CREATE INDEX IF NOT EXISTS idx_accessories_house_id ON accessories(house_id);

-- Step 4: Add helpful comments
COMMENT ON COLUMN accessories.house_id IS 'Direct reference to the parent house. An accessory belongs to one house.';
COMMENT ON TABLE houses IS 'Department 56 collectible houses';
COMMENT ON TABLE accessories IS 'Department 56 accessories that belong to houses';

-- Display success message
SELECT 
  'Schema migration complete!' AS status,
  'Tables updated: houses, accessories' AS details,
  'Changes: removed user_id columns, added house_id to accessories' AS changes;
"""

print(sql)
print()
print("=" * 70)
print("✅ After running the SQL above, return here and confirm.")
print("=" * 70)
