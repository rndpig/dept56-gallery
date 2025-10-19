# UI Layout Updates - Manage Tab

## Changes Made

### Layout Restructuring

The Manage tab has been reorganized for a more intuitive workflow when editing houses and their linked accessories.

#### Previous Layout (v1):
```
┌─────────────────────────────────┬─────────────────┐
│ House Form                      │ Link Form       │
│                                 │ Collections     │
│ Linked Accessories (below)      │ Tags            │
├─────────────────────────────────┤                 │
│ Accessory Form                  │                 │
└─────────────────────────────────┴─────────────────┘
```

#### Previous Layout (v2):
```
Top Row (side-by-side):
┌────────────────────────────────┬──────────────────┐
│ House Form (60%)               │ Linked           │
│                                │ Accessories (40%)│
│                                │                  │
└────────────────────────────────┴──────────────────┘

Bottom Row:
┌────────────────────────────────┬──────────────────┐
│ Accessory Form (60%)           │ Link Form        │
│                                │ Collections      │
│                                │ Tags             │
│                                │ Data Tools       │
└────────────────────────────────┴──────────────────┘
```

#### Current Layout (v3) - MOST INTUITIVE:
```
Top Row (side-by-side):
┌────────────────────────────────┬──────────────────┐
│ House Form (60%)               │ Linked           │
│                                │ Accessories (40%)│
│                                ├──────────────────┤
│                                │ Accessory        │
│                                │ Form (40%)       │
└────────────────────────────────┴──────────────────┘

Bottom Row (utilities):
┌──────────────┬──────────────┬──────────────┐
│ Link Form    │ Collections  │ Tags         │
│              │              │ Data Tools   │
└──────────────┴──────────────┴──────────────┘
```

### Right Column Organization

**All accessory-related functionality is now in the right column:**

1. **Linked Accessories Panel** (when editing a house)
   - Shows immediately when house is selected
   - Compact display with thumbnails and descriptions
   - "Edit" buttons to load accessories

2. **Accessory Form** (always visible)
   - Positioned directly below linked accessories
   - Edit or create accessories
   - Full form with all fields (including notes)

**Benefits of this arrangement:**
- **Logical grouping**: House on left, all accessory stuff on right
- **Vertical workflow**: Select house → see accessories → edit accessory (all in one column)
- **No searching**: Everything accessory-related is in the right panel
- **Efficient scrolling**: Scroll down in right column to go from viewing accessories to editing them

### Linked Accessories Panel Updates

**Display**:
- ✅ Thumbnail image
- ✅ Accessory name
- ✅ Description (if present)
- ❌ Notes hidden (kept simple, available in edit form)
- ✅ "Edit" button for quick access

**Empty State**: 
- Shows "No accessories linked to this house yet" when a house has no linked accessories
- Panel only visible when editing an existing house

**Interaction**:
- Click "Edit" button to load the accessory into the form below
- Automatically scrolls to the accessory form

### Bottom Row - Utilities

**3-column grid for management tools:**
- Link form (for creating new links)
- Collections management
- Tags management
- Data tools (export, refresh)

These are separated from the main editing workflow as they're used less frequently.

### Benefits

1. **Vertical Organization**: All accessory work flows vertically in one column
2. **Spatial Relationship**: House and accessories grouped side-by-side
3. **Less Scanning**: Eyes don't need to jump around the screen
4. **Intuitive Flow**: 
   - Select house → see accessories (right, top)
   - Need to edit one? → form is right below
   - Need to add/link? → tools at bottom
5. **Efficient**: No need to scroll horizontally or search for forms
6. **Contextual**: Linked accessories only show when editing a house

### Technical Details

**Grid System**: 
- Top row: `lg:grid-cols-5` (5-column grid)
  - House form: `lg:col-span-3` (60%)
  - Right column: `lg:col-span-2` (40%) with `space-y-6` for vertical stacking
- Bottom row: `lg:grid-cols-3` (3 equal columns)

**Right Column Stacking**:
- Uses `space-y-6` for vertical spacing
- Linked accessories card (conditional on editHouseId)
- Accessory form card (always visible)

**Responsive**: 
- On mobile/tablet: All cards stack vertically (full width)
- On desktop: Side-by-side layout with right column stacking

**Data Preservation**:
- Notes field is still in AccessoryForm
- Notes field is still saved to database
- Only hidden in the compact linked accessories display

### User Experience

When editing data from a Word document:

1. **Select a house** from dropdown (left)
2. **See linked accessories** in top-right panel
3. **Edit house details** as needed (left)
4. **Click "Edit" on any accessory** → loads in form directly below
5. **Edit accessory** (right, scrolled down slightly)
6. **Save** and return to top of right column
7. **Repeat** for other accessories
8. Complete entire document's data entry efficiently

The vertical flow in the right column means:
- View → Edit → Save → View next → Edit → Save
- All in one smooth vertical motion
- No jumping between left and right
- No scrolling back up to see what's next
