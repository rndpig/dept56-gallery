-- Verify approval_history policies are complete
-- This checks both USING and WITH CHECK clauses

SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual as "USING clause",
    with_check as "WITH CHECK clause"
FROM pg_policies 
WHERE tablename = 'approval_history'
ORDER BY cmd;

-- Test if insert would work (doesn't actually insert)
-- This will tell us if the policy allows inserts
EXPLAIN (VERBOSE) 
INSERT INTO approval_history (
    staged_house_id,
    original_house_id,
    original_name,
    approved_by
) VALUES (
    '00000000-0000-0000-0000-000000000000'::uuid,
    '00000000-0000-0000-0000-000000000000'::uuid,
    'Test',
    'test@example.com'
);
