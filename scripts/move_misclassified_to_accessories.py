"""
Move misclassified accessories from houses table to accessories table.
Preserves all data, images, and relationships.
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

# User-identified accessories currently in houses table
MISCLASSIFIED_ACCESSORIES = [
    "Animated Flight Test",
    "Bear Down And Go",
    "Candy Cane Shack",
    "Christmas Packages",
    "Christmas Welcome",
    "Coca Cola Bottle Cap Ride",
    "Cocoa Cart (Classic Christmas)",
    "Crayola Super Sharpener",
    "Do I Have A Deal For You!",
    "Early Rising Elves",
    "Gingerbread Trees",
    "Hasbro Easy-Bake Bakery",
    "Have A Coke and A Smile",
    "Just A Cup Of Joe",
    "Light the Way-Santa's Beacon",
    "Mrs. Claus' Cookies & Milk",
    "North Pole Gate (lit)",
    "Northern Lights Express Engine",
    "Perry's Christmas Poinsettias",
    "Pop's Peppermint Barrel",
    "Santa's Sleigh Silhouette",
    "She'll Be Belle Of The Ball",
    "Toymaker Elves set of 3",
]

def move_houses_to_accessories():
    """Move misclassified items from houses to accessories table"""
    
    print("=" * 80)
    print("MOVING MISCLASSIFIED ACCESSORIES FROM HOUSES TO ACCESSORIES TABLE")
    print("=" * 80)
    print(f"\nWill move {len(MISCLASSIFIED_ACCESSORIES)} items\n")
    
    # Show items
    for i, name in enumerate(MISCLASSIFIED_ACCESSORIES, 1):
        print(f"  {i:2d}. {name}")
    
    # Confirm
    print("\n" + "=" * 80)
    response = input("Proceed with moving these items? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("PROCESSING")
    print("=" * 80)
    
    moved_count = 0
    errors = []
    
    for name in MISCLASSIFIED_ACCESSORIES:
        try:
            # Step 1: Get the house record
            house_result = supabase.table('houses').select('*').eq('name', name).execute()
            
            if not house_result.data:
                print(f"\n⚠️  {name}")
                print(f"   Not found in houses table (may have been already moved)")
                continue
            
            house_data = house_result.data[0]
            house_id = house_data['id']
            
            print(f"\n📦 {name}")
            print(f"   House ID: {house_id[:8]}...")
            
            # Step 2: Check if item already exists in accessories table
            acc_check = supabase.table('accessories').select('id').eq('name', name).execute()
            
            if acc_check.data:
                print(f"   ⚠️  Already exists in accessories table (ID: {acc_check.data[0]['id'][:8]}...)")
                print(f"   Will delete from houses table only")
                
                # Just delete from houses
                supabase.table('houses').delete().eq('id', house_id).execute()
                print(f"   ✅ Deleted from houses table")
                moved_count += 1
                continue
            
            # Step 3: Get any accessories linked TO this "house"
            links_as_house = supabase.table('house_accessory_links').select('*').eq('house_id', house_id).execute()
            
            if links_as_house.data:
                print(f"   Has {len(links_as_house.data)} accessories linked as 'house'")
            
            # Step 4: Get any links where this item is the accessory
            links_as_acc = supabase.table('house_accessory_links').select('*').eq('accessory_id', house_id).execute()
            
            if links_as_acc.data:
                print(f"   Is linked to {len(links_as_acc.data)} houses as 'accessory'")
            
            # Step 5: Create new accessory record with all data from house
            accessory_record = {
                'user_id': house_data['user_id'],
                'name': house_data['name'],
                'description': house_data.get('description'),
                'notes': house_data.get('notes'),
                'photo_url': house_data.get('photo_url'),
                'sku': house_data.get('sku'),
                'price': house_data.get('price'),
                'year': house_data.get('year'),
                'retired_year': house_data.get('retired_year'),
                'purchased_year': house_data.get('purchased_year'),
                'collection': house_data.get('collection'),
                'series': house_data.get('series'),
            }
            
            # Insert into accessories table
            acc_result = supabase.table('accessories').insert(accessory_record).execute()
            new_acc_id = acc_result.data[0]['id']
            print(f"   ✅ Created in accessories table (ID: {new_acc_id[:8]}...)")
            
            # Step 6: Update links - change this item from house_id to accessory_id
            if links_as_house.data:
                for link in links_as_house.data:
                    # Delete old link where this was the house
                    supabase.table('house_accessory_links').delete().eq('id', link['id']).execute()
                    print(f"   🔗 Deleted link where '{name}' was house")
            
            # Step 7: Update links where this was listed as accessory
            # Change the accessory_id from old house_id to new acc_id
            if links_as_acc.data:
                for link in links_as_acc.data:
                    supabase.table('house_accessory_links').update({'accessory_id': new_acc_id}).eq('id', link['id']).execute()
                    print(f"   🔗 Updated link to use new accessory ID")
            
            # Step 8: Copy tags if any
            try:
                tags = supabase.table('house_tags').select('tag_id').eq('house_id', house_id).execute()
                if tags.data:
                    for tag in tags.data:
                        supabase.table('accessory_tags').insert({
                            'accessory_id': new_acc_id,
                            'tag_id': tag['tag_id']
                        }).execute()
                    print(f"   🏷️  Copied {len(tags.data)} tags")
            except Exception as e:
                print(f"   ⚠️  Could not copy tags: {str(e)}")
            
            # Step 9: Copy collections if any
            try:
                collections = supabase.table('house_collections').select('collection_id').eq('house_id', house_id).execute()
                if collections.data:
                    for coll in collections.data:
                        supabase.table('accessory_collections').insert({
                            'accessory_id': new_acc_id,
                            'collection_id': coll['collection_id']
                        }).execute()
                    print(f"   📚 Copied {len(collections.data)} collections")
            except Exception as e:
                print(f"   ⚠️  Could not copy collections: {str(e)}")
            
            # Step 10: Delete from houses table
            supabase.table('houses').delete().eq('id', house_id).execute()
            print(f"   ✅ Deleted from houses table")
            
            moved_count += 1
            
        except Exception as e:
            error_msg = f"Error processing {name}: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ {error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successfully moved: {moved_count} items from houses to accessories")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    # Check if any items still exist in houses table
    remaining_in_houses = []
    for name in MISCLASSIFIED_ACCESSORIES:
        house_check = supabase.table('houses').select('id').eq('name', name).execute()
        if house_check.data:
            remaining_in_houses.append(name)
    
    if remaining_in_houses:
        print(f"⚠️  Still {len(remaining_in_houses)} items in houses table:")
        for name in remaining_in_houses:
            print(f"  - {name}")
    else:
        print("✅ No items remain in houses table!")
    
    # Verify they're in accessories table
    found_in_accessories = []
    for name in MISCLASSIFIED_ACCESSORIES:
        acc_check = supabase.table('accessories').select('id').eq('name', name).execute()
        if acc_check.data:
            found_in_accessories.append(name)
    
    print(f"\n✅ {len(found_in_accessories)} items confirmed in accessories table")
    
    # Final counts
    houses_count = supabase.table('houses').select('id', count='exact').execute()
    accessories_count = supabase.table('accessories').select('id', count='exact').execute()
    
    print(f"\nFinal database counts:")
    print(f"  Houses: {houses_count.count}")
    print(f"  Accessories: {accessories_count.count}")

if __name__ == '__main__':
    move_houses_to_accessories()
