-- Approval History Table
-- Stores original values before moderation changes for undo capability

CREATE TABLE IF NOT EXISTS approval_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  staged_house_id UUID REFERENCES staged_houses(id) ON DELETE CASCADE NOT NULL,
  original_house_id UUID REFERENCES houses(id) ON DELETE SET NULL,
  
  -- Original values before the change
  original_name TEXT,
  original_year INTEGER,
  original_sku TEXT,
  original_notes TEXT,
  original_photo_url TEXT,
  
  -- New values that were applied
  new_name TEXT,
  new_year INTEGER,
  new_sku TEXT,
  new_notes TEXT,
  new_photo_url TEXT,
  
  -- Metadata
  approved_by TEXT NOT NULL,
  approved_at TIMESTAMPTZ DEFAULT NOW(),
  undone_at TIMESTAMPTZ,
  undone_by TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_approval_history_staged_house 
  ON approval_history(staged_house_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_original_house 
  ON approval_history(original_house_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_approved_at 
  ON approval_history(approved_at DESC);

-- RLS Policies
ALTER TABLE approval_history ENABLE ROW LEVEL SECURITY;

-- Admin users can view all approval history
CREATE POLICY "Admin users can view all approval history"
  ON approval_history
  FOR SELECT
  TO authenticated
  USING (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

-- Admin users can insert approval history
CREATE POLICY "Admin users can insert approval history"
  ON approval_history
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

-- Admin users can update approval history (for undo)
CREATE POLICY "Admin users can update approval history"
  ON approval_history
  FOR UPDATE
  TO authenticated
  USING (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

COMMENT ON TABLE approval_history IS 'Audit trail and undo capability for approved scraped data';
