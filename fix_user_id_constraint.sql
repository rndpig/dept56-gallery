-- Make user_id nullable to support bulk imports with service role key
-- This allows us to import data without requiring an authenticated user

ALTER TABLE houses
ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE accessories
ALTER COLUMN user_id DROP NOT NULL;

-- Optional: Add a comment explaining why this is nullable
COMMENT ON COLUMN houses.user_id IS 'User who owns this house. Nullable for bulk imports.';
COMMENT ON COLUMN accessories.user_id IS 'User who owns this accessory. Nullable for bulk imports.';
