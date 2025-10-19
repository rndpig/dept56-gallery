#!/usr/bin/env python3
"""
Fix case-insensitive duplicate accessories.
Keep the version with the most house links (or oldest if equal).
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
print("REMOVING CASE-INSENSITIVE DUPLICATE ACCESSORIES")
print("Priority: Keep accessories with house links, then oldest")
print("=" * 80)
print()

# Get all accessories
response = supabase.table('accessories').select('*').execute()
accessories = response.data

# Get house links
links_response = supabase.table('house_accessory_links').select('*').execute()
links = links_response.data

# Count links per accessory
link_counts = defaultdict(int)
for link in links:
    link_counts[link['accessory_id']] += 1

print(f"Total accessories: {len(accessories)}")
print(f"Total links: {len(links)}")
print()

# Group by lowercase name
name_groups = defaultdict(list)
for accessory in accessories:
    name_lower = accessory['name'].strip().lower()
    name_groups[name_lower].append(accessory)

# Find duplicates (case-insensitive)
duplicates = {name: accs for name, accs in name_groups.items() if len(accs) > 1}

print(f"Found {len(duplicates)} accessory names with duplicates")
total_duplicates = sum(len(accs) for accs in duplicates.values())
print(f"Total duplicate records: {total_duplicates}")
print()

# Preview
print("Preview of duplicates (first 10):")
print()

for i, (name_lower, accs) in enumerate(sorted(duplicates.items())[:10], 1):
    print(f"{i}. \"{accs[0]['name']}\" - {len(accs)} copies")
    for acc in accs:
        num_links = link_counts.get(acc['id'], 0)
        print(f"   - ID: {acc['id'][:8]}... Links: {num_links}")
    print()

# Confirmation
num_to_delete = sum(len(accs) - 1 for accs in duplicates.values())
confirm = input(f"Delete {num_to_delete} duplicate accessories? (yes/no): ")

if confirm.lower() != 'yes':
    print("Aborted.")
    exit(0)

print()
print("=" * 80)
print("PROCESSING DUPLICATES")
print("=" * 80)
print()

deleted_count = 0
errors = 0

for name_lower, accs in sorted(duplicates.items()):
    # Sort: most links first, then oldest (by created_at)
    sorted_accs = sorted(accs, key=lambda a: (
        -link_counts.get(a['id'], 0),  # Most links first
        a.get('created_at', '9999-12-31')  # Oldest first if equal
    ))
    
    keep = sorted_accs[0]
    to_delete = sorted_accs[1:]
    
    print(f"📦 {keep['name']}")
    print(f"   ✅ Keeping: {keep['id'][:8]}... ({link_counts.get(keep['id'], 0)} links)")
    
    for dup in to_delete:
        try:
            # Delete the duplicate accessory
            supabase.table('accessories').delete().eq('id', dup['id']).execute()
            print(f"   ❌ Deleted: {dup['id'][:8]}... ({link_counts.get(dup['id'], 0)} links) - '{dup['name']}'")
            deleted_count += 1
        except Exception as e:
            print(f"   ⚠️  Error deleting {dup['id'][:8]}...: {e}")
            errors += 1
    
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Successfully deleted: {deleted_count} duplicate accessories")
print(f"Errors: {errors}")
print()

# Verification
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

response = supabase.table('accessories').select('*').execute()
final_accessories = response.data

# Check for remaining duplicates
name_groups_final = defaultdict(list)
for accessory in final_accessories:
    name_lower = accessory['name'].strip().lower()
    name_groups_final[name_lower].append(accessory)

remaining_duplicates = {name: accs for name, accs in name_groups_final.items() if len(accs) > 1}

if remaining_duplicates:
    print(f"⚠️  Still {len(remaining_duplicates)} duplicate names remaining!")
    for name_lower, accs in remaining_duplicates.items():
        print(f"   - '{accs[0]['name']}' ({len(accs)} copies)")
else:
    print("✅ No case-insensitive duplicate accessory names remaining!")

links_response_final = supabase.table('house_accessory_links').select('*').execute()
final_links = links_response_final.data

print()
print("Final database counts:")
print(f"  Accessories: {len(final_accessories)}")
print(f"  House-Accessory Links: {len(final_links)}")
