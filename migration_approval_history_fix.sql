-- Fix approval_history RLS policies
-- Run this in Supabase SQL Editor to fix the permission error

-- Drop the old policies that were causing the error
DROP POLICY IF EXISTS "Admin users can view all approval history" ON approval_history;
DROP POLICY IF EXISTS "Admin users can insert approval history" ON approval_history;
DROP POLICY IF EXISTS "Admin users can update approval history" ON approval_history;

-- Create new policies using auth.email() instead of querying auth.users
CREATE POLICY "Admin users can view all approval history"
  ON approval_history
  FOR SELECT
  TO authenticated
  USING (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

CREATE POLICY "Admin users can insert approval history"
  ON approval_history
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

CREATE POLICY "Admin users can update approval history"
  ON approval_history
  FOR UPDATE
  TO authenticated
  USING (
    auth.email() IN (SELECT email FROM admin_whitelist)
  );

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE tablename = 'approval_history';
