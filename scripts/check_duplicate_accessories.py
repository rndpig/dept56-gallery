"""
Check for duplicate accessories in the database
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv()

supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("CHECKING FOR DUPLICATE ACCESSORIES")
print("=" * 80)

# Get all accessories
accessories = supabase.table('accessories').select('id, name').execute()
print(f"\nTotal accessories: {len(accessories.data)}")

# Count duplicates
names = [a['name'] for a in accessories.data]
name_counts = Counter(names)
duplicates = {name: count for name, count in name_counts.items() if count > 1}

print(f"Duplicate accessories: {len(duplicates)}")

if duplicates:
    print("\nDuplicate items:")
    for name, count in sorted(duplicates.items()):
        print(f"  - {name}: {count} copies")
        
        # Show IDs
        ids = [a['id'] for a in accessories.data if a['name'] == name]
        for i, id in enumerate(ids, 1):
            print(f"    {i}. ID: {id[:8]}...")
else:
    print("\n✅ No duplicate accessories found!")
