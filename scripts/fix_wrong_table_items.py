"""
Fix script to remove accessories that are incorrectly duplicated in the houses table.
These 29 items should ONLY exist in the accessories table.
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

# List of items that exist in BOTH tables and should be removed from houses
ITEMS_TO_REMOVE_FROM_HOUSES = [
    "Around the World in 24 Hours Flight Center",
    "Basket Weaving 101",
    "Baskets & Bows",
    "Beard Bros. Sleigh Wash",
    "Bjorn Turoc Rocking Horse Maker",
    "Bottom of Form",
    "Bouncy's Ball Factory",
    "Car Wash Cadets",
    "Christmas Bread Bakers",
    "Christmas Quilts",
    "Coca-Cola Soda Fountain",
    "Coca-Cola Taste Test",
    "Cocoa Chocolate Works",
    "Crayola Crayon Factory",
    "Every Quilt Kid Tested",
    "FAO Piano Dance Contest",
    "Finny's Ornament House",
    "Gingerbread Button Treats",
    "Gingerbread Supply Company",
    "Jacques' Jack In The Box Shop",
    "Leonardo & Vincent",
    "Nanook's Home",
    "Naughty Stocking Stuffers",
    "North Pole's Finest Wooden Toys",
    "Ready For Paint",
    "Teacup Delivery Service",
    "That's A Wrap",
    "This One Passes QC",
    "Too Good to Resist"
]

def fix_duplicate_items():
    """Remove accessories from the houses table."""
    
    print("=" * 80)
    print("REMOVING ACCESSORIES FROM HOUSES TABLE")
    print("=" * 80)
    print(f"\nWill remove {len(ITEMS_TO_REMOVE_FROM_HOUSES)} items from houses table")
    print("These items will remain in the accessories table where they belong.\n")
    
    # Show what will be deleted
    print("Items to be removed from HOUSES table:")
    for i, name in enumerate(ITEMS_TO_REMOVE_FROM_HOUSES, 1):
        print(f"  {i:2d}. {name}")
    
    # Confirm
    print("\n" + "=" * 80)
    response = input("Proceed with deletion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("PROCESSING DELETIONS")
    print("=" * 80)
    
    deleted_count = 0
    errors = []
    
    for name in ITEMS_TO_REMOVE_FROM_HOUSES:
        try:
            # Get the house record
            house_result = supabase.table('houses').select('id').eq('name', name).execute()
            
            if not house_result.data:
                print(f"\n⚠️  {name}")
                print(f"   Not found in houses table (may have been already removed)")
                continue
            
            house_id = house_result.data[0]['id']
            
            # Check for linked accessories (as a house)
            links = supabase.table('house_accessory_links').select('id, accessory_id').eq('house_id', house_id).execute()
            
            if links.data:
                print(f"\n📦 {name}")
                print(f"   House ID: {house_id[:8]}...")
                print(f"   Has {len(links.data)} accessory link(s) as 'house'")
                
                # Delete the links first
                for link in links.data:
                    supabase.table('house_accessory_links').delete().eq('id', link['id']).execute()
                    print(f"   ✓ Deleted link to accessory {link['accessory_id'][:8]}...")
            
            # Delete from houses table
            supabase.table('houses').delete().eq('id', house_id).execute()
            print(f"   ✅ Deleted from houses table")
            deleted_count += 1
            
        except Exception as e:
            error_msg = f"Error processing {name}: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ {error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successfully deleted: {deleted_count} items from houses table")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    # Check if any items still exist in both tables
    remaining_dupes = []
    for name in ITEMS_TO_REMOVE_FROM_HOUSES:
        house_check = supabase.table('houses').select('id').eq('name', name).execute()
        acc_check = supabase.table('accessories').select('id').eq('name', name).execute()
        
        if house_check.data and acc_check.data:
            remaining_dupes.append(name)
    
    if remaining_dupes:
        print(f"⚠️  Still {len(remaining_dupes)} items in both tables:")
        for name in remaining_dupes:
            print(f"  - {name}")
    else:
        print("✅ No items remain in both tables!")
    
    # Final counts
    houses_count = supabase.table('houses').select('id', count='exact').execute()
    accessories_count = supabase.table('accessories').select('id', count='exact').execute()
    
    print(f"\nFinal database counts:")
    print(f"  Houses: {houses_count.count}")
    print(f"  Accessories: {accessories_count.count}")

if __name__ == '__main__':
    fix_duplicate_items()
