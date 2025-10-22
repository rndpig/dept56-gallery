-- ============================================================================
-- ADMIN WHITELIST TABLE - ADDENDUM TO STAGING MIGRATION
-- ============================================================================
-- Purpose: Create admin whitelist table for proper RLS security
-- Run this AFTER the main staging tables migration
-- ============================================================================

-- ============================================================================
-- TABLE: admin_whitelist
-- ============================================================================
-- Stores approved admin email addresses
CREATE TABLE IF NOT EXISTS admin_whitelist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  added_by TEXT,
  notes TEXT
);

-- Enable RLS
ALTER TABLE admin_whitelist ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone authenticated can read the whitelist (needed for RLS checks)
CREATE POLICY "Authenticated users can read admin_whitelist"
  ON admin_whitelist
  FOR SELECT
  TO authenticated
  USING (auth.uid() IS NOT NULL);

-- Insert your family members
INSERT INTO admin_whitelist (email, name, notes) VALUES
  ('rndpig@gmail.com', 'Ryan N Dilger', 'Owner'),
  ('annadilger@gmail.com', 'Anna Dilger', 'Family member'),
  ('bday1951@gmail.com', 'Family member', 'Family member'),
  ('drdcreek@gmail.com', 'Family member', 'Family member'),
  ('ericlday@gmail.com', 'Eric Day', 'Family member'),
  ('amyannday@gmail.com', 'Amy Ann Day', 'Family member')
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- UPDATE STAGING TABLE POLICIES TO USE WHITELIST
-- ============================================================================

-- Drop the temporary "any authenticated user" policies
DROP POLICY IF EXISTS "Authenticated users full access to staged_houses" ON staged_houses;
DROP POLICY IF EXISTS "Authenticated users full access to staged_accessories" ON staged_accessories;
DROP POLICY IF EXISTS "Authenticated users read scraping_log" ON scraping_log;
DROP POLICY IF EXISTS "Authenticated users read moderation_audit" ON moderation_audit;
DROP POLICY IF EXISTS "Authenticated users read scraper_config" ON scraper_config;

-- Create proper whitelist-based policies
CREATE POLICY "Whitelisted admins full access to staged_houses"
  ON staged_houses
  FOR ALL
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  )
  WITH CHECK (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  );

CREATE POLICY "Whitelisted admins full access to staged_accessories"
  ON staged_accessories
  FOR ALL
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  )
  WITH CHECK (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  );

CREATE POLICY "Whitelisted admins read scraping_log"
  ON scraping_log
  FOR SELECT
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  );

CREATE POLICY "Whitelisted admins read moderation_audit"
  ON moderation_audit
  FOR SELECT
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  );

CREATE POLICY "Whitelisted admins read scraper_config"
  ON scraper_config
  FOR SELECT
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN (
      SELECT email FROM admin_whitelist
    )
  );

-- Service role policies remain unchanged (already set in main migration)

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check whitelist was populated
-- SELECT * FROM admin_whitelist ORDER BY email;

-- Test that you can query staging tables (run this while logged in)
-- SELECT COUNT(*) FROM staged_houses;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
