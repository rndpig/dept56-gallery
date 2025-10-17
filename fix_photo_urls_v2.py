"""
Fix photo URLs by matching house/accessory names to actual storage filenames
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, service_key)

print("\n🔧 Fixing photo URLs by mapping to actual storage files...\n")

# Get all files from storage
print("📦 Fetching all files from storage...")
all_files = []
offset = 0
limit = 1000
while True:
    files = supabase.storage.from_('dept56-images').list('ingestion', {
        'limit': limit,
        'offset': offset
    })
    if not files:
        break
    all_files.extend(files)
    if len(files) < limit:
        break
    offset += limit

print(f"Found {len(all_files)} files in storage\n")

# Create a mapping of base names to filenames
# Files are named like: "Year Title_primary.jpeg" or "ACC Year Title_primary.jpeg"
file_map = {}
for f in all_files:
    name = f['name']
    # Extract the base name (everything before _primary or _acc)
    if '_primary' in name:
        base = name.split('_primary')[0]
        file_map[base] = name
    elif '_acc' in name:
        base = name.split('_acc')[0]
        # Store accessories separately
        if base not in file_map:
            file_map[base] = []
        if not isinstance(file_map[base], list):
            file_map[base] = [file_map[base]]
        file_map[base].append(name)

print(f"Created mapping for {len(file_map)} items\n")

# Get all houses
houses = supabase.table('houses').select('id, name, year').execute().data
print(f"📦 Processing {len(houses)} houses...")

updated_houses = 0
not_found = []

for house in houses:
    # Try to find matching file
    # Files might be named: "Year Name" or just "Name"
    name = house['name']
    year = house['year']
    
    # Try different combinations
    possible_keys = [
        f"{year} {name}" if year else name,
        name,
        f"ACC {year} {name}" if year else f"ACC {name}",
    ]
    
    found = False
    for key in possible_keys:
        if key in file_map and isinstance(file_map[key], str):
            # Found it!
            filename = file_map[key]
            public_url = supabase.storage.from_('dept56-images').get_public_url(f"ingestion/{filename}")
            supabase.table('houses').update({'photo_url': public_url}).eq('id', house['id']).execute()
            updated_houses += 1
            if updated_houses <= 3:
                print(f"  ✅ {name[:40]}")
            found = True
            break
    
    if not found:
        not_found.append(name)

print(f"\n🎭 Processing accessories...")
accessories = supabase.table('accessories').select('id, name').execute().data

updated_accessories = 0
acc_not_found = []

for acc in accessories:
    name = acc['name']
    
    # Accessories are prefixed with "ACC "
    possible_keys = [
        f"ACC {name}",
        name,
    ]
    
    found = False
    for key in possible_keys:
        if key in file_map:
            filename = file_map[key] if isinstance(file_map[key], str) else file_map[key][0]
            public_url = supabase.storage.from_('dept56-images').get_public_url(f"ingestion/{filename}")
            supabase.table('accessories').update({'photo_url': public_url}).eq('id', acc['id']).execute()
            updated_accessories += 1
            if updated_accessories <= 3:
                print(f"  ✅ {name[:40]}")
            found = True
            break
    
    if not found:
        acc_not_found.append(name)

print("\n" + "="*60)
print(f"✅ Updated {updated_houses} houses")
print(f"✅ Updated {updated_accessories} accessories")

if not_found:
    print(f"\n⚠️  {len(not_found)} houses without matching images:")
    for name in not_found[:5]:
        print(f"  - {name}")
    if len(not_found) > 5:
        print(f"  ... and {len(not_found) - 5} more")

if acc_not_found:
    print(f"\n⚠️  {len(acc_not_found)} accessories without matching images:")
    for name in acc_not_found[:5]:
        print(f"  - {name}")
    if len(acc_not_found) > 5:
        print(f"  ... and {len(acc_not_found) - 5} more")

print("\n💡 Now refresh your browser - images should appear!")
print("="*60 + "\n")
