"""
Find accessories that are incorrectly stored in the houses table.
These are items that should ONLY be in the accessories table but also appear in houses.
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

def find_accessories_in_houses():
    """Find accessories that are incorrectly in the houses table."""
    
    print("=" * 80)
    print("FINDING ACCESSORIES INCORRECTLY STORED IN HOUSES TABLE")
    print("=" * 80)
    
    # Get all accessories
    print("\n1. Fetching all accessories...")
    accessories = supabase.table('accessories').select('id, name').execute()
    print(f"   Total accessories in accessories table: {len(accessories.data)}")
    
    # Get all houses
    print("\n2. Fetching all houses...")
    houses = supabase.table('houses').select('id, name').execute()
    print(f"   Total houses in houses table: {len(houses.data)}")
    
    # Find accessories that appear in houses table
    accessory_names = {acc['name'] for acc in accessories.data}
    house_names = {house['name'] for house in houses.data}
    
    # Items that are in BOTH tables
    duplicated_in_both = accessory_names & house_names
    
    print(f"\n3. Items that exist in BOTH tables: {len(duplicated_in_both)}")
    
    if duplicated_in_both:
        print("\n   Items incorrectly appearing in HOUSES table:")
        for name in sorted(duplicated_in_both):
            # Get IDs from both tables
            house_rec = next((h for h in houses.data if h['name'] == name), None)
            acc_rec = next((a for a in accessories.data if a['name'] == name), None)
            
            print(f"\n   📦 {name}")
            print(f"      - In houses: {house_rec['id'][:8]}...")
            print(f"      - In accessories: {acc_rec['id'][:8]}...")
            
            # Check if the house record has any linked accessories
            links = supabase.table('house_accessory_links').select('accessory_id').eq('house_id', house_rec['id']).execute()
            print(f"      - Linked accessories as 'house': {len(links.data)}")
            
            # Check if this accessory is linked to any house
            acc_links = supabase.table('house_accessory_links').select('house_id').eq('accessory_id', acc_rec['id']).execute()
            print(f"      - Linked to houses as 'accessory': {len(acc_links.data)}")
    
    # Check for items ONLY in houses that might be accessories
    print("\n4. Checking for potential accessories only in houses table...")
    print("   (Looking for common accessory keywords in house names)")
    
    accessory_keywords = ['accessory', 'sign', 'figurine', 'set of', 'ornament', 
                          'tree', 'fence', 'figure', 'animated', 'weaving']
    
    potential_accessories = []
    for house in houses.data:
        name_lower = house['name'].lower()
        if any(keyword in name_lower for keyword in accessory_keywords):
            if house['name'] not in duplicated_in_both:
                potential_accessories.append(house)
    
    print(f"\n   Found {len(potential_accessories)} potential accessories in houses table:")
    for item in potential_accessories[:20]:  # Show first 20
        print(f"      - {item['name']}")
    
    return list(duplicated_in_both), potential_accessories

if __name__ == '__main__':
    duplicated, potential = find_accessories_in_houses()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Items confirmed in BOTH tables (need to remove from houses): {len(duplicated)}")
    print(f"Potential accessories only in houses (manual review needed): {len(potential)}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Delete the duplicate records from houses table (items that exist in both)")
    print("2. Manually review potential accessories and move if needed")
    print("3. Ensure house_accessories links are preserved before deletion")
