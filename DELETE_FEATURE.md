# Delete Functionality

## Overview
Added the ability to delete houses and accessories with confirmation dialogs to prevent accidental deletions.

## Features Implemented

### 1. Delete Functions
Added two delete handler functions in `DeptApp.tsx`:

- **`deleteHouse(houseId, houseName)`**
  - Shows confirmation dialog with house name
  - Warns that all links to accessories will be removed (but accessories remain)
  - Deletes the house from database
  - Refreshes data and clears the edit selection
  - Shows success/error alerts

- **`deleteAccessory(accessoryId, accessoryName)`**
  - Shows confirmation dialog with accessory name
  - Warns that all links to houses will be removed (but houses remain)
  - Deletes the accessory from database
  - Refreshes data and clears the edit selection
  - Shows success/error alerts

### 2. Form UI Updates

Both `HouseForm` and `AccessoryForm` now include:
- **Delete Button**: Red button that appears next to Save/Update button
- **Only shows when editing**: Delete button only appears when `initial.id` exists (not when creating new items)
- **Disabled during save**: Button is disabled while form is saving
- **Confirmation required**: Clicking triggers native browser confirmation dialog

Button appearance:
- Red background (`bg-red-600`)
- White text
- Hover effect (`hover:bg-red-700`)
- Positioned next to the Save/Update button

### 3. Button Text Changes
- Save buttons now show:
  - "Save House" / "Save Accessory" when creating new items
  - "Update House" / "Update Accessory" when editing existing items

## User Experience

### Deleting a House:
1. Select a house from the dropdown in Manage tab
2. Red "Delete" button appears next to "Update House" button
3. Click "Delete"
4. Confirmation dialog appears:
   ```
   Are you sure you want to delete "[House Name]"?
   
   This will also remove all links to accessories, but the accessories themselves will not be deleted.
   
   This action cannot be undone.
   ```
5. Click "OK" to confirm or "Cancel" to abort
6. If confirmed, house is deleted and success message appears
7. Form resets to "Create New House" mode

### Deleting an Accessory:
Same flow as houses, with appropriate messaging about house links.

## Safety Features

1. **Confirmation Dialog**: Native browser confirm() prevents accidental clicks
2. **Clear Warning**: Explains what will be deleted and what will remain
3. **Name Display**: Shows the item name in the confirmation for verification
4. **Cannot Undo Warning**: Makes it clear the action is permanent
5. **Only When Editing**: Delete button only appears when editing existing items, not when creating new ones
6. **Success Feedback**: Alert confirms successful deletion
7. **Error Handling**: Alert shows if deletion fails

## Database Impact

- **Houses**: Deleting a house removes all `house_accessory_links` entries, but accessories remain
- **Accessories**: Deleting an accessory removes all `house_accessory_links` entries, but houses remain
- **Cascading**: Database handles cleanup of related collections and tags links automatically
- **Images**: Photo URLs remain in storage (manual cleanup may be needed)

## Technical Details

- Uses existing `db.deleteHouse()` and `db.deleteAccessory()` functions
- Calls `loadData()` after deletion to refresh the UI
- Resets edit state with `setEditHouseId("")` / `setEditAccessoryId("")`
- Type-safe with proper TypeScript types including `id` field in `initial` prop
