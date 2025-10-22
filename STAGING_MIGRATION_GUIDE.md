# Staging Tables Migration Guide

## 📋 Overview

This migration creates the database foundation for the web scraper project:
- **5 new tables** for staging scraped data
- **Row Level Security (RLS)** policies for admin-only access
- **Helper functions** for moderation workflow
- **Audit trail** for all changes

---

## 🚀 Running the Migration

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project: https://supabase.com/dashboard/project/xctottgirqkkmjmutoon
2. Navigate to **SQL Editor** (left sidebar)
3. Click **"New Query"**
4. Copy the entire contents of `migration_staging_tables.sql`
5. Paste into the query editor
6. Click **"Run"** (or press Ctrl+Enter)
7. Verify success - should see "Success. No rows returned"

### Option 2: Command Line (Using psql)

```bash
# Make sure you have your Supabase database connection string
psql "postgresql://postgres:[PASSWORD]@db.xctottgirqkkmjmutoon.supabase.co:5432/postgres" -f migration_staging_tables.sql
```

### Option 3: Python Script (Automated)

I can create a Python script that runs the migration using the Supabase client if you prefer.

---

## ✅ Verification Steps

After running the migration, verify everything is set up correctly:

### 1. Check Tables Were Created

Run this query in Supabase SQL Editor:

```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (
  table_name LIKE 'staged_%' 
  OR table_name IN ('scraping_log', 'moderation_audit', 'scraper_config')
)
ORDER BY table_name;
```

**Expected output:**
```
moderation_audit    | BASE TABLE
scraper_config      | BASE TABLE
scraping_log        | BASE TABLE
staged_accessories  | BASE TABLE
staged_houses       | BASE TABLE
```

### 2. Check RLS is Enabled

```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('staged_houses', 'staged_accessories', 'scraping_log', 'moderation_audit', 'scraper_config');
```

**Expected output:** All should show `rowsecurity = t` (true)

### 3. Check Default Configuration

```sql
SELECT key, value, description 
FROM scraper_config
ORDER BY key;
```

**Expected output:**
```
confidence_thresholds | {"auto_approve": 0.90, "recommend": 0.70, "review": 0.50}
enabled_sources       | ["dept56_retired", "replacements"]
rate_limits           | {"dept56_official": 1, "dept56_retired": 2, "replacements": 1}
timeout_seconds       | {"request": 30, "page_load": 45}
user_agents           | ["Mozilla/5.0..."]
```

### 4. Test Helper Function

```sql
SELECT * FROM get_pending_items_summary();
```

**Expected output:**
```
item_type  | total_pending | high_confidence | medium_confidence | low_confidence
-----------+---------------+-----------------+-------------------+---------------
house      |             0 |               0 |                 0 |              0
accessory  |             0 |               0 |                 0 |              0
```

---

## 📊 Table Descriptions

### `staged_houses`
Stores scraped house data before applying to production. Each row represents one scraped item with confidence scores and source tracking.

**Key columns:**
- `original_house_id` - Links to existing house (NULL for new imports)
- `overall_confidence_score` - 0.00 to 1.00 confidence in the match
- `status` - pending, approved, rejected, needs_review
- `changed_fields` - JSONB showing what will change if approved

### `staged_accessories`
Same structure as `staged_houses` but for accessories.

### `scraping_log`
Detailed log of every scraping attempt for debugging and monitoring.

**Useful for:**
- Identifying problematic searches
- Tracking success rates by source
- Performance monitoring
- Error analysis

### `moderation_audit`
Complete audit trail of all moderation decisions.

**Enables:**
- Rollback capability
- Accountability
- Decision tracking
- Change history

### `scraper_config`
Runtime configuration for the scraper (rates, thresholds, etc.)

**Benefits:**
- No code changes needed to adjust behavior
- Can disable problematic sources
- A/B test different thresholds
- Emergency rate limiting

---

