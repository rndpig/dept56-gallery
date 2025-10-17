-- Remove user_id column from houses and accessories tables
-- This column is no longer needed for bulk imports

-- Remove user_id from houses table
ALTER TABLE houses
DROP COLUMN IF EXISTS user_id;

-- Remove user_id from accessories table
ALTER TABLE accessories
DROP COLUMN IF EXISTS user_id;

-- Add comments explaining the schema
COMMENT ON TABLE houses IS 'Department 56 collectible houses catalog';
COMMENT ON TABLE accessories IS 'Accessories linked to Department 56 houses';
COMMENT ON COLUMN accessories.house_id IS 'Foreign key linking accessory to its parent house';
