# Form Layout Update - October 18, 2025

## Changes Made

Reorganized the Edit/Add House and Edit/Add Accessory forms for better space utilization and visual clarity.

## House Form Layout

### Before
- 2-column grid with all fields
- Photo preview displayed separately below fields
- Year fields took up full column width

### After
- **House Name**: Full width at top
- **Year Fields**: Compact 2-column row (Released Year | Purchased Year) with max-width constraint
- **Photo Section**: File input with thumbnail preview side-by-side
  - File chooser takes flexible width
  - 20x20 thumbnail displayed immediately to the right
  - Border and rounded corners for polish
- **Description, SKU, Notes**: Full width below photo section

### Benefits
- More compact layout saves vertical space
- Year fields don't waste horizontal space
- Photo preview is immediately visible next to upload button
- Cleaner visual hierarchy

## Accessory Form Layout

### Before
- 2-column grid mixing name and purchased year
- Photo preview displayed separately below fields

### After
- **Accessory Name**: Full width at top
- **Purchased Year**: Single compact field with max-width constraint
  - (Accessories don't have a "released year")
- **Photo Section**: File input with thumbnail preview side-by-side
  - Same layout as house form
- **Description, SKU, Notes**: Full width below photo section

### Benefits
- Consistent with house form design
- Purchased year field appropriately sized (doesn't need full width)
- Photo thumbnail immediately visible

## Photo Handling Behavior

### How It Works
- Selecting a new photo **replaces** the old photo URL in the database
- The old photo file remains in Supabase Storage but is no longer referenced
- No explicit delete button needed - selecting a new photo automatically overwrites

### Storage Details
- Photos uploaded to: `supabase.storage/dept56-images/uploads/`
- Filename format: `{timestamp}-{random}.{ext}`
- Old photos become orphaned files (not automatically deleted)

### If You Need Photo Deletion
If you want to add a red "X" button to delete the current photo:

```tsx
{photoUrl && (
  <div className="relative">
    <img src={photoUrl} alt="preview" className="h-20 w-20 rounded-xl object-cover border border-gray-300" />
    <button
      type="button"
      onClick={() => setPhotoUrl(undefined)}
      className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-700"
    >
      ×
    </button>
  </div>
)}
```

This would:
- Clear the photo preview
- Save with `photo_url: undefined` (removes reference from database)
- Old file remains in storage (could be cleaned up manually or with a cron job)

## Visual Improvements

### Thumbnail Styling
- **Size**: 20x20 pixels (compact but visible)
- **Shape**: Rounded corners (rounded-xl)
- **Border**: Light gray border for definition
- **Object Fit**: Cover (maintains aspect ratio, fills square)
- **Flex Shrink**: 0 (prevents squashing)

### Year Fields
- **Max Width**: Constrained to prevent excessive stretching
- **Grid**: 2 columns for houses, single column for accessories
- **Placeholder**: Updated to remove "e.g.," prefix for cleaner look

## Code Changes

### Files Modified
- `src/DeptApp.tsx`
  - HouseForm component (lines ~540-607)
  - AccessoryForm component (lines ~725-792)

### Key Changes
1. Removed `sm:grid-cols-2` wrapper around all fields
2. Added dedicated year row with `grid-cols-2` and `max-w-md`
3. Moved photo thumbnail into same Field as file input
4. Used `flex items-start gap-3` for horizontal layout
5. Added `flex-1` to file input and `flex-shrink-0` to thumbnail

## Testing Checklist

- [x] House form displays correctly
- [x] Accessory form displays correctly
- [x] Year fields are appropriately sized
- [x] Photo thumbnail appears next to file chooser
- [x] Selecting new photo updates thumbnail immediately
- [x] Saving house/accessory with new photo works
- [x] Editing existing item shows current photo thumbnail
- [x] Form is responsive (test on different screen sizes)

## Future Enhancements

If needed, consider:
1. **Photo Delete Button**: Add red X to explicitly remove photo
2. **Photo Cropping**: Add image cropper before upload
3. **Storage Cleanup**: Cron job to remove orphaned images
4. **Multiple Photos**: If needed in future (would require schema change)
5. **Drag & Drop**: Enhanced UX for photo upload

## Related Files

- `src/DeptApp.tsx` - Main component with forms
- `src/lib/database.ts` - Photo upload/delete functions
- `supabase-schema.sql` - Database schema with photo_url field
