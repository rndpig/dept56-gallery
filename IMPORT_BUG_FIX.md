# Import Bug Fix: Preventing Duplicate Items in Houses and Accessories Tables

## Problem Summary

Accessories were incorrectly appearing in the Houses gallery because 29 items existed in BOTH the `houses` and `accessories` tables.

## Root Cause

The batch import script (`scripts/batch_process.py`) had **NO duplicate detection**:

1. ❌ No check if item name already exists in the same table
2. ❌ No cross-table check (if accessory name exists in houses table or vice versa)
3. ❌ Lookup maps (`house_name_to_id`, `accessory_name_to_id`) were empty at script start
4. ❌ Running the import script multiple times would create duplicates
5. ❌ Parser misclassifications would result in same item in both tables

## Fixes Implemented

### 1. Pre-Load Existing Items (CRITICAL FIX)

**Before:**
```python
# Create lookup maps for linking
house_name_to_id = {}
accessory_name_to_id = {}
```

**After:**
```python
# Create lookup maps for linking
# Pre-populate with existing items from database to prevent duplicates
house_name_to_id = {}
accessory_name_to_id = {}

print("Loading existing items from database to prevent duplicates...")
try:
    # Load all existing houses
    existing_houses = self.supabase.table('houses').select('id, name').eq('user_id', self.user_id).execute()
    for house in existing_houses.data:
        house_name_to_id[house['name']] = house['id']
    print(f"  Found {len(existing_houses.data)} existing houses")
    
    # Load all existing accessories
    existing_accessories = self.supabase.table('accessories').select('id, name').eq('user_id', self.user_id).execute()
    for acc in existing_accessories.data:
        accessory_name_to_id[acc['name']] = acc['id']
    print(f"  Found {len(existing_accessories.data)} existing accessories")
except Exception as e:
    print(f"  ⚠️  Warning: Could not load existing items: {str(e)}")
    print("  Continuing without duplicate detection...")
```

**Impact:** Script now knows about ALL existing items before starting upload.

### 2. Duplicate Check for Houses (SAME-TABLE + CROSS-TABLE)

**Before:**
```python
# Insert house - NO CHECKS
response = self.supabase.table('houses').insert(house_record).execute()
```

**After:**
```python
house_name = house_data['name']

# DUPLICATE CHECK #1: Skip if already exists as a house
if house_name in house_name_to_id:
    print(f"  ⏭️  House already exists: {house_name}")
    skipped_duplicates.append({'type': 'house', 'name': house_name, 'reason': 'already in houses table'})
    continue

# DUPLICATE CHECK #2: Check if it exists as an accessory (CROSS-TABLE CHECK)
if house_name in accessory_name_to_id:
    print(f"  ⚠️  WARNING: '{house_name}' already exists as ACCESSORY - skipping house upload")
    skipped_duplicates.append({'type': 'house', 'name': house_name, 'reason': 'already exists as accessory'})
    errors.append({'type': 'house', 'name': house_name, 'error': 'Item already exists as accessory - possible parser misclassification'})
    continue

# Insert house - ONLY if passed both checks
response = self.supabase.table('houses').insert(house_record).execute()
```

**Impact:** 
- ✅ Won't create duplicate houses
- ✅ Won't create house if it already exists as accessory
- ✅ Logs warning if parser tries to upload same item to both tables

### 3. Duplicate Check for Accessories (SAME-TABLE + CROSS-TABLE)

**Before:**
```python
# Insert accessory - NO CHECKS
response = self.supabase.table('accessories').insert(acc_record).execute()
```

**After:**
```python
acc_name = acc_data['name']

# DUPLICATE CHECK #1: Skip if already exists as an accessory
if acc_name in accessory_name_to_id:
    print(f"  ⏭️  Accessory already exists: {acc_name}")
    skipped_duplicates.append({'type': 'accessory', 'name': acc_name, 'reason': 'already in accessories table'})
    continue

# DUPLICATE CHECK #2: Check if it exists as a house (CROSS-TABLE CHECK)
if acc_name in house_name_to_id:
    print(f"  ⚠️  WARNING: '{acc_name}' already exists as HOUSE - skipping accessory upload")
    skipped_duplicates.append({'type': 'accessory', 'name': acc_name, 'reason': 'already exists as house'})
    errors.append({'type': 'accessory', 'name': acc_name, 'error': 'Item already exists as house - possible parser misclassification'})
    continue

# Insert accessory - ONLY if passed both checks
response = self.supabase.table('accessories').insert(acc_record).execute()
```

**Impact:**
- ✅ Won't create duplicate accessories
- ✅ Won't create accessory if it already exists as house
- ✅ Logs warning if parser tries to upload same item to both tables

### 4. Enhanced Summary Reporting

**Before:**
```python
print(f"  Houses uploaded:      {total_houses}")
print(f"  Accessories uploaded: {total_accessories}")
print(f"  Errors:               {len(errors)}")
```

