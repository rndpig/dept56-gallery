-- Temporary DEV ONLY policy to allow localhost testing of Data Review tab
-- This allows anonymous (anon key) reads of staged_houses table
-- REMOVE THIS BEFORE PRODUCTION DEPLOYMENT

-- Add a policy for anonymous reads (for localhost development)
CREATE POLICY "DEV: Allow anonymous read staged_houses"
  ON staged_houses
  FOR SELECT
  TO anon
  USING (true);

-- Note: Writes still require authentication
-- This only affects SELECT queries
