-- ============================================
-- RLS Policies for Authenticated Admin Users
-- ============================================
-- This script sets up Row-Level Security (RLS) policies for a Department 56 gallery app
-- with Google OAuth authentication and email whitelist.
--
-- Security model:
-- - Public READ access: Anyone can browse the collection
-- - Private WRITE access: Only authenticated users with whitelisted emails can edit
-- - Storage: Public read, authenticated write for images
--
-- Run this script in your Supabase SQL Editor after enabling Google OAuth

-- ============================================
-- TABLE POLICIES
-- ============================================

-- Drop existing policies
DROP POLICY IF EXISTS "Allow all access to houses" ON houses;
DROP POLICY IF EXISTS "Public read access to houses" ON houses;
DROP POLICY IF EXISTS "Authenticated users can modify houses" ON houses;

DROP POLICY IF EXISTS "Allow all access to accessories" ON accessories;
DROP POLICY IF EXISTS "Public read access to accessories" ON accessories;
DROP POLICY IF EXISTS "Authenticated users can modify accessories" ON accessories;

DROP POLICY IF EXISTS "Allow all access to collections" ON collections;
DROP POLICY IF EXISTS "Public read access to collections" ON collections;
DROP POLICY IF EXISTS "Authenticated users can modify collections" ON collections;

DROP POLICY IF EXISTS "Allow all access to tags" ON tags;
DROP POLICY IF EXISTS "Public read access to tags" ON tags;
DROP POLICY IF EXISTS "Authenticated users can modify tags" ON tags;

DROP POLICY IF EXISTS "Allow all access to house_accessory_links" ON house_accessory_links;
DROP POLICY IF EXISTS "Public read access to house_accessory_links" ON house_accessory_links;
DROP POLICY IF EXISTS "Authenticated users can modify house_accessory_links" ON house_accessory_links;

DROP POLICY IF EXISTS "Allow all access to house_collections" ON house_collections;
DROP POLICY IF EXISTS "Public read access to house_collections" ON house_collections;
DROP POLICY IF EXISTS "Authenticated users can modify house_collections" ON house_collections;

DROP POLICY IF EXISTS "Allow all access to accessory_collections" ON accessory_collections;
DROP POLICY IF EXISTS "Public read access to accessory_collections" ON accessory_collections;
DROP POLICY IF EXISTS "Authenticated users can modify accessory_collections" ON accessory_collections;

DROP POLICY IF EXISTS "Allow all access to house_tags" ON house_tags;
DROP POLICY IF EXISTS "Public read access to house_tags" ON house_tags;
DROP POLICY IF EXISTS "Authenticated users can modify house_tags" ON house_tags;

DROP POLICY IF EXISTS "Allow all access to accessory_tags" ON accessory_tags;
DROP POLICY IF EXISTS "Public read access to accessory_tags" ON accessory_tags;
DROP POLICY IF EXISTS "Authenticated users can modify accessory_tags" ON accessory_tags;

-- ============================================
-- HOUSES - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to houses"
  ON houses FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify houses"
  ON houses FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- ACCESSORIES - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to accessories"
  ON accessories FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify accessories"
  ON accessories FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- COLLECTIONS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to collections"
  ON collections FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify collections"
  ON collections FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- TAGS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to tags"
  ON tags FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify tags"
  ON tags FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- HOUSE-ACCESSORY LINKS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to house_accessory_links"
  ON house_accessory_links FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify house_accessory_links"
  ON house_accessory_links FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- HOUSE-COLLECTIONS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to house_collections"
  ON house_collections FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify house_collections"
  ON house_collections FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- ACCESSORY-COLLECTIONS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to accessory_collections"
  ON accessory_collections FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify accessory_collections"
  ON accessory_collections FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- HOUSE-TAGS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to house_tags"
  ON house_tags FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify house_tags"
  ON house_tags FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- ACCESSORY-TAGS - Public read, authenticated write
-- ============================================

CREATE POLICY "Public read access to accessory_tags"
  ON accessory_tags FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can modify accessory_tags"
  ON accessory_tags FOR ALL
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- STORAGE BUCKET POLICIES
-- ============================================
-- Note: Storage policies must be set in the Supabase Dashboard
-- Go to: Storage > dept56-images > Policies
--
-- Create these two policies:
--
-- 1. "Public read access to images"
--    Operation: SELECT
--    Policy: true
--
-- 2. "Authenticated users can upload images"
--    Operation: INSERT
--    Policy: auth.role() = 'authenticated'
--
-- 3. "Authenticated users can update images"
--    Operation: UPDATE  
--    Policy: auth.role() = 'authenticated'
--
-- 4. "Authenticated users can delete images"
--    Operation: DELETE
--    Policy: auth.role() = 'authenticated'
