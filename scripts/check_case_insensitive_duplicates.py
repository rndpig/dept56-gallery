#!/usr/bin/env python3
"""
Check for duplicate accessories using case-insensitive name matching.
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("CHECKING FOR CASE-INSENSITIVE DUPLICATE ACCESSORIES")
print("=" * 80)
print()

# Get all accessories
response = supabase.table('accessories').select('*').execute()
accessories = response.data

print(f"Total accessories: {len(accessories)}")

# Get house links for each accessory
links_response = supabase.table('house_accessory_links').select('*').execute()
links = links_response.data

# Count links per accessory
link_counts = defaultdict(int)
for link in links:
    link_counts[link['accessory_id']] += 1

# Group by lowercase name
name_groups = defaultdict(list)
for accessory in accessories:
    name_lower = accessory['name'].strip().lower()
    name_groups[name_lower].append(accessory)

# Find duplicates (case-insensitive)
duplicates = {name: accs for name, accs in name_groups.items() if len(accs) > 1}

print(f"Case-insensitive duplicates: {len(duplicates)}")
print()

if duplicates:
    print("=" * 80)
    print("DUPLICATE ACCESSORIES (CASE-INSENSITIVE)")
    print("=" * 80)
    print()
    
    for name_lower, accs in sorted(duplicates.items()):
        print(f"📦 Lowercase name: '{name_lower}' - {len(accs)} copies")
        for acc in sorted(accs, key=lambda a: -link_counts.get(a['id'], 0)):
            num_links = link_counts.get(acc['id'], 0)
            print(f"   - ID: {acc['id'][:8]}... Actual name: '{acc['name']}' Links: {num_links}")
        print()
    
    # Summary
    total_with_links = sum(1 for accs in duplicates.values() for acc in accs if link_counts.get(acc['id'], 0) > 0)
    total_without_links = sum(1 for accs in duplicates.values() for acc in accs if link_counts.get(acc['id'], 0) == 0)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Duplicate accessories with links: {total_with_links}")
    print(f"Duplicate accessories without links: {total_without_links}")
    print(f"Total duplicate records: {sum(len(accs) for accs in duplicates.values())}")
    print(f"Estimated records to delete: {sum(len(accs) - 1 for accs in duplicates.values())}")
else:
    print("✅ No case-insensitive duplicate accessories found!")