## 🔒 Security & Permissions

### RLS Policies Applied

**Admins (authenticated users in `admin_users` table):**
- ✅ Full read/write access to `staged_houses` and `staged_accessories`
- ✅ Read access to logs and audit tables
- ✅ Read access to scraper config

**Service Role (Python scraper using service_role_key):**
- ✅ Can insert/update staging tables
- ✅ Can write to scraping_log
- ❌ Cannot modify production `houses` or `accessories` tables

**Regular users:**
- ❌ No access to any staging tables (completely isolated)

---

## 🧪 Testing the Migration

### Test 1: Insert Sample Staged House

```sql
INSERT INTO staged_houses (
  item_number, 
  name, 
  intro_year,
  overall_confidence_score,
  dept56_retired_url
) VALUES (
  '56.54305',
  'Robbie''s Robot Factory',
  2006,
  0.95,
  'https://retiredproducts.department56.com/products/robbies-robot-factory'
);

-- Verify insert
SELECT * FROM staged_houses;
```

### Test 2: Check Pending Summary

```sql
SELECT * FROM get_pending_items_summary();
```

Should now show 1 pending house with high confidence.

### Test 3: Insert Scraping Log

```sql
INSERT INTO scraping_log (
  search_query,
  item_type,
  source_site,
  results_found,
  best_match_name,
  success,
  execution_time_ms
) VALUES (
  'Robbie''s Robot Factory',
  'house',
  'dept56_retired',
  1,
  'Robbie''s Robot Factory',
  true,
  1250
);

-- Verify
SELECT * FROM scraping_log ORDER BY created_at DESC LIMIT 1;
```

### Test 4: Clean Up Test Data

```sql
DELETE FROM scraping_log WHERE search_query = 'Robbie''s Robot Factory';
DELETE FROM staged_houses WHERE item_number = '56.54305';
```

---

## 🐛 Troubleshooting

### Error: "relation already exists"
**Solution:** Tables already created. Either:
1. Skip the migration (already done)
2. Run the ROLLBACK section first to clean up
3. Use `CREATE TABLE IF NOT EXISTS` (already in the script)

### Error: "admin_users does not exist"
**Solution:** RLS policies reference `admin_users` table. Make sure your main database has this table. Check with:
```sql
SELECT * FROM admin_users LIMIT 1;
```

### Error: "permission denied for table"
**Solution:** Make sure you're running as a superuser or service_role. In Supabase dashboard, this should work automatically.

### Indexes not created
**Solution:** Indexes are optional for functionality but recommended for performance. If they fail, the migration will still work.

---

## 📈 Next Steps After Migration

Once migration is successful:

1. **Test Access** - Verify you can query staging tables from your admin account
2. **Build Python Scraper** - Connect to these tables using Supabase Python client
3. **Create Moderation UI** - Add React components to view/approve staged items
4. **Run Test Scrapes** - Start with 5-10 items to validate the workflow

---

## 🔄 Rollback Instructions

If you need to completely remove all staging tables:

```sql
-- WARNING: This will delete all staged data permanently!

DROP TRIGGER IF EXISTS update_staged_houses_updated_at ON staged_houses;
DROP TRIGGER IF EXISTS update_staged_accessories_updated_at ON staged_accessories;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS get_pending_items_summary();
DROP TABLE IF EXISTS moderation_audit CASCADE;
DROP TABLE IF EXISTS scraping_log CASCADE;
DROP TABLE IF EXISTS scraper_config CASCADE;
DROP TABLE IF EXISTS staged_accessories CASCADE;
DROP TABLE IF EXISTS staged_houses CASCADE;
```

---

## 📞 Support

If you encounter any issues:
1. Check the Supabase logs (Dashboard → Logs)
2. Verify your admin_users table exists and has your email
3. Test with the verification queries above
4. Share the error message for debugging

Ready to run the migration? Let me know if you need any help! 🚀
