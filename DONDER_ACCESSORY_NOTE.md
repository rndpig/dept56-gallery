# Quick Note: Donder Accessory Approval

## Current Situation
Donder (SKU 808928) is in the pending review list but has `original_house_id = NULL` because it doesn't exist in your database yet.

## Issue
The current `applyApproval()` function only handles UPDATES to existing houses, not CREATING new accessories.

## Temporary Workaround for Tonight
**DON'T approve Donder yet!** The current code will fail because:
```typescript
if (item.original_house_id) {
  // Update existing house
} else {
  throw new Error("New house import not yet implemented");
}
```

## Proper Solution (for next session)
Need to add logic to:
1. Detect if item is an accessory vs house
2. Create new accessory record in `accessories` table
3. Link it to related house in `house_accessory_links` table
4. Get user_id from session to assign ownership

## Code Needed
```typescript
async function createNewAccessory(item: StagedHouse, relatedHouseId: string) {
  const userId = (await supabase.auth.getUser()).data.user?.id;
  
  // Create accessory
  const { data: newAccessory } = await supabase
    .from("accessories")
    .insert({
      user_id: userId,
      name: item.name,
      notes: item.description,
      photo_url: item.primary_image_url
    })
    .select()
    .single();
  
  // Link to house
  await supabase
    .from("house_accessory_links")
    .insert({
      house_id: relatedHouseId,
      accessory_id: newAccessory.id
    });
}
```

## For Now
- Approve the 6 pending HOUSE updates only
- Leave Donder for next session when we implement accessory creation
- This is safer than rushing the feature with limited quota
