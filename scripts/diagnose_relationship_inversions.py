"""
Diagnostic script to find items that are in the wrong table based on their relationships.

Logic:
1. Find "houses" that are linked to accessories whose names match actual houses
   (This suggests the "house" is actually an accessory)

2. Find "accessories" that have links where the linked item name matches a house
   (This suggests the "accessory" is actually a house)

3. Find items in wrong tables based on relationship inversions
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def diagnose_relationship_issues():
    """Find items in wrong tables based on relationship analysis"""
    
    print("=" * 80)
    print("RELATIONSHIP-BASED MISCLASSIFICATION DIAGNOSIS")
    print("=" * 80)
    
    # Get all houses, accessories, and links
    print("\n1. Loading data from database...")
    houses = supabase.table('houses').select('id, name').execute()
    accessories = supabase.table('accessories').select('id, name').execute()
    links = supabase.table('house_accessory_links').select('house_id, accessory_id').execute()
    
    print(f"   Houses: {len(houses.data)}")
    print(f"   Accessories: {len(accessories.data)}")
    print(f"   Links: {len(links.data)}")
    
    # Create lookup maps
    house_id_to_name = {h['id']: h['name'] for h in houses.data}
    house_name_to_id = {h['name']: h['id'] for h in houses.data}
    
    acc_id_to_name = {a['id']: a['name'] for a in accessories.data}
    acc_name_to_id = {a['name']: a['id'] for a in accessories.data}
    
    # Analysis 1: Find "houses" that are linked to items that are actually houses
    print("\n" + "=" * 80)
    print("ANALYSIS 1: Houses linked to accessories whose names match other houses")
    print("(These 'houses' are probably actually accessories)")
    print("=" * 80)
    
    misclassified_as_houses = []
    
    for link in links.data:
        house_id = link['house_id']
        acc_id = link['accessory_id']
        
        house_name = house_id_to_name.get(house_id)
        acc_name = acc_id_to_name.get(acc_id)
        
        if not house_name or not acc_name:
            continue
        
        # Check if the "accessory" name actually matches a house
        if acc_name in house_name_to_id:
            # This link says: house_name -> acc_name
            # But acc_name is ALSO a house!
            # This suggests house_name is actually an accessory
            misclassified_as_houses.append({
                'name': house_name,
                'house_id': house_id,
                'linked_to': acc_name,
                'linked_acc_id': acc_id
            })
    
    print(f"\nFound {len(misclassified_as_houses)} items in HOUSES table that are likely accessories:")
    for item in misclassified_as_houses:
        print(f"\n📦 {item['name']}")
        print(f"   Current: In HOUSES table (ID: {item['house_id'][:8]}...)")
        print(f"   Linked to: '{item['linked_to']}' (which IS a house)")
        print(f"   → Suggestion: Move to ACCESSORIES table")
    
    # Analysis 2: Find accessories with NO links (orphaned)
    print("\n" + "=" * 80)
    print("ANALYSIS 2: Accessories with no house links")
    print("(These might be houses, or legitimately standalone accessories)")
    print("=" * 80)
    
    linked_acc_ids = {link['accessory_id'] for link in links.data}
    orphaned_accessories = [acc for acc in accessories.data if acc['id'] not in linked_acc_ids]
    
    print(f"\nFound {len(orphaned_accessories)} accessories with no house links:")
    for acc in orphaned_accessories[:20]:  # Show first 20
        print(f"   - {acc['name']}")
    if len(orphaned_accessories) > 20:
        print(f"   ... and {len(orphaned_accessories) - 20} more")
    
    # Analysis 3: Find houses with NO accessories linked
    print("\n" + "=" * 80)
    print("ANALYSIS 3: Houses with no accessory links")
    print("(These are fine - houses don't need accessories)")
    print("=" * 80)
    
    linked_house_ids = {link['house_id'] for link in links.data}
    houses_no_accessories = [h for h in houses.data if h['id'] not in linked_house_ids]
    
    print(f"\nFound {len(houses_no_accessories)} houses with no accessories (this is OK)")
    
    # Analysis 4: Reverse check - accessories that ARE in the houses table
    print("\n" + "=" * 80)
    print("ANALYSIS 4: Cross-reference - Names in both tables")
    print("=" * 80)
    
    items_in_both = []
    for house in houses.data:
        if house['name'] in acc_name_to_id:
            items_in_both.append(house['name'])
    
    print(f"\nFound {len(items_in_both)} items in BOTH tables:")
    for name in items_in_both:
        print(f"   - {name}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Items in HOUSES that should be ACCESSORIES: {len(misclassified_as_houses)}")
    print(f"Orphaned accessories (no house link): {len(orphaned_accessories)}")
    print(f"Houses with no accessories: {len(houses_no_accessories)}")
    print(f"Items in BOTH tables: {len(items_in_both)}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if misclassified_as_houses:
        print(f"\n1. CRITICAL: Move {len(misclassified_as_houses)} items from HOUSES to ACCESSORIES")
        print("   These items are linked to houses, so they must be accessories.")
        print("\n   Items to move:")
        for item in misclassified_as_houses:
            print(f"     - {item['name']} → linked to house '{item['linked_to']}'")
    
    if items_in_both:
        print(f"\n2. Remove {len(items_in_both)} duplicate entries from one table")
    
    if orphaned_accessories:
        print(f"\n3. REVIEW: {len(orphaned_accessories)} orphaned accessories")
        print("   These may be legitimately standalone, or may need house links")
    
    return {
        'misclassified_as_houses': misclassified_as_houses,
        'items_in_both': items_in_both,
        'orphaned_accessories': orphaned_accessories
    }

if __name__ == '__main__':
    results = diagnose_relationship_issues()
