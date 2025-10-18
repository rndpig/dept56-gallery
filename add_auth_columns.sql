-- Add user_id columns back and set up authentication
-- This adds user ownership while maintaining existing data

-- Add user_id columns
ALTER TABLE houses
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE accessories
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE collections
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE tags
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Drop any existing policies
DROP POLICY IF EXISTS "Public can view houses" ON houses;
DROP POLICY IF EXISTS "Public can view accessories" ON accessories;
DROP POLICY IF EXISTS "Public can view collections" ON collections;
DROP POLICY IF EXISTS "Public can view tags" ON tags;
DROP POLICY IF EXISTS "Public can view house_accessory_links" ON house_accessory_links;
DROP POLICY IF EXISTS "Public can view house_collections" ON house_collections;
DROP POLICY IF EXISTS "Public can view accessory_collections" ON accessory_collections;
DROP POLICY IF EXISTS "Public can view house_tags" ON house_tags;
DROP POLICY IF EXISTS "Public can view accessory_tags" ON accessory_tags;

-- Create authenticated access policies
CREATE POLICY "Authenticated users can view houses"
  ON houses FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert own houses"
  ON houses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own houses"
  ON houses FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL)
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete own houses"
  ON houses FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- Similar policies for accessories
CREATE POLICY "Authenticated users can view accessories"
  ON accessories FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert own accessories"
  ON accessories FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own accessories"
  ON accessories FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL)
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete own accessories"
  ON accessories FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- Storage policies for dept56-images bucket
DROP POLICY IF EXISTS "Public images access" ON storage.objects;

CREATE POLICY "Authenticated users can view images"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'dept56-images'
    AND auth.role() = 'authenticated'
  );

-- Ensure RLS is enabled
ALTER TABLE houses ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessories ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_accessory_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_tags ENABLE ROW LEVEL SECURITY;