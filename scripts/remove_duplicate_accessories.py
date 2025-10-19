"""
Remove duplicate accessories from the accessories table.
Keeps the oldest record (by created_at) for each name.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def remove_duplicate_accessories():
    """Remove duplicate accessories, keeping only the oldest one"""
    
    print("=" * 80)
    print("REMOVING DUPLICATE ACCESSORIES")
    print("=" * 80)
    
    # Get all accessories with created_at timestamp
    accessories = supabase.table('accessories').select('*').order('created_at').execute()
    
    print(f"\nTotal accessories: {len(accessories.data)}")
    
    # Group by name
    by_name = defaultdict(list)
    for acc in accessories.data:
        by_name[acc['name']].append(acc)
    
    # Find duplicates
    duplicates_to_delete = []
    for name, accs in by_name.items():
        if len(accs) > 1:
            # Keep the first one (oldest by created_at), delete the rest
            to_keep = accs[0]
            to_delete = accs[1:]
            duplicates_to_delete.extend(to_delete)
            print(f"\n📦 {name}")
            print(f"   Found {len(accs)} copies")
            print(f"   ✅ Keeping: {to_keep['id'][:8]}... (created: {to_keep.get('created_at', 'N/A')})")
            for i, acc in enumerate(to_delete, 1):
                print(f"   ❌ Will delete: {acc['id'][:8]}... (created: {acc.get('created_at', 'N/A')})")
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"Unique accessories: {len(by_name)}")
    print(f"Duplicates to delete: {len(duplicates_to_delete)}")
    
    if not duplicates_to_delete:
        print("\n✅ No duplicates found!")
        return
    
    # Confirm
    print(f"\n{'=' * 80}")
    response = input(f"Delete {len(duplicates_to_delete)} duplicate accessories? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Aborted by user")
        return
    
    print(f"\n{'=' * 80}")
    print("DELETING DUPLICATES")
    print(f"{'=' * 80}\n")
    
    deleted_count = 0
    errors = []
    
    for acc in duplicates_to_delete:
        try:
            acc_id = acc['id']
            acc_name = acc['name']
            
            # Delete links first
            links = supabase.table('house_accessory_links').select('id').eq('accessory_id', acc_id).execute()
            if links.data:
                for link in links.data:
                    supabase.table('house_accessory_links').delete().eq('id', link['id']).execute()
                print(f"  🔗 Deleted {len(links.data)} link(s) for '{acc_name}'")
            
            # Delete the accessory
            supabase.table('accessories').delete().eq('id', acc_id).execute()
            deleted_count += 1
            print(f"  ✅ Deleted: {acc_name} (ID: {acc_id[:8]}...)")
            
        except Exception as e:
            error_msg = f"Error deleting {acc.get('name', 'unknown')}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("FINAL SUMMARY")
    print(f"{'=' * 80}")
    print(f"Successfully deleted: {deleted_count} duplicate accessories")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors[:10]:
            print(f"  - {error}")
    
    # Verify
    final_accessories = supabase.table('accessories').select('id, name').execute()
    names = [a['name'] for a in final_accessories.data]
    from collections import Counter
    final_dupes = {name: count for name, count in Counter(names).items() if count > 1}
    
    print(f"\nFinal database counts:")
    print(f"  Total accessories: {len(final_accessories.data)}")
    print(f"  Remaining duplicates: {len(final_dupes)}")
    
    if final_dupes:
        print("\n⚠️  Still have duplicates:")
        for name, count in list(final_dupes.items())[:10]:
            print(f"  - {name}: {count} copies")
    else:
        print("\n✅ All duplicates removed!")

if __name__ == '__main__':
    remove_duplicate_accessories()
