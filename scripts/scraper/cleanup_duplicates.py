"""
Clean up duplicate staged items
Keeps only the highest confidence entry for each original_house_id
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

load_dotenv()

supabase = create_client(os.getenv("VITE_SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

print("=" * 70)
print("🧹 Cleaning up duplicate staged items")
print("=" * 70)

# Get all pending staged houses
result = supabase.table('staged_houses').select('*').eq('status', 'pending').execute()
items = result.data

print(f"\nFound {len(items)} pending items")

# Group by original_house_id
by_house = defaultdict(list)
for item in items:
    if item['original_house_id']:
        by_house[item['original_house_id']].append(item)

# Find duplicates
duplicates_to_delete = []
kept_items = []

for house_id, duplicates in by_house.items():
    if len(duplicates) > 1:
        # Sort by confidence score (highest first)
        sorted_items = sorted(duplicates, key=lambda x: x['overall_confidence_score'], reverse=True)
        
        # Keep the highest confidence one
        kept = sorted_items[0]
        kept_items.append(kept)
        
        # Mark the rest for deletion
        to_delete = sorted_items[1:]
        duplicates_to_delete.extend(to_delete)
        
        print(f"\n📦 {kept['name']}")
        print(f"   Found {len(duplicates)} duplicates")
        print(f"   ✅ Keeping: ID {kept['id'][:8]}... (confidence: {kept['overall_confidence_score']:.2f})")
        print(f"   🗑️  Deleting {len(to_delete)} duplicates")

if not duplicates_to_delete:
    print("\n✅ No duplicates found!")
else:
    print(f"\n{'=' * 70}")
    print(f"Found {len(duplicates_to_delete)} duplicate items to delete")
    print(f"{'=' * 70}")
    
    confirm = input("\nProceed with deletion? (yes/no): ")
    
    if confirm.lower() == 'yes':
        for item in duplicates_to_delete:
            supabase.table('staged_houses').delete().eq('id', item['id']).execute()
            print(f"  ✅ Deleted {item['name']} (ID: {item['id'][:8]}...)")
        
        print(f"\n{'=' * 70}")
        print("✅ Cleanup complete!")
        print(f"{'=' * 70}")
        print(f"Deleted: {len(duplicates_to_delete)} items")
        print(f"Remaining: {len(kept_items)} unique pending items")
    else:
        print("\n❌ Cleanup cancelled")
