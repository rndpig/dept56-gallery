# Cleanup: Remove "Imported from DOCX" Text

## Problem
During the initial data import from Word documents, some records got "Imported from DOCX" text added to their notes or description fields. This text needs to be removed from the database.

## Solution Options

### Option 1: SQL Script (Recommended - Fastest)

**File**: `cleanup_imported_text.sql`

1. Open Supabase Dashboard
2. Navigate to SQL Editor
3. Copy the contents of `cleanup_imported_text.sql`
4. Paste and run the script
5. Check the verification results at the end

**What it does:**
- Removes "Imported from DOCX" from notes fields
- Removes "Imported from DOCX" from description fields
- Cleans up empty strings (sets to NULL)
- Works on both houses and accessories tables
- Shows verification counts at the end

**SQL Commands:**
```sql
UPDATE houses SET notes = TRIM(REPLACE(notes, 'Imported from DOCX', ''))
WHERE notes LIKE '%Imported from DOCX%';

UPDATE houses SET description = TRIM(REPLACE(description, 'Imported from DOCX', ''))
WHERE description LIKE '%Imported from DOCX%';

UPDATE accessories SET notes = TRIM(REPLACE(notes, 'Imported from DOCX', ''))
WHERE notes LIKE '%Imported from DOCX%';

UPDATE accessories SET description = TRIM(REPLACE(description, 'Imported from DOCX', ''))
WHERE description LIKE '%Imported from DOCX%';
```

### Option 2: TypeScript Cleanup Script

**File**: `scripts/cleanup-imported-text.ts`

Run from command line:
```bash
npx tsx scripts/cleanup-imported-text.ts
```

**What it does:**
- Connects to Supabase
- Fetches all houses and accessories
- Removes "Imported from DOCX" from each record
- Shows progress as it cleans
- Reports final statistics

**Advantages:**
- Shows which specific records were cleaned
- More detailed logging
- Can be modified for other cleanup tasks

**Disadvantages:**
- Slower than SQL (processes records one-by-one)
- Requires Node.js and tsx package

## Fields Affected

### Houses Table
- `notes` field
- `description` field

### Accessories Table
- `notes` field
- `description` field

## Verification

After running the cleanup, verify with this SQL query:

```sql
-- This should return zero results
SELECT 
  'houses' as table_name, 
  name, 
  notes, 
  description 
FROM houses 
WHERE notes LIKE '%Imported from DOCX%' 
   OR description LIKE '%Imported from DOCX%'

UNION ALL

SELECT 
  'accessories' as table_name, 
  name, 
  notes, 
  description 
FROM accessories 
WHERE notes LIKE '%Imported from DOCX%' 
   OR description LIKE '%Imported from DOCX%';
```

If this returns any rows, those records still have the unwanted text.

## Safety

Both scripts are **safe** because they:
- Only modify records that contain "Imported from DOCX"
- Use `TRIM()` to clean up extra whitespace
- Set empty strings to NULL (cleaner database)
- Don't delete any records
- Don't affect other data

## Backup Recommendation

Before running, consider backing up your data:

```sql
-- Export houses
COPY (SELECT * FROM houses) TO STDOUT WITH CSV HEADER;

-- Export accessories  
COPY (SELECT * FROM accessories) TO STDOUT WITH CSV HEADER;
```

Or use Supabase's built-in backup feature in the dashboard.

## Expected Results

After cleanup:
- ✅ All instances of "Imported from DOCX" removed
- ✅ Extra whitespace trimmed
- ✅ Empty notes/descriptions set to NULL
- ✅ Data remains otherwise intact
- ✅ No records deleted

## If Problems Occur

If something goes wrong:
1. Check Supabase logs for errors
2. Verify your RLS policies allow updates
3. Make sure you're authenticated correctly
4. Try the SQL script instead of the TypeScript script (or vice versa)
5. Contact support if data appears corrupted

## Alternative: Manual Cleanup

If you only have a few records, you can:
1. Go to Manage tab
2. Select each house/accessory
3. Edit the notes/description fields
4. Remove "Imported from DOCX" manually
5. Save

This is only practical for small datasets (< 20 records).
