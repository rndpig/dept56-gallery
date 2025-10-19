"""
Diagnostic script to find accessories that are incorrectly stored in the houses table.
These would appear as houses in the gallery but should be accessories.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key (bypasses RLS)
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def diagnose_misclassified():
    """Find items that might be misclassified between houses and accessories."""
    
    print("=" * 80)
    print("DIAGNOSING MISCLASSIFIED ITEMS")
    print("=" * 80)
    
    # Check specific items mentioned
    print("\n1. Checking 'Basket Weaving 101'...")
    house_result = supabase.table('houses').select('*').eq('name', 'Basket Weaving 101').execute()
    acc_result = supabase.table('accessories').select('*').eq('name', 'Basket Weaving 101').execute()
    
    print(f"   In houses table: {len(house_result.data)} records")
    if house_result.data:
        for item in house_result.data:
            print(f"     - ID: {item['id'][:8]}..., is_house: {item.get('is_house', 'N/A')}")
    
    print(f"   In accessories table: {len(acc_result.data)} records")
    if acc_result.data:
        for item in acc_result.data:
            print(f"     - ID: {item['id'][:8]}..., is_house: {item.get('is_house', 'N/A')}")
    
    print("\n2. Checking 'Animated Flight Test'...")
    house_result2 = supabase.table('houses').select('*').eq('name', 'Animated Flight Test').execute()
    acc_result2 = supabase.table('accessories').select('*').eq('name', 'Animated Flight Test').execute()
    
    print(f"   In houses table: {len(house_result2.data)} records")
    if house_result2.data:
        for item in house_result2.data:
            print(f"     - ID: {item['id'][:8]}..., is_house: {item.get('is_house', 'N/A')}")
    
    print(f"   In accessories table: {len(acc_result2.data)} records")
    if acc_result2.data:
        for item in acc_result2.data:
            print(f"     - ID: {item['id'][:8]}..., is_house: {item.get('is_house', 'N/A')}")
    
    # Check for houses where is_house = false (these should be accessories)
    print("\n3. Finding all records in 'houses' table where is_house = false...")
    false_houses = supabase.table('houses').select('id, name, is_house').eq('is_house', False).execute()
    
    print(f"\n   Found {len(false_houses.data)} items in houses table with is_house = false:")
    for item in false_houses.data:
        print(f"     - {item['name']}")
    
    # Check for accessories where is_house = true (these should be houses)
    print("\n4. Finding all records in 'accessories' table where is_house = true...")
    true_accessories = supabase.table('accessories').select('id, name, is_house').eq('is_house', True).execute()
    
    print(f"\n   Found {len(true_accessories.data)} items in accessories table with is_house = true:")
    for item in true_accessories.data:
        print(f"     - {item['name']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Items in HOUSES table that should be ACCESSORIES (is_house=false): {len(false_houses.data)}")
    print(f"Items in ACCESSORIES table that should be HOUSES (is_house=true): {len(true_accessories.data)}")
    
    return false_houses.data, true_accessories.data

if __name__ == '__main__':
    misclassified_houses, misclassified_accessories = diagnose_misclassified()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("These items need to be moved between tables:")
    print(f"\n1. Move {len(misclassified_houses)} items from 'houses' to 'accessories' table")
    print(f"2. Move {len(misclassified_accessories)} items from 'accessories' to 'houses' table")
