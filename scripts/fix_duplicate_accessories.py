"""
Remove duplicate accessories, keeping the version that has house links.
Priority: Keep accessory with most house links, then oldest by created_at.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def fix_duplicate_accessories():
    """Remove duplicate accessories, keeping those with house links"""
    
    print("=" * 80)
    print("REMOVING DUPLICATE ACCESSORIES")
    print("Priority: Keep accessories with house links")
    print("=" * 80)
    
    # Get all accessories
    accessories = supabase.table('accessories').select('*').order('name').execute()
    
    # Get all links
    links = supabase.table('house_accessory_links').select('*').execute()
    
    # Create map of accessory_id -> count of links
    link_counts = {}
    for link in links.data:
        acc_id = link['accessory_id']
        link_counts[acc_id] = link_counts.get(acc_id, 0) + 1
    
    print(f"\nTotal accessories: {len(accessories.data)}")
    print(f"Total links: {len(links.data)}")
    
    # Group by name
    by_name = {}
    for acc in accessories.data:
        name = acc['name']
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(acc)
    
    # Find duplicates
    duplicates = {name: accs for name, accs in by_name.items() if len(accs) > 1}
    
    print(f"\nFound {len(duplicates)} accessory names with duplicates")
    print(f"Total duplicate records: {sum(len(accs) - 1 for accs in duplicates.values())}")
    
    if not duplicates:
        print("\n✅ No duplicates found!")
        return
    
    # Show preview
    print("\nPreview of duplicates (first 10):")
    for i, (name, accs) in enumerate(list(duplicates.items())[:10], 1):
        print(f"\n{i}. {name} - {len(accs)} copies")
        for acc in accs:
            acc_id = acc['id']
            num_links = link_counts.get(acc_id, 0)
            print(f"   - ID: {acc_id[:8]}... Links: {num_links}")
    
    # Confirm
    print("\n" + "=" * 80)
    response = input(f"Delete {sum(len(accs) - 1 for accs in duplicates.values())} duplicate accessories? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("PROCESSING DUPLICATES")
    print("=" * 80)
    
    deleted_count = 0
    errors = []
    
    for name, accs in duplicates.items():
        try:
            # Sort by: 1) number of links (descending), 2) created_at (ascending = oldest first)
            sorted_accs = sorted(
                accs,
                key=lambda a: (
                    -link_counts.get(a['id'], 0),  # Most links first (negative for descending)
                    a.get('created_at', '9999-12-31')  # Oldest first (earlier dates sort first)
                )
            )
            
            # Keep the first one (most links, or oldest if same links)
            keep = sorted_accs[0]
            to_delete = sorted_accs[1:]
            
            keep_links = link_counts.get(keep['id'], 0)
            
            print(f"\n📦 {name}")
            print(f"   ✅ Keeping: {keep['id'][:8]}... ({keep_links} links)")
            
            # Delete the rest
            for acc in to_delete:
                acc_id = acc['id']
                acc_links = link_counts.get(acc_id, 0)
                
                # If this duplicate has links, we need to transfer them to the kept accessory
                if acc_links > 0:
                    # Get all links for this accessory
                    acc_link_records = [l for l in links.data if l['accessory_id'] == acc_id]
                    
                    for link in acc_link_records:
                        # Check if this house->accessory link already exists for the kept accessory
                        existing = supabase.table('house_accessory_links')\
                            .select('id')\
                            .eq('house_id', link['house_id'])\
                            .eq('accessory_id', keep['id'])\
                            .execute()
                        
                        if not existing.data:
                            # Transfer the link to the kept accessory
                            supabase.table('house_accessory_links')\
                                .update({'accessory_id': keep['id']})\
                                .eq('id', link['id'])\
                                .execute()
                            print(f"   🔗 Transferred link from {acc_id[:8]}...")
                        else:
                            # Link already exists, just delete the duplicate link
                            supabase.table('house_accessory_links')\
                                .delete()\
                                .eq('id', link['id'])\
                                .execute()
                            print(f"   🔗 Deleted duplicate link from {acc_id[:8]}...")
                
                # Delete the accessory
                supabase.table('accessories').delete().eq('id', acc_id).execute()
                print(f"   ❌ Deleted: {acc_id[:8]}... ({acc_links} links)")
                deleted_count += 1
                
        except Exception as e:
            error_msg = f"Error processing {name}: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ {error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successfully deleted: {deleted_count} duplicate accessories")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    # Check for remaining duplicates
    accessories_after = supabase.table('accessories').select('name').execute()
    names_after = [a['name'] for a in accessories_after.data]
    
    from collections import Counter
    name_counts = Counter(names_after)
    remaining_dupes = {name: count for name, count in name_counts.items() if count > 1}
    
    if remaining_dupes:
        print(f"⚠️  Still {len(remaining_dupes)} accessory names with duplicates:")
        for name, count in list(remaining_dupes.items())[:10]:
            print(f"  - {name}: {count} copies")
    else:
        print("✅ No duplicate accessory names remaining!")
    
    # Final counts
    accessories_count = supabase.table('accessories').select('id', count='exact').execute()
    links_count = supabase.table('house_accessory_links').select('id', count='exact').execute()
    
    print(f"\nFinal database counts:")
    print(f"  Accessories: {accessories_count.count}")
    print(f"  House-Accessory Links: {links_count.count}")

if __name__ == '__main__':
    fix_duplicate_accessories()
