-- Add house_id column to accessories table
-- This creates a direct foreign key relationship between accessories and houses
-- Run this in your Supabase SQL Editor

-- Add the house_id column to accessories table
ALTER TABLE accessories 
ADD COLUMN house_id UUID REFERENCES houses(id) ON DELETE CASCADE;

-- Create an index for better query performance
CREATE INDEX idx_accessories_house_id ON accessories(house_id);

-- Add a helpful comment
COMMENT ON COLUMN accessories.house_id IS 'Direct reference to the parent house. An accessory belongs to one house.';

-- Display success message
SELECT 'Successfully added house_id column to accessories table' AS status;
