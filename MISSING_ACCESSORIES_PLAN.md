# Missing Accessories Feature - Implementation Plan

## Goal
Flag accessories that are mentioned/linked to houses in the user's database but don't exist as separate items

## How Department 56 Products Work
- **Houses/Buildings**: Main collectible items (e.g., "Reindeer Stables")
- **Accessories**: Separate pieces that complement buildings (e.g., "Donder", "Blitzen")
- **Sets**: Sometimes sold together, sometimes individually

## Detection Strategy

### 1. Parse Product Descriptions
Many house descriptions mention included accessories:
- "Includes Donder and Blitzen figurines"
- "Comes with 3 accessories"
- "Set includes building and 2 figures"

### 2. Check Department 56 Product Pages
- House product pages often list "Related Accessories" or "Coordinates With"
- Individual accessory SKUs are often listed

### 3. Cross-Reference with User's Collection
- User has House A in database
- Scraper finds House A mentions Accessory B
- Check if user has Accessory B in accessories table
- If not → flag as "Missing Accessory"

## Implementation Steps

### Phase 1: Extend Parser
- Add accessory extraction to product_parser.py
- Parse "includes", "comes with", "coordinates with" from descriptions
- Extract accessory names and SKUs if available

### Phase 2: Create Accessory Suggestions Table
```sql
CREATE TABLE accessory_suggestions (
  id UUID PRIMARY KEY,
  house_id UUID REFERENCES houses(id),
  accessory_name TEXT,
  accessory_sku TEXT,
  reason TEXT, -- "mentioned_in_description", "coordinates_with", etc.
  confidence_score FLOAT,
  scraped_from_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Phase 3: Add UI Section
- "Missing Accessories" card in Data Review tab
- Show accessories the scraper found related to user's houses
- "Add to Collection" button to create new accessory record

## Example Flow

User has: "Reindeer Stables, Donder & Blitzen" (building)
Scraper finds on dept56.com:
- Main product: Building SKU #b09360
- Includes: Donder (SKU 808928), Blitzen (SKU 808929)

Scraper checks accessories table:
- Donder: NOT FOUND
- Blitzen: NOT FOUND

Creates suggestions:
- "Add Donder as an accessory to your collection?"
- "Add Blitzen as an accessory to your collection?"

## Questions to Answer
1. Should we auto-create accessories or just suggest them?
2. How do we handle accessories that come WITH a building vs sold separately?
3. Should we track which accessories user already has but separately purchased?
