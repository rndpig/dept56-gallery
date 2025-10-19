#!/usr/bin/env python3
"""
Check for items that might be in the wrong table (houses in accessories, accessories in houses).
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("CHECKING FOR MISCLASSIFIED ITEMS")
print("=" * 80)
print()

# Get all houses and accessories
houses_response = supabase.table('houses').select('*').execute()
accessories_response = supabase.table('accessories').select('*').execute()

houses = houses_response.data
accessories = accessories_response.data

print(f"Total houses: {len(houses)}")
print(f"Total accessories: {len(accessories)}")
print()

# Check specific item
test_name = "Around the World in 24 Hours Flight Center"
print(f"Searching for: '{test_name}'")
print()

house_match = [h for h in houses if test_name.lower() in h['name'].lower()]
accessory_match = [a for a in accessories if test_name.lower() in a['name'].lower()]

if house_match:
    print(f"✅ Found in HOUSES table: {len(house_match)} match(es)")
    for h in house_match:
        print(f"   - ID: {h['id'][:8]}... Name: '{h['name']}'")
else:
    print(f"❌ NOT found in houses table")

print()

if accessory_match:
    print(f"✅ Found in ACCESSORIES table: {len(accessory_match)} match(es)")
    for a in accessory_match:
        print(f"   - ID: {a['id'][:8]}... Name: '{a['name']}'")
else:
    print(f"❌ NOT found in accessories table")

print()
print("=" * 80)
print("LOOKING FOR ITEMS IN BOTH TABLES")
print("=" * 80)
print()

# Check for items in both tables
house_names = {h['name'].strip().lower() for h in houses}
accessory_names = {a['name'].strip().lower() for a in accessories}

in_both = house_names & accessory_names

if in_both:
    print(f"Found {len(in_both)} items in BOTH tables:")
    for name_lower in sorted(in_both):
        # Find original names
        h = next((h for h in houses if h['name'].strip().lower() == name_lower), None)
        a = next((a for a in accessories if a['name'].strip().lower() == name_lower), None)
        if h and a:
            print(f"  - '{h['name']}' (House ID: {h['id'][:8]}..., Accessory ID: {a['id'][:8]}...)")
else:
    print("✅ No items found in both tables")

print()
print("=" * 80)
print("KEYWORDS SUGGESTING MISCLASSIFICATION")
print("=" * 80)
print()

# Keywords that suggest an item should be a house
house_keywords = ['house', 'building', 'shop', 'store', 'inn', 'hotel', 'church', 'chapel', 
                  'station', 'factory', 'mill', 'barn', 'cottage', 'manor', 'center', 'centre',
                  'bakery', 'brewery', 'cafe', 'restaurant', 'theater', 'theatre', 'hall',
                  'tower', 'castle', 'palace', 'museum', 'library', 'school', 'depot']

# Find accessories with house-like keywords
suspicious_accessories = []
for a in accessories:
    name_lower = a['name'].lower()
    matched_keywords = [kw for kw in house_keywords if kw in name_lower]
    if matched_keywords:
        suspicious_accessories.append({
            'id': a['id'],
            'name': a['name'],
            'keywords': matched_keywords
        })

print(f"Found {len(suspicious_accessories)} accessories with house-like keywords:")
print()

# Show first 20
for item in suspicious_accessories[:20]:
    print(f"  - '{item['name']}'")
    print(f"    ID: {item['id'][:8]}... Keywords: {', '.join(item['keywords'])}")
    print()

if len(suspicious_accessories) > 20:
    print(f"... and {len(suspicious_accessories) - 20} more")
    print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("To fix this, you have three options:")
print()
print("1. MANUAL REVIEW: Review the list above and manually move items")
print("2. BATCH SCRIPT: Create a script to move items matching specific keywords")
print("3. UI FEATURE: Add a 'Move to Houses' button in the edit form (recommended)")
print()
print("I recommend option 3: Adding UI buttons to move items between tables.")
