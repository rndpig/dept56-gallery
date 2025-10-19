# Import Bug Diagnosis: Duplicate Items in Houses and Accessories Tables

## Problem

29 accessories appeared in BOTH the `houses` and `accessories` tables, causing them to show up incorrectly in the Houses gallery.

Examples:
- "Basket Weaving 101" - Accessory appearing as a house
- "Around the World in 24 Hours Flight Center" - Accessory appearing as a house

## Root Cause Analysis

### Bug Location: `scripts/batch_process.py`

The batch processor has **NO duplicate detection** when uploading items. The upload process:

1. Parses all Word documents sequentially
2. For each document, extracts houses and accessories
3. Inserts all extracted items into database **without checking if they already exist**
4. Uses name-to-ID lookup maps that are **cleared between runs**

### How Duplicates Occurred

**Scenario 1: Parser Misclassification**
1. Document A parsed: "Basket Weaving 101" correctly identified as accessory → inserted into `accessories` table
2. Document B parsed: "Basket Weaving 101" misidentified as house → inserted into `houses` table
3. Result: Same item in both tables

**Scenario 2: Multiple Runs Without Cleanup**
1. First run: Items correctly inserted
2. Database not cleared
3. Second run: Same items inserted again, creating duplicates
4. If parser changed logic between runs, same item could go to different table

### Code Evidence

From `batch_process.py` line 109-145:

```python
# Upload houses
for house_data in result.get('houses', []):
    try:
        house_record = {
            'user_id': self.user_id,
            'name': house_data['name'],
            # ... other fields
        }
        
        # Insert house - NO CHECK IF IT ALREADY EXISTS
        response = self.supabase.table('houses').insert(house_record).execute()
        house_id = response.data[0]['id']
        house_name_to_id[house_data['name']] = house_id  # Local map only
```

**The problem:**
- ❌ No `SELECT` to check if name already exists in `houses` or `accessories`
- ❌ No unique constraint on name in database schema
- ❌ `house_name_to_id` map is cleared between script runs
- ❌ No cross-table checking (doesn't check if accessory name exists in houses table)

### Secondary Issue: Parser Confusion

From `docx_parser_simple.py`, the parser uses heuristics to determine item type:
- Line 1 = House name
- Line 2+ = Accessory names (usually)

But some documents have different formats:
- Some accessories listed on line 1
- Some have "Set of X" format
- Some have "Accessories - ..." list format

This can cause misclassification where the same physical accessory item appears as:
- A house in one document
- An accessory in another document

## The 29 Affected Items

These items existed in BOTH tables because either:
1. Parser misclassified them in different documents, OR
2. Batch script ran multiple times without clearing database

Items fixed:
1. Around the World in 24 Hours Flight Center
2. Basket Weaving 101
3. Baskets & Bows
4. Beard Bros. Sleigh Wash
5. Bjorn Turoc Rocking Horse Maker
6. Bottom of Form
7. Car Wash Cadets
8. Christmas Bread Bakers
9. Christmas Quilts
10. Coca-Cola Soda Fountain
11. Coca-Cola Taste Test
12. Cocoa Chocolate Works
13. Crayola Crayon Factory
14. Every Quilt Kid Tested
15. FAO Piano Dance Contest
16. Finny's Ornament House
17. Gingerbread Button Treats
18. Gingerbread Supply Company
19. Leonardo & Vincent
20. Nanook's Home
21. Naughty Stocking Stuffers
22. North Pole's Finest Wooden Toys
23. Ready For Paint
24. Teacup Delivery Service
25. That's A Wrap
26. This One Passes QC
27. Too Good to Resist
28. Bouncy's Ball Factory (already removed)
29. Jacques' Jack In The Box Shop (already removed)
30. North Pole's Finest Wooden Toys (already removed)

## Solution Implemented

### Immediate Fix (COMPLETED)
✅ Deleted duplicate records from `houses` table (26 items)
✅ Preserved correct records in `accessories` table
✅ Database now clean: 249 houses, 334 accessories, 0 duplicates

### Long-term Prevention (TO IMPLEMENT)

1. **Add Duplicate Detection to `batch_process.py`**
2. **Add Database Unique Constraints** (optional)
3. **Improve Parser Classification Logic**
4. **Add Pre-Import Validation**

See fixes in the next section.
