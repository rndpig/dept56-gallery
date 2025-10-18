-- Fix RLS policies for single-user app (no authentication)
-- The issue: user_id is NULL and auth.uid() is NULL, so NULL = NULL returns FALSE
-- The solution: Allow access when both are NULL (single-user mode)

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own houses" ON houses;
DROP POLICY IF EXISTS "Users can insert own houses" ON houses;
DROP POLICY IF EXISTS "Users can update own houses" ON houses;
DROP POLICY IF EXISTS "Users can delete own houses" ON houses;

DROP POLICY IF EXISTS "Users can view own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can insert own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can update own accessories" ON accessories;
DROP POLICY IF EXISTS "Users can delete own accessories" ON accessories;

DROP POLICY IF EXISTS "Users can view own collections" ON collections;
DROP POLICY IF EXISTS "Users can insert own collections" ON collections;
DROP POLICY IF EXISTS "Users can update own collections" ON collections;
DROP POLICY IF EXISTS "Users can delete own collections" ON collections;

DROP POLICY IF EXISTS "Users can view own tags" ON tags;
DROP POLICY IF EXISTS "Users can insert own tags" ON tags;
DROP POLICY IF EXISTS "Users can update own tags" ON tags;
DROP POLICY IF EXISTS "Users can delete own tags" ON tags;

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

-- Create new policies that allow access in single-user mode
-- Houses policies
CREATE POLICY "Allow all access to houses"
  ON houses FOR ALL
  USING (user_id IS NULL OR auth.uid() = user_id)
  WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- Accessories policies
CREATE POLICY "Allow all access to accessories"
  ON accessories FOR ALL
  USING (user_id IS NULL OR auth.uid() = user_id)
  WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- Collections policies
CREATE POLICY "Allow all access to collections"
  ON collections FOR ALL
  USING (user_id IS NULL OR auth.uid() = user_id)
  WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- Tags policies
CREATE POLICY "Allow all access to tags"
  ON tags FOR ALL
  USING (user_id IS NULL OR auth.uid() = user_id)
  WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

-- House-Accessory Links policies
CREATE POLICY "Allow all access to house_accessory_links"
  ON house_accessory_links FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_accessory_links.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_accessory_links.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  );

-- House-Collections policies
CREATE POLICY "Allow all access to house_collections"
  ON house_collections FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_collections.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_collections.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  );

-- Accessory-Collections policies
CREATE POLICY "Allow all access to accessory_collections"
  ON accessory_collections FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM accessories 
      WHERE accessories.id = accessory_collections.accessory_id 
      AND (accessories.user_id IS NULL OR accessories.user_id = auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM accessories 
      WHERE accessories.id = accessory_collections.accessory_id 
      AND (accessories.user_id IS NULL OR accessories.user_id = auth.uid())
    )
  );

-- House-Tags policies
CREATE POLICY "Allow all access to house_tags"
  ON house_tags FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_tags.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM houses 
      WHERE houses.id = house_tags.house_id 
      AND (houses.user_id IS NULL OR houses.user_id = auth.uid())
    )
  );

-- Accessory-Tags policies
CREATE POLICY "Allow all access to accessory_tags"
  ON accessory_tags FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM accessories 
      WHERE accessories.id = accessory_tags.accessory_id 
      AND (accessories.user_id IS NULL OR accessories.user_id = auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM accessories 
      WHERE accessories.id = accessory_tags.accessory_id 
      AND (accessories.user_id IS NULL OR accessories.user_id = auth.uid())
    )
  );
