-- ============================================================================
-- WEB SCRAPER STAGING TABLES MIGRATION
-- ============================================================================
-- Purpose: Create staging tables for web scraper data enhancement project
-- Safety: These tables are isolated from production (houses/accessories)
-- Date: 2025-10-21
-- ============================================================================

-- ============================================================================
-- TABLE: staged_houses
-- ============================================================================
-- Stores scraped house data for moderation before applying to production
CREATE TABLE IF NOT EXISTS staged_houses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Link to existing house (NULL for new imports)
  original_house_id UUID REFERENCES houses(id) ON DELETE SET NULL,
  
  -- Core identification
  item_number TEXT NOT NULL,
  name TEXT NOT NULL,
  
  -- Scraped data fields
  intro_year INTEGER,
  retire_year INTEGER,
  description TEXT,
  dimensions TEXT,
  
  -- Images
  primary_image_url TEXT,
  additional_images JSONB DEFAULT '[]'::jsonb,  -- Array of {url, source, scraped_at}
  
  -- Source URLs (where we found this data)
  dept56_official_url TEXT,
  dept56_retired_url TEXT,
  replacements_url TEXT,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Confidence scoring (0.00 to 1.00)
  name_match_score DECIMAL(3,2) CHECK (name_match_score >= 0 AND name_match_score <= 1),
  details_confidence_score DECIMAL(3,2) CHECK (details_confidence_score >= 0 AND details_confidence_score <= 1),
  overall_confidence_score DECIMAL(3,2) CHECK (overall_confidence_score >= 0 AND overall_confidence_score <= 1),
  
  -- Discovered relationships
  discovered_series TEXT,
  discovered_collection TEXT,
  discovered_accessories JSONB DEFAULT '[]'::jsonb,  -- Array of {name, item_number, confidence}
  
  -- Moderation workflow
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'needs_review')),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  reviewed_by TEXT,  -- Email of admin who reviewed
  moderator_notes TEXT,
  
  -- Fields that changed (for diff display)
  changed_fields JSONB DEFAULT '{}'::jsonb,  -- {field: {old: value, new: value}}
  
  -- Audit trail
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_staged_houses_status ON staged_houses(status);
CREATE INDEX IF NOT EXISTS idx_staged_houses_original_id ON staged_houses(original_house_id);
CREATE INDEX IF NOT EXISTS idx_staged_houses_item_number ON staged_houses(item_number);
CREATE INDEX IF NOT EXISTS idx_staged_houses_confidence ON staged_houses(overall_confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_staged_houses_created_at ON staged_houses(created_at DESC);

-- ============================================================================
-- TABLE: staged_accessories
-- ============================================================================
-- Stores scraped accessory data for moderation before applying to production
CREATE TABLE IF NOT EXISTS staged_accessories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Link to existing accessory (NULL for new imports)
  original_accessory_id UUID REFERENCES accessories(id) ON DELETE SET NULL,
  
  -- Core identification
  item_number TEXT NOT NULL,
  name TEXT NOT NULL,
  
  -- Scraped data fields
  intro_year INTEGER,
  retire_year INTEGER,
  description TEXT,
  dimensions TEXT,
  
  -- Images
  primary_image_url TEXT,
  additional_images JSONB DEFAULT '[]'::jsonb,
  
  -- Source URLs
  dept56_official_url TEXT,
  dept56_retired_url TEXT,
  replacements_url TEXT,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Confidence scoring
  name_match_score DECIMAL(3,2) CHECK (name_match_score >= 0 AND name_match_score <= 1),
  details_confidence_score DECIMAL(3,2) CHECK (details_confidence_score >= 0 AND details_confidence_score <= 1),
  overall_confidence_score DECIMAL(3,2) CHECK (overall_confidence_score >= 0 AND overall_confidence_score <= 1),
  
  -- Discovered relationships
  discovered_series TEXT,
  discovered_collection TEXT,
  discovered_compatible_houses JSONB DEFAULT '[]'::jsonb,  -- Array of {name, item_number, confidence}
  
  -- Moderation workflow
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'needs_review')),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  reviewed_by TEXT,
  moderator_notes TEXT,
  
  -- Fields that changed
  changed_fields JSONB DEFAULT '{}'::jsonb,
  
  -- Audit trail
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_staged_accessories_status ON staged_accessories(status);
CREATE INDEX IF NOT EXISTS idx_staged_accessories_original_id ON staged_accessories(original_accessory_id);
CREATE INDEX IF NOT EXISTS idx_staged_accessories_item_number ON staged_accessories(item_number);
CREATE INDEX IF NOT EXISTS idx_staged_accessories_confidence ON staged_accessories(overall_confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_staged_accessories_created_at ON staged_accessories(created_at DESC);

-- ============================================================================
-- TABLE: scraping_log
-- ============================================================================
-- Detailed logging of all scraping operations for debugging and monitoring
CREATE TABLE IF NOT EXISTS scraping_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- What we searched for
  search_query TEXT NOT NULL,
  item_type TEXT CHECK (item_type IN ('house', 'accessory')),
  
  -- Where we searched
  source_site TEXT NOT NULL CHECK (source_site IN ('dept56_official', 'dept56_retired', 'replacements')),
  
  -- Results
  results_found INTEGER DEFAULT 0,
  best_match_name TEXT,
  best_match_url TEXT,
  best_match_score DECIMAL(3,2),
  
  -- Success/failure tracking
  success BOOLEAN DEFAULT false,
  error_message TEXT,
  error_type TEXT,  -- 'network', 'parsing', 'rate_limit', 'not_found', 'timeout'
  
  -- Performance
  execution_time_ms INTEGER,
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analysis
CREATE INDEX IF NOT EXISTS idx_scraping_log_source ON scraping_log(source_site);
CREATE INDEX IF NOT EXISTS idx_scraping_log_success ON scraping_log(success);
CREATE INDEX IF NOT EXISTS idx_scraping_log_created_at ON scraping_log(created_at DESC);

-- ============================================================================
-- TABLE: moderation_audit
-- ============================================================================
-- Track all moderation decisions for accountability and rollback capability
CREATE TABLE IF NOT EXISTS moderation_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- What was moderated
  staged_item_id UUID NOT NULL,
  item_type TEXT NOT NULL CHECK (item_type IN ('house', 'accessory')),
  
  -- Action taken
  action TEXT NOT NULL CHECK (action IN ('approved', 'rejected', 'flagged', 'edited')),
  
  -- Changes applied (for rollback)
  before_data JSONB,  -- Full staged item data before action
  after_data JSONB,   -- Production data after approval (if applicable)
  changes_applied JSONB,  -- Specific fields that were updated
  
  -- Who and when
  moderator TEXT NOT NULL,  -- Email
  moderator_notes TEXT,
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_moderation_audit_staged_item ON moderation_audit(staged_item_id);
CREATE INDEX IF NOT EXISTS idx_moderation_audit_moderator ON moderation_audit(moderator);
CREATE INDEX IF NOT EXISTS idx_moderation_audit_action ON moderation_audit(action);
CREATE INDEX IF NOT EXISTS idx_moderation_audit_created_at ON moderation_audit(created_at DESC);

-- ============================================================================
-- TABLE: scraper_config
-- ============================================================================
-- Runtime configuration for scraper behavior (avoid hardcoding in Python)
CREATE TABLE IF NOT EXISTS scraper_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT UNIQUE NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default configuration
INSERT INTO scraper_config (key, value, description) VALUES
  ('rate_limits', '{"dept56_official": 1, "dept56_retired": 2, "replacements": 1}'::jsonb, 'Requests per second for each site'),
  ('confidence_thresholds', '{"auto_approve": 0.90, "recommend": 0.70, "review": 0.50}'::jsonb, 'Confidence score thresholds for actions'),
  ('timeout_seconds', '{"request": 30, "page_load": 45}'::jsonb, 'Timeout values for web requests'),
  ('user_agents', '["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]'::jsonb, 'List of user agents to rotate'),
  ('enabled_sources', '["dept56_retired", "replacements"]'::jsonb, 'Which sites to scrape (can disable problematic ones)')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on staging tables
ALTER TABLE staged_houses ENABLE ROW LEVEL SECURITY;
ALTER TABLE staged_accessories ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE moderation_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_config ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users (admins) can do everything on staging tables
CREATE POLICY "Authenticated users full access to staged_houses"
  ON staged_houses
  FOR ALL
  TO authenticated
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users full access to staged_accessories"
  ON staged_accessories
  FOR ALL
  TO authenticated
  USING (auth.uid() IS NOT NULL)
  WITH CHECK (auth.uid() IS NOT NULL);

-- Policy: Authenticated users can read logs
CREATE POLICY "Authenticated users read scraping_log"
  ON scraping_log
  FOR SELECT
  TO authenticated
  USING (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users read moderation_audit"
  ON moderation_audit
  FOR SELECT
  TO authenticated
  USING (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users read scraper_config"
  ON scraper_config
  FOR SELECT
  TO authenticated
  USING (auth.uid() IS NOT NULL);

-- Policy: Service role (Python scraper) can insert into logs
CREATE POLICY "Service role insert scraping_log"
  ON scraping_log
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Policy: Service role can insert/update staging tables
CREATE POLICY "Service role manage staged_houses"
  ON staged_houses
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role manage staged_accessories"
  ON staged_accessories
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Get pending items count by confidence level
CREATE OR REPLACE FUNCTION get_pending_items_summary()
RETURNS TABLE (
  item_type TEXT,
  total_pending BIGINT,
  high_confidence BIGINT,
  medium_confidence BIGINT,
  low_confidence BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    'house'::TEXT,
    COUNT(*),
    COUNT(*) FILTER (WHERE overall_confidence_score >= 0.80),
    COUNT(*) FILTER (WHERE overall_confidence_score >= 0.50 AND overall_confidence_score < 0.80),
    COUNT(*) FILTER (WHERE overall_confidence_score < 0.50)
  FROM staged_houses
  WHERE status = 'pending'
  
  UNION ALL
  
  SELECT 
    'accessory'::TEXT,
    COUNT(*),
    COUNT(*) FILTER (WHERE overall_confidence_score >= 0.80),
    COUNT(*) FILTER (WHERE overall_confidence_score >= 0.50 AND overall_confidence_score < 0.80),
    COUNT(*) FILTER (WHERE overall_confidence_score < 0.50)
  FROM staged_accessories
  WHERE status = 'pending';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_staged_houses_updated_at
  BEFORE UPDATE ON staged_houses
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_staged_accessories_updated_at
  BEFORE UPDATE ON staged_accessories
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after migration to verify everything is set up correctly

-- Check tables exist
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name LIKE 'staged_%' OR table_name IN ('scraping_log', 'moderation_audit', 'scraper_config');

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables 
-- WHERE schemaname = 'public' AND tablename LIKE 'staged_%';

-- Check default config
-- SELECT * FROM scraper_config;

-- Check pending items summary function
-- SELECT * FROM get_pending_items_summary();

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- Uncomment and run these if you need to completely remove the staging system

-- DROP TRIGGER IF EXISTS update_staged_houses_updated_at ON staged_houses;
-- DROP TRIGGER IF EXISTS update_staged_accessories_updated_at ON staged_accessories;
-- DROP FUNCTION IF EXISTS update_updated_at_column();
-- DROP FUNCTION IF EXISTS get_pending_items_summary();
-- DROP TABLE IF EXISTS moderation_audit;
-- DROP TABLE IF EXISTS scraping_log;
-- DROP TABLE IF EXISTS scraper_config;
-- DROP TABLE IF EXISTS staged_accessories;
-- DROP TABLE IF EXISTS staged_houses;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
