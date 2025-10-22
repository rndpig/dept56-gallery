# APPROVAL HISTORY MIGRATION INSTRUCTIONS

## ⚠️ IMPORTANT: Run this BEFORE testing the approval features

This migration creates a backup system that stores original data before any changes are applied.

## Steps to Run:

1. **Go to Supabase SQL Editor:**
   - Visit: https://supabase.com/dashboard
   - Select your project
   - Click "SQL Editor" in the left sidebar

2. **Copy and Run the Migration:**
   - Open the file: `migration_approval_history.sql`
   - Copy ALL contents
   - Paste into Supabase SQL Editor
   - Click "Run" or press Ctrl+Enter

3. **Verify Success:**
   - You should see: "Success. No rows returned"
   - Check Tables list - you should see `approval_history`

## What This Creates:

- **approval_history table**: Stores original values before each approval
- **Indexes**: For fast lookups
- **RLS Policies**: Same admin access as other tables

## What It Does:

When you click "Approve":
1. ✅ Backs up current data to `approval_history`
2. ✅ Updates the `houses` table with new data
3. ✅ Records who approved and when
4. ✅ Enables "Undo" button to revert changes

## Safety Features:

- **Backup Before Change**: Original data saved BEFORE overwriting
- **Undo Capability**: Restore original values with one click
- **Audit Trail**: See who approved what and when
- **No Data Loss**: All changes are reversible

---

**After running this migration, you can safely test the approval features!**
