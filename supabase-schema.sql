-- Department 56 Gallery App - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLES
-- ============================================

-- Houses table
CREATE TABLE houses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  year INTEGER,
  notes TEXT,
  photo_url TEXT,
  purchased_on DATE,
  purchased_year INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Accessories table
CREATE TABLE accessories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  notes TEXT,
  photo_url TEXT,
  purchased_on DATE,
  purchased_year INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collections table
CREATE TABLE collections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Tags table
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- House-Accessory links (many-to-many)
CREATE TABLE house_accessory_links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  house_id UUID REFERENCES houses(id) ON DELETE CASCADE NOT NULL,
  accessory_id UUID REFERENCES accessories(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(house_id, accessory_id)
);

-- House-Collection links (many-to-many)
CREATE TABLE house_collections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  house_id UUID REFERENCES houses(id) ON DELETE CASCADE NOT NULL,
  collection_id UUID REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(house_id, collection_id)
);

-- Accessory-Collection links (many-to-many)
CREATE TABLE accessory_collections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  accessory_id UUID REFERENCES accessories(id) ON DELETE CASCADE NOT NULL,
  collection_id UUID REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(accessory_id, collection_id)
);

-- House-Tag links (many-to-many with metadata)
CREATE TABLE house_tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  house_id UUID REFERENCES houses(id) ON DELETE CASCADE NOT NULL,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('manual', 'ml')),
  confidence DECIMAL(3, 2),
  reviewed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(house_id, tag_id)
);

-- Accessory-Tag links (many-to-many with metadata)
CREATE TABLE accessory_tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  accessory_id UUID REFERENCES accessories(id) ON DELETE CASCADE NOT NULL,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('manual', 'ml')),
  confidence DECIMAL(3, 2),
  reviewed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(accessory_id, tag_id)
);

-- ============================================
-- INDEXES for better query performance
-- ============================================

CREATE INDEX idx_houses_user_id ON houses(user_id);
CREATE INDEX idx_accessories_user_id ON accessories(user_id);
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_house_accessory_links_house_id ON house_accessory_links(house_id);
CREATE INDEX idx_house_accessory_links_accessory_id ON house_accessory_links(accessory_id);
CREATE INDEX idx_house_collections_house_id ON house_collections(house_id);
CREATE INDEX idx_house_collections_collection_id ON house_collections(collection_id);
CREATE INDEX idx_accessory_collections_accessory_id ON accessory_collections(accessory_id);
CREATE INDEX idx_accessory_collections_collection_id ON accessory_collections(collection_id);
CREATE INDEX idx_house_tags_house_id ON house_tags(house_id);
CREATE INDEX idx_house_tags_tag_id ON house_tags(tag_id);
CREATE INDEX idx_accessory_tags_accessory_id ON accessory_tags(accessory_id);
CREATE INDEX idx_accessory_tags_tag_id ON accessory_tags(tag_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE houses ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessories ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_accessory_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE house_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessory_tags ENABLE ROW LEVEL SECURITY;

-- Houses policies
CREATE POLICY "Users can view own houses"
  ON houses FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own houses"
  ON houses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own houses"
  ON houses FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own houses"
  ON houses FOR DELETE
  USING (auth.uid() = user_id);

-- Accessories policies
CREATE POLICY "Users can view own accessories"
  ON accessories FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own accessories"
  ON accessories FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own accessories"
  ON accessories FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own accessories"
  ON accessories FOR DELETE
  USING (auth.uid() = user_id);

-- Collections policies
CREATE POLICY "Users can view own collections"
  ON collections FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own collections"
  ON collections FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own collections"
  ON collections FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own collections"
  ON collections FOR DELETE
  USING (auth.uid() = user_id);

-- Tags policies
CREATE POLICY "Users can view own tags"
  ON tags FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tags"
  ON tags FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tags"
  ON tags FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own tags"
  ON tags FOR DELETE
  USING (auth.uid() = user_id);

-- House-Accessory links policies (can access if owns the house)
CREATE POLICY "Users can view own house_accessory_links"
  ON house_accessory_links FOR SELECT
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_accessory_links.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can insert own house_accessory_links"
  ON house_accessory_links FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_accessory_links.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can delete own house_accessory_links"
  ON house_accessory_links FOR DELETE
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_accessory_links.house_id AND houses.user_id = auth.uid()));

-- House-Collection links policies
CREATE POLICY "Users can view own house_collections"
  ON house_collections FOR SELECT
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_collections.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can insert own house_collections"
  ON house_collections FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_collections.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can delete own house_collections"
  ON house_collections FOR DELETE
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_collections.house_id AND houses.user_id = auth.uid()));

-- Accessory-Collection links policies
CREATE POLICY "Users can view own accessory_collections"
  ON accessory_collections FOR SELECT
  USING (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_collections.accessory_id AND accessories.user_id = auth.uid()));

CREATE POLICY "Users can insert own accessory_collections"
  ON accessory_collections FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_collections.accessory_id AND accessories.user_id = auth.uid()));

CREATE POLICY "Users can delete own accessory_collections"
  ON accessory_collections FOR DELETE
  USING (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_collections.accessory_id AND accessories.user_id = auth.uid()));

-- House-Tag links policies
CREATE POLICY "Users can view own house_tags"
  ON house_tags FOR SELECT
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_tags.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can insert own house_tags"
  ON house_tags FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_tags.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can update own house_tags"
  ON house_tags FOR UPDATE
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_tags.house_id AND houses.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_tags.house_id AND houses.user_id = auth.uid()));

CREATE POLICY "Users can delete own house_tags"
  ON house_tags FOR DELETE
  USING (EXISTS (SELECT 1 FROM houses WHERE houses.id = house_tags.house_id AND houses.user_id = auth.uid()));

-- Accessory-Tag links policies
CREATE POLICY "Users can view own accessory_tags"
  ON accessory_tags FOR SELECT
  USING (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_tags.accessory_id AND accessories.user_id = auth.uid()));

CREATE POLICY "Users can insert own accessory_tags"
  ON accessory_tags FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_tags.accessory_id AND accessories.user_id = auth.uid()));

CREATE POLICY "Users can update own accessory_tags"
  ON accessory_tags FOR UPDATE
  USING (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_tags.accessory_id AND accessories.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_tags.accessory_id AND accessories.user_id = auth.uid()));

CREATE POLICY "Users can delete own accessory_tags"
  ON accessory_tags FOR DELETE
  USING (EXISTS (SELECT 1 FROM accessories WHERE accessories.id = accessory_tags.accessory_id AND accessories.user_id = auth.uid()));

-- ============================================
-- STORAGE BUCKET for images
-- ============================================
-- Run this in the Supabase Storage section OR via SQL:

INSERT INTO storage.buckets (id, name, public)
VALUES ('dept56-images', 'dept56-images', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for dept56-images bucket
CREATE POLICY "Users can upload their own images"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'dept56-images' 
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can view their own images"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'dept56-images' 
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can update their own images"
  ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'dept56-images' 
    AND auth.uid()::text = (storage.foldername(name))[1]
  )
  WITH CHECK (
    bucket_id = 'dept56-images' 
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can delete their own images"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'dept56-images' 
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_houses_updated_at
  BEFORE UPDATE ON houses
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accessories_updated_at
  BEFORE UPDATE ON accessories
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
