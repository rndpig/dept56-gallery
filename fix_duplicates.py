"""
Find and fix duplicate entries in the database
"""
import os
from collections import defaultdict
from supabase import create_client
from dotenv import load_dotenv
from typing import Dict, List, Any

load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

def find_duplicates(items: List[Dict[str, Any]], key_field: str) -> Dict[str, List[Dict[str, Any]]]:
    """Find items with duplicate names and return them grouped"""
    groups = defaultdict(list)
    for item in items:
        groups[item[key_field]].append(item)
    return {k: v for k, v in groups.items() if len(v) > 1}

def choose_primary(duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Choose which duplicate to keep based on data completeness"""
    # Sort by:
    # 1. Has photo_url
    # 2. Has notes
    # 3. Has year
    # 4. Most recent updated_at
    return sorted(duplicates, key=lambda x: (
        bool(x.get('photo_url')),
        bool(x.get('notes')),
        bool(x.get('year')),
        x.get('updated_at', '')
    ), reverse=True)[0]

def merge_duplicates(table: str, duplicates: Dict[str, List[Dict[str, Any]]]):
    """Merge duplicate entries, preserving relationships"""
    print(f"\nProcessing {len(duplicates)} duplicate groups in {table}...")
    
    for name, items in duplicates.items():
        primary = choose_primary(items)
        secondary_ids = [item['id'] for item in items if item['id'] != primary['id']]
        
        print(f"\n📦 Processing duplicates for: {name}")
        print(f"  ✓ Keeping ID: {primary['id']}")
        print(f"  ✗ Removing IDs: {', '.join(secondary_ids)}")
        
        # Update relationships for houses
        if table == 'houses':
            for old_id in secondary_ids:
                # Move accessory links
                links = supabase.table('house_accessory_links').select('*').eq('house_id', old_id).execute()
                for link in links.data:
                    try:
                        supabase.table('house_accessory_links').insert({
                            'house_id': primary['id'],
                            'accessory_id': link['accessory_id']
                        }).execute()
                    except Exception as e:
                        print(f"    ⚠️ Failed to move accessory link: {e}")
                
                # Delete old accessory links
                supabase.table('house_accessory_links').delete().eq('house_id', old_id).execute()
                
                # Delete the duplicate house
                supabase.table('houses').delete().eq('id', old_id).execute()
                print(f"    ✓ Removed duplicate and moved its relationships")
        
        # Update relationships for accessories
        elif table == 'accessories':
            for old_id in secondary_ids:
                # Move house links
                links = supabase.table('house_accessory_links').select('*').eq('accessory_id', old_id).execute()
                for link in links.data:
                    try:
                        supabase.table('house_accessory_links').insert({
                            'house_id': link['house_id'],
                            'accessory_id': primary['id']
                        }).execute()
                    except Exception as e:
                        print(f"    ⚠️ Failed to move house link: {e}")
                
                # Delete old house links
                supabase.table('house_accessory_links').delete().eq('accessory_id', old_id).execute()
                
                # Delete the duplicate accessory
                supabase.table('accessories').delete().eq('id', old_id).execute()
                print(f"    ✓ Removed duplicate and moved its relationships")

def main():
    print("\n🔍 Looking for duplicates...")
    
    # Check houses
    houses = supabase.table('houses').select('*').execute()
    house_duplicates = find_duplicates(houses.data, 'name')
    print(f"\nFound {len(house_duplicates)} duplicate house groups")
    
    # Check accessories
    accessories = supabase.table('accessories').select('*').execute()
    accessory_duplicates = find_duplicates(accessories.data, 'name')
    print(f"Found {len(accessory_duplicates)} duplicate accessory groups")
    
    if not house_duplicates and not accessory_duplicates:
        print("\n✨ No duplicates found! Database is clean.")
        return
    
    # Process duplicates
    if house_duplicates:
        merge_duplicates('houses', house_duplicates)
    
    if accessory_duplicates:
        merge_duplicates('accessories', accessory_duplicates)
    
    print("\n✅ Cleanup complete!")
    print("💡 Refresh your browser to see the changes.")

if __name__ == '__main__':
    main()