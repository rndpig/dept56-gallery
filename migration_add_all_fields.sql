-- Comprehensive Migration: Add all new fields to houses and accessories tables
-- Date: October 18, 2025
-- Description: Adds SKU, description, price, retired_year, collection, series fields

-- ============================================
-- ADD NEW FIELDS TO HOUSES TABLE
-- ============================================

-- Add SKU field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS sku VARCHAR(50);

-- Add description field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add price field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);

-- Add retired_year field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS retired_year INTEGER;

-- Add collection field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS collection VARCHAR(255);

-- Add series field
ALTER TABLE houses 
ADD COLUMN IF NOT EXISTS series VARCHAR(255);

-- ============================================
-- ADD NEW FIELDS TO ACCESSORIES TABLE
-- ============================================

-- Add SKU field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS sku VARCHAR(50);

-- Add description field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add price field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);

-- Add year field (released/introduced year)
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS year INTEGER;

-- Add retired_year field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS retired_year INTEGER;

-- Add collection field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS collection VARCHAR(255);

-- Add series field
ALTER TABLE accessories 
ADD COLUMN IF NOT EXISTS series VARCHAR(255);

-- ============================================
-- CREATE INDEXES FOR BETTER PERFORMANCE
-- ============================================

-- Index on SKU fields for faster lookups
CREATE INDEX IF NOT EXISTS idx_houses_sku ON houses(sku);
CREATE INDEX IF NOT EXISTS idx_accessories_sku ON accessories(sku);

-- Index on year fields for filtering
CREATE INDEX IF NOT EXISTS idx_houses_year ON houses(year);
CREATE INDEX IF NOT EXISTS idx_houses_retired_year ON houses(retired_year);
CREATE INDEX IF NOT EXISTS idx_accessories_year ON accessories(year);
CREATE INDEX IF NOT EXISTS idx_accessories_retired_year ON accessories(retired_year);

-- Index on collection and series for filtering
CREATE INDEX IF NOT EXISTS idx_houses_collection ON houses(collection);
CREATE INDEX IF NOT EXISTS idx_houses_series ON houses(series);
CREATE INDEX IF NOT EXISTS idx_accessories_collection ON accessories(collection);
CREATE INDEX IF NOT EXISTS idx_accessories_series ON accessories(series);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify the migration worked:

-- Check houses table structure
-- SELECT column_name, data_type, character_maximum_length, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'houses'
-- ORDER BY ordinal_position;

-- Check accessories table structure
-- SELECT column_name, data_type, character_maximum_length, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'accessories'
-- ORDER BY ordinal_position;

-- ============================================
-- NOTES
-- ============================================
-- All new fields are nullable to support gradual data migration
-- Existing data will not be affected
-- SKU fields are VARCHAR(50) to handle various formats (e.g., "56.12345", "Item #56957")
-- Price fields use DECIMAL(10,2) for precise monetary values
-- Year fields use INTEGER for 4-digit years
-- Collection and Series use VARCHAR(255) for text values
