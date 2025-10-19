"""
Comprehensive analysis to find ALL items in wrong tables
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("COMPREHENSIVE MISCLASSIFICATION ANALYSIS")
print("=" * 80)

# Get all data
houses = supabase.table('houses').select('id, name').execute()
accessories = supabase.table('accessories').select('id, name').execute()
links = supabase.table('house_accessory_links').select('house_id, accessory_id').execute()

print(f"\nDatabase totals:")
print(f"  Houses: {len(houses.data)}")
print(f"  Accessories: {len(accessories.data)}")
print(f"  Links: {len(links.data)}")

# Create maps
house_name_to_id = {h['name']: h['id'] for h in houses.data}
acc_name_to_id = {a['name']: a['id'] for a in accessories.data}
acc_id_to_name = {a['id']: a['name'] for a in accessories.data}
house_id_to_name = {h['id']: h['name'] for h in houses.data}

# Find linked accessory IDs
linked_acc_ids = {l['accessory_id'] for l in links.data}
orphaned_accs = [a for a in accessories.data if a['id'] not in linked_acc_ids]

print(f"\n  Accessories with house links: {len(linked_acc_ids)}")
print(f"  Orphaned accessories (no links): {len(orphaned_accs)}")

# Check orphaned accessories - many might be houses!
print("\n" + "=" * 80)
print("ORPHANED ACCESSORIES - Sample of 100")
print("(These might actually be HOUSES)")
print("=" * 80)

for i, acc in enumerate(orphaned_accs[:100], 1):
    print(f"{i:3d}. {acc['name']}")

print(f"\nShowing {min(100, len(orphaned_accs))} of {len(orphaned_accs)} total")

# The BIG question: Which "houses" should actually be accessories?
# Heuristic: Check for common accessory keywords
print("\n" + "=" * 80)
print("HOUSES THAT MIGHT BE ACCESSORIES")
print("(Based on name keywords)")
print("=" * 80)

accessory_keywords = [
    'set of', 'set', 'figurine', 'sign', 'snowman', 'snowmen',
    'figure', 'statue', 'animated', 'display', 'ornament',
    'decoration', 'light', 'beacon', 'welcome', 'packages',
    'loading', 'delivery', 'elf', 'santa', 'test', 'flight',
    'training', 'checking', 'everything looks'
]

suspect_houses = []
for house in houses.data:
    name_lower = house['name'].lower()
    for keyword in accessory_keywords:
        if keyword in name_lower:
            suspect_houses.append(house)
            break

print(f"\nFound {len(suspect_houses)} houses with accessory-like names:")
for i, house in enumerate(suspect_houses, 1):
    # Check if it has any accessories linked TO it
    links_from_this_house = [l for l in links.data if l['house_id'] == house['id']]
    print(f"{i:3d}. {house['name']} - {len(links_from_this_house)} accessories linked")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print(f"\n1. Review {len(suspect_houses)} houses with accessory-like keywords")
print(f"2. Review {len(orphaned_accs)} orphaned accessories - many might be houses")
print(f"\n⚠️  This requires MANUAL REVIEW of your actual collection to classify correctly")
