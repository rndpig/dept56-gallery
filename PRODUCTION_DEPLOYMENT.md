# Production Deployment Guide
**Date:** October 18, 2025  
**Purpose:** Clear database and re-import all Word documents with enhanced parser

## Prerequisites
✅ Python environment configured
✅ Supabase credentials in `.env` file
✅ All Word documents in `\\DilgerNAS\Public\Media\Day NP Files`

## Step 1: Run Database Migration

Open Supabase SQL Editor and execute these scripts **in order**:

### 1.1 Apply Field Additions
```sql
-- File: migration_add_all_fields.sql
-- This adds: SKU, description, price, retired_year, collection, series to houses and accessories
```
Run the entire contents of `migration_add_all_fields.sql`

### 1.2 Verify Migration
```sql
-- Check houses table structure
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'houses'
ORDER BY ordinal_position;

-- Check accessories table structure
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'accessories'
ORDER BY ordinal_position;
```

Expected new columns:
- houses: sku, description, price, retired_year, collection, series
- accessories: sku, description, year, price, retired_year, collection, series

## Step 2: Clear Existing Data

⚠️ **WARNING: This will delete ALL existing data!**

In Supabase SQL Editor, run:
```sql
-- File: clear_database.sql
```
Run the entire contents of `clear_database.sql`

Verify all tables are empty:
```sql
SELECT 'houses' as table_name, COUNT(*) FROM houses
UNION ALL SELECT 'accessories', COUNT(*) FROM accessories
UNION ALL SELECT 'house_accessory_links', COUNT(*) FROM house_accessory_links;
```
All counts should be **0**.

## Step 3: Test Parser on Sample Documents

Before batch processing, test on a few documents:

```powershell
# Test multi-accessory document
python scripts\docx_parser_simple.py "\\DilgerNAS\Public\Media\Day NP Files\ACC Follow the Leader 2016 Fisher Price Pull Toy Factory toot-toot Tester.docx"

# Test single-accessory document
python scripts\docx_parser_simple.py "\\DilgerNAS\Public\Media\Day NP Files\Frosty Pines Outfitters 2002 Ready for Adventure.docx"

# Check parsed output
Get-ChildItem parsed_output\*.json | Select-Object -Last 2
Get-ChildItem parsed_output\images | Select-Object -Last 5
```

## Step 4: Batch Process All Documents

Run the batch processor to parse all Word documents:

```powershell
# Get your Supabase credentials from .env file
# You'll need your email and password

python scripts\batch_process.py "\\DilgerNAS\Public\Media\Day NP Files" --email "your-email@example.com" --password "your-password"
```

**What this does:**
1. Authenticates with Supabase
2. Finds all `.docx` files in the directory
3. Parses each document (text + images)
4. Uploads houses and accessories to Supabase
5. Creates house-accessory links
6. Saves consolidated results to `parsed_output/consolidated_results.json`
7. Saves summary to `parsed_output/upload_summary.json`

**Expected output:**
- Houses: ~100 (one per document)
- Accessories: ~100+ (varies per document)
- Images: ~200+ extracted to `parsed_output/images/`

## Step 5: Verify Upload

Check Supabase database:

```sql
-- Count records
SELECT 'houses' as table, COUNT(*) as count FROM houses
UNION ALL SELECT 'accessories', COUNT(*) FROM accessories
UNION ALL SELECT 'links', COUNT(*) FROM house_accessory_links;

-- Sample houses with new fields
SELECT name, sku, price, year, retired_year, collection, series
FROM houses
LIMIT 10;

-- Sample accessories with new fields
SELECT name, sku, price, year, retired_year, collection, series
FROM accessories
LIMIT 10;

-- Check links
SELECT 
  h.name as house_name,
  a.name as accessory_name
FROM house_accessory_links hal
JOIN houses h ON h.id = hal.house_id
JOIN accessories a ON a.id = hal.accessory_id
LIMIT 20;
```

## Step 6: Upload Images to Supabase Storage

**Note:** The batch processor extracts images locally but doesn't upload to Supabase Storage yet.

Manual upload process:
1. Go to Supabase Storage → `dept56-images` bucket
2. Create folder with your user ID
3. Upload images from `parsed_output/images/`

OR: Use a separate upload script (to be created)

## Step 7: Update TypeScript Types (if needed)

The types in `src/types/database.ts` should already include the new fields.
Verify:

```typescript
export interface House {
  // ... existing fields
  sku?: string;
  description?: string;
  price?: number;
  retired_year?: number;
  collection?: string;
  series?: string;
}

export interface Accessory {
  // ... existing fields
  sku?: string;
  description?: string;
  price?: number;
  year?: number;
  retired_year?: number;
  collection?: string;
  series?: string;
}
```

## Troubleshooting

### Issue: Authentication fails
- Check `.env` file has correct `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- Verify your email/password are correct
- Check Supabase dashboard for user account

### Issue: Permission denied on insert
- Verify RLS policies allow inserts for authenticated users
- Check you're using the correct user ID
- Review `fix_rls_policies.sql` if needed

### Issue: Duplicate key errors
- Database wasn't fully cleared
- Re-run `clear_database.sql`

### Issue: Missing fields in database
- Migration wasn't applied
- Re-run `migration_add_all_fields.sql`

### Issue: Parser errors on specific documents
- Check `upload_summary.json` for error details
- Manually review problematic documents
- Fix document format or update parser logic

## Success Criteria

✅ Migration applied successfully (new columns visible)
✅ Old data cleared (all counts = 0)
✅ All documents parsed without critical errors
✅ Houses uploaded: ~100
✅ Accessories uploaded: ~100+
✅ Links created successfully
✅ Images extracted locally: ~200+
✅ Sample queries return expected data

## Files Created/Modified

**New Files:**
- `migration_add_all_fields.sql` - Comprehensive migration
- `clear_database.sql` - Clear all data
- `scripts/batch_process.py` - Batch processor
- `PRODUCTION_DEPLOYMENT.md` - This guide

**Modified Files:**
- `scripts/docx_parser_simple.py` - Added image extraction
- `parsed_output/images/` - Extracted images directory

## Next Steps (Post-Deployment)

1. Update UI forms to display new fields
2. Add filtering/sorting by collection, series, year ranges
3. Upload images to Supabase Storage
4. Update photo_url fields to point to storage
5. Add data validation/cleanup UI
6. Create backup/export functionality
