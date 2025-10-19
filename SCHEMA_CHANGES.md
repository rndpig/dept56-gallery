# Database Schema Changes

## Changes Made

### 1. Type Definitions Updated (`src/types/database.ts`)
- Added `description?: string` field to both `House` and `Accessory` types
- Removed `purchased_on?: string` field from both types (date field)
- Kept `purchased_year?: number` field
- Cleaned up `user_id` references

### 2. SQL Migration Created (`add_description_field.sql`)
Run this in Supabase SQL Editor to update the database:
```sql
ALTER TABLE houses ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE accessories ADD COLUMN IF NOT EXISTS description TEXT;
```

The `purchased_on` columns are not dropped to preserve existing data.

### 3. Form Updates
Both `HouseForm` and `AccessoryForm` have been updated:
- Removed "Purchased on (date)" field
- Added "Description" textarea field (separate from Notes)
- Renamed "Year" to "Released Year" for houses
- "Purchased Year" remains for both
- **Notes field is preserved in both edit forms** (for SKUs and additional metadata)

### 4. Field Purpose
- **Description**: Brief description of the item (from Word docs)
- **Notes**: Additional notes, SKUs, and other metadata (only in edit forms)

### 5. Linked Accessories Display - Enhanced Layout
When editing a house in the Manage tab:
- **New Layout**: Linked accessories now appear **to the right of the house form** (more intuitive side-by-side view)
- Each accessory shows:
  - Thumbnail image (if available)
  - Name
  - Description only (notes are hidden in the compact view but preserved in edit form)
  - "Edit" button to quickly edit that accessory
- Shows "No accessories linked to this house yet" message if none
- Clicking "Edit" loads the accessory into the edit form and smoothly scrolls to it
- This enables editing a house and all its accessories in a single session

### 6. Manage Tab Layout (NEW STRUCTURE)
**Top Row** (side-by-side):
- Left (60%): House edit/add form
- Right (40%): Linked accessories panel (only when editing a house)

**Bottom Row**:
- Left (60%): Accessory edit/add form
- Right (40%): Link form, Collections, Tags, Data Tools

## Next Steps

### Ready to Test:
1. ✅ Run the SQL migration in Supabase
2. ✅ Forms are ready with new description field
3. ✅ Linked accessories display implemented with intuitive layout
4. ✅ Notes field preserved in edit forms but hidden in linked accessories compact view
5. ⏳ Test data migration and forms
6. ⏳ Test linked accessories workflow

### Workflow Benefits:
Now you can:
1. Select a house to edit from the dropdown
2. **See all accessories linked to that house in the right panel** (side-by-side view)
3. Click "Edit" on any linked accessory to edit it
4. Switch between editing the house and its accessories seamlessly
5. Complete data entry for an entire Word document in one session
6. Description shown in compact view, full details (including notes) available in edit form