**After:**
```python
print(f"  Houses uploaded:      {total_houses}")
print(f"  Accessories uploaded: {total_accessories}")
print(f"  Duplicates skipped:   {len(skipped_duplicates)}")
print(f"  Errors:               {len(errors)}")

if skipped_duplicates:
    print(f"\n{'─'*70}")
    print("SKIPPED DUPLICATES:")
    print(f"{'─'*70}")
    for skip in skipped_duplicates[:20]:  # Show first 20
        print(f"  - {skip['type'].upper()}: {skip['name']} ({skip['reason']})")
```

**Impact:**
- ✅ Shows exactly which items were skipped
- ✅ Shows reason for skipping (same table vs. cross-table)
- ✅ Helps identify parser misclassifications

## Testing the Fix

### Scenario 1: Re-running Import on Existing Data
```bash
python scripts\batch_process.py "path\to\documents" --user-id YOUR_USER_ID
```

**Expected Result:**
```
Loading existing items from database to prevent duplicates...
  Found 249 existing houses
  Found 334 existing accessories

Processing documents...
  ⏭️  House already exists: A Stitch In Yule Time
  ⏭️  Accessory already exists: She'll Be Belle of the Ball
  ...

UPLOAD SUMMARY
  Houses uploaded:      0
  Accessories uploaded: 0
  Duplicates skipped:   583
  Errors:               0
```

### Scenario 2: Adding New Items
```bash
# Add new document to folder, then run import
python scripts\batch_process.py "path\to\documents" --user-id YOUR_USER_ID
```

**Expected Result:**
```
Loading existing items from database to prevent duplicates...
  Found 249 existing houses
  Found 334 existing accessories

Processing documents...
  ⏭️  House already exists: A Stitch In Yule Time
  ...
  ✅ House: NEW HOUSE NAME
  ✅ Accessory: NEW ACCESSORY NAME

UPLOAD SUMMARY
  Houses uploaded:      1
  Accessories uploaded: 1
  Duplicates skipped:   583
  Errors:               0
```

### Scenario 3: Parser Misclassification Detected
```bash
# If parser tries to upload "Basket Weaving 101" as both house AND accessory
python scripts\batch_process.py "path\to\documents" --user-id YOUR_USER_ID
```

**Expected Result:**
```
Processing documents...
  ✅ Accessory: Basket Weaving 101
  ...
  ⚠️  WARNING: 'Basket Weaving 101' already exists as ACCESSORY - skipping house upload

UPLOAD SUMMARY
  Errors: 1

ERRORS:
  - {'type': 'house', 'name': 'Basket Weaving 101', 'error': 'Item already exists as accessory - possible parser misclassification'}
```

## Benefits

1. **✅ Idempotent Imports** - Can run import script multiple times without creating duplicates
2. **✅ Cross-Table Protection** - Same item cannot exist in both houses and accessories tables
3. **✅ Parser Error Detection** - Logs warnings when parser misclassifies items
4. **✅ Safe Re-imports** - Can re-import all documents to update metadata without duplicating items
5. **✅ Clear Reporting** - Shows exactly what was skipped and why

## Migration Path

### For Fresh Imports (No Existing Data)
```bash
# 1. Clear database (optional)
python scripts\clear_database.py

# 2. Run import with new duplicate detection
python scripts\batch_process.py "path\to\documents" --user-id YOUR_USER_ID
```

### For Existing Data (Already Imported)
```bash
# 1. Fix existing duplicates first (if any)
python scripts\fix_wrong_table_items.py

# 2. Future imports will use new duplicate detection automatically
python scripts\batch_process.py "path\to\new\documents" --user-id YOUR_USER_ID
```

## Files Modified

- ✅ `scripts/batch_process.py` - Added duplicate detection logic
- ✅ `IMPORT_BUG_DIAGNOSIS.md` - Root cause analysis
- ✅ `IMPORT_BUG_FIX.md` - This fix documentation

## Future Enhancements (Optional)

1. **Database Unique Constraint**
   ```sql
   ALTER TABLE houses ADD CONSTRAINT houses_name_user_unique UNIQUE (name, user_id);
   ALTER TABLE accessories ADD CONSTRAINT accessories_name_user_unique UNIQUE (name, user_id);
   ```
   This would enforce uniqueness at the database level as a safety net.

2. **Update vs. Insert Logic**
   Instead of skipping duplicates, optionally update existing records with new metadata:
   ```python
   if house_name in house_name_to_id:
       # Update existing house instead of skipping
       house_id = house_name_to_id[house_name]
       self.supabase.table('houses').update(house_record).eq('id', house_id).execute()
   ```

3. **Dry-Run Mode**
   Add `--dry-run` flag to preview what would be imported without actually inserting:
   ```python
   parser.add_argument('--dry-run', action='store_true', help='Preview import without making changes')
   ```

## Conclusion

The batch import script now has **comprehensive duplicate detection** with:
- ✅ Same-table checking (no duplicate houses, no duplicate accessories)
- ✅ Cross-table checking (same name cannot be house AND accessory)
- ✅ Pre-loading existing items before import
- ✅ Clear reporting of skipped items
- ✅ Error logging for parser misclassifications

**This prevents the duplicate import bug from happening again.**
