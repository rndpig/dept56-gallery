"""
Automated script to fix duplicate houses in Supabase
Keeps houses with accessories, deletes duplicates
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key
url: str = os.environ.get("VITE_SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)

def fix_duplicates():
    """Fix duplicate houses by keeping those with accessories"""
    print("\n🔧 FIXING DUPLICATE HOUSES")
    print("="*80)
    
    # Get all houses
    result = supabase.table('houses').select('id, name, created_at').execute()
    houses = result.data
    
    # Find duplicates
    name_map = {}
    for house in houses:
        name = house['name']
        if name not in name_map:
            name_map[name] = []
        name_map[name].append(house)
    
    duplicates = {name: records for name, records in name_map.items() if len(records) > 1}
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"Found {len(duplicates)} duplicate house names")
    print(f"Total records to process: {sum(len(records) for records in duplicates.values())}")
    
    # Process each duplicate
    kept_count = 0
    deleted_count = 0
    
    for name, records in sorted(duplicates.items()):
        # Get accessory counts for each record
        records_with_counts = []
        for record in records:
            links = supabase.table('house_accessory_links').select('id').eq('house_id', record['id']).execute()
            accessory_count = len(links.data) if links.data else 0
            records_with_counts.append((record, accessory_count))
        
        # Sort by accessory count (descending), then by created_at (ascending)
        records_with_counts.sort(key=lambda x: (-x[1], x[0]['created_at']))
        
        # Keep first record, delete rest
        kept_record, kept_count_acc = records_with_counts[0]
        print(f"\n📦 {name}")
        print(f"   ✅ Keeping: {kept_record['id'][:8]}... ({kept_count_acc} accessories)")
        kept_count += 1
        
        # Delete duplicates
        for record, acc_count in records_with_counts[1:]:
            print(f"   ❌ Deleting: {record['id'][:8]}... ({acc_count} accessories)")
            try:
                # Transfer any accessories/collections/tags before deleting
                if acc_count > 0:
                    # Transfer accessories
                    links = supabase.table('house_accessory_links').select('*').eq('house_id', record['id']).execute()
                    for link in links.data:
                        # Check if link already exists for kept record
                        existing = supabase.table('house_accessory_links').select('id')\
                            .eq('house_id', kept_record['id'])\
                            .eq('accessory_id', link['accessory_id'])\
                            .execute()
                        
                        if not existing.data:
                            # Create new link for kept record
                            supabase.table('house_accessory_links').insert({
                                'house_id': kept_record['id'],
                                'accessory_id': link['accessory_id']
                            }).execute()
                    
                    print(f"      → Transferred {len(links.data)} accessory links")
                
                # Transfer collections
                colls = supabase.table('house_collections').select('*').eq('house_id', record['id']).execute()
                for coll in colls.data:
                    existing = supabase.table('house_collections').select('id')\
                        .eq('house_id', kept_record['id'])\
                        .eq('collection_id', coll['collection_id'])\
                        .execute()
                    
                    if not existing.data:
                        supabase.table('house_collections').insert({
                            'house_id': kept_record['id'],
                            'collection_id': coll['collection_id']
                        }).execute()
                
                if colls.data:
                    print(f"      → Transferred {len(colls.data)} collection links")
                
                # Transfer tags
                tags = supabase.table('house_tags').select('*').eq('house_id', record['id']).execute()
                for tag in tags.data:
                    existing = supabase.table('house_tags').select('id')\
                        .eq('house_id', kept_record['id'])\
                        .eq('tag_id', tag['tag_id'])\
                        .execute()
                    
                    if not existing.data:
                        supabase.table('house_tags').insert({
                            'house_id': kept_record['id'],
                            'tag_id': tag['tag_id'],
                            'source': tag.get('source', 'manual'),
                            'confidence': tag.get('confidence'),
                            'reviewed': tag.get('reviewed', True)
                        }).execute()
                
                if tags.data:
                    print(f"      → Transferred {len(tags.data)} tag links")
                
                # Now delete the duplicate house
                supabase.table('houses').delete().eq('id', record['id']).execute()
                deleted_count += 1
                
            except Exception as e:
                print(f"      ⚠️  Error deleting: {e}")
    
    print("\n" + "="*80)
    print(f"✅ COMPLETE!")
    print(f"   Kept: {kept_count} houses")
    print(f"   Deleted: {deleted_count} duplicates")
    print("="*80)
    
    # Verify
    print("\n🔍 Verifying fix...")
    result = supabase.table('houses').select('name').execute()
    names = [h['name'] for h in result.data]
    remaining_dupes = [name for name in set(names) if names.count(name) > 1]
    
    if remaining_dupes:
        print(f"⚠️  WARNING: {len(remaining_dupes)} duplicates still exist:")
        for name in remaining_dupes:
            print(f"   - {name}")
    else:
        print("✅ No duplicates remaining!")
    
    print(f"\nTotal houses in database: {len(result.data)}")

if __name__ == "__main__":
    print("\n⚠️  DUPLICATE HOUSE FIX SCRIPT")
    print("="*80)
    print("This will delete duplicate houses, keeping those with accessories")
    print("="*80)
    
    response = input("\nDo you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        try:
            fix_duplicates()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ Cancelled")
