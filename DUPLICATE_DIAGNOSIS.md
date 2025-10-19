# Duplicate Houses Diagnosis and Fix

## Problem
The gallery is showing duplicate houses with the same name and image, but with different accessory counts. This indicates duplicate records in the database.

## Root Cause
The batch processing script likely inserted duplicate house records during the data migration. This could have happened if:
1. The script was run multiple times
2. Some documents had slightly different formatting that wasn't detected as duplicates
3. The database wasn't fully cleared before re-running the import

## Evidence
From the screenshot:
- "Alfie's Toy School For Elves Early Release" appears twice
- Same image, same name
- One shows "1 accessory", the other shows nothing

## Diagnosis Steps

### 1. Run Diagnostic SQL
Execute `diagnose_duplicates.sql` in Supabase SQL Editor to:
- Find all houses with duplicate names
- Show their IDs, creation dates, and accessory counts
- Identify which records to keep vs delete

### 2. Review Results
Look for:
- How many duplicates exist
- Which house has more complete data (more accessories, fields filled)
- Creation timestamps to determine which is the original

## Fix Strategy

### Option 1: Automated Fix (Recommended if many duplicates)
Run `fix_duplicates.sql` which will:
1. Keep the OLDEST record (earliest `created_at`) for each duplicate name
2. Transfer all accessories, collections, and tags to the kept record
3. Delete the duplicate records
4. Verify no duplicates remain

**IMPORTANT**: 
- Backup your database first!
- Review the diagnostic output before running the fix
- The script keeps the oldest record assuming it's the original

### Option 2: Manual Fix (Recommended if few duplicates)
For each duplicate:
1. Identify the correct record to keep
2. Manually transfer any unique accessories/collections/tags
3. Delete the duplicate record

### Option 3: Re-run Import (Nuclear option)
If data quality is poor:
1. Run `clear_database.sql`
2. Re-run `batch_process.py` with the Word documents
3. Verify no duplicates this time

## Prevention
To prevent this in the future:

### Update batch_process.py
Add duplicate detection before inserting:

```python
# Before creating a house, check if it exists
existing = supabase.table('houses').select('id').eq('name', house_name).execute()
if existing.data:
    print(f"⚠️  House '{house_name}' already exists, skipping...")
    continue
```

### Add Database Constraint
Add a unique constraint on house names (optional):

```sql
-- Only do this if you want to enforce unique names
ALTER TABLE houses 
ADD CONSTRAINT houses_name_unique UNIQUE (name);
```

Note: This might not be desired if you truly want to allow houses with the same name.

## Verification After Fix

Run these queries:
```sql
-- Should return 0 rows
SELECT name, COUNT(*) 
FROM houses 
GROUP BY name 
HAVING COUNT(*) > 1;

-- Should match expected count (~456)
SELECT COUNT(*) FROM houses;

-- Check specific house
SELECT COUNT(*) 
FROM houses 
WHERE name LIKE '%Alfie%Toy School%';
-- Should return 1
```

## Files Created
1. `check_duplicates.sql` - Basic duplicate check queries
2. `diagnose_duplicates.sql` - Comprehensive diagnostic queries
3. `fix_duplicates.sql` - Automated fix script
4. `DUPLICATE_DIAGNOSIS.md` - This file

## Recommendation
1. Run `diagnose_duplicates.sql` first to see the extent of the problem
2. If only a few duplicates (< 10), fix manually
3. If many duplicates (> 10), review and run `fix_duplicates.sql`
4. After fixing, refresh the frontend to verify the gallery shows unique houses only
5. Update `batch_process.py` to prevent future duplicates
