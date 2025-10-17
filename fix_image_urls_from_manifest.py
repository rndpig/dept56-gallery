import os
import json
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('VITE_SUPABASE_ANON_KEY')
)

# Load the manifest
manifest_path = "ingestion_output/manifest_20251016_193056.json"
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Loaded {len(manifest)} entries from manifest")

# Get all houses from database
houses = supabase.table('houses').select('id, name').execute()
houses_by_name = {h['name']: h['id'] for h in houses.data}
print(f"Found {len(houses_by_name)} houses in database")

# Get all accessories from database  
accessories = supabase.table('accessories').select('id, name').execute()
accessories_by_name = {a['name']: a['id'] for a in accessories.data}
print(f"Found {len(accessories_by_name)} accessories in database\n")

matched_houses = 0
matched_accessories = 0
house_updates = []
accessory_updates = []

for entry in manifest:
    if not entry['success']:
        continue
    
    # Get the stem (filename without .docx)
    stem = entry['file'].replace('.docx', '')
    
    # Get titles from metadata
    primary_title = entry['metadata']['primary_title']
    accessory_titles = entry['metadata'].get('accessory_titles', [])
    
    # Update house
    if primary_title in houses_by_name:
        house_id = houses_by_name[primary_title]
        image_path = f"ingestion/{stem}_primary.jpeg"
        public_url = f"https://xctottgirqkkmjmutoon.supabase.co/storage/v1/object/public/dept56-images/{image_path}"
        
        house_updates.append({
            'id': house_id,
            'photo_url': public_url
        })
        matched_houses += 1
        
        if matched_houses <= 5:
            print(f"House: {primary_title}")
            print(f"  Image: {stem}_primary.jpeg")
            print(f"  URL: {public_url}\n")
    
    # Update accessories
    for i, acc_title in enumerate(accessory_titles):
        if acc_title in accessories_by_name:
            acc_id = accessories_by_name[acc_title]
            acc_image_path = f"ingestion/{stem}_acc{i}.jpeg"
            acc_public_url = f"https://xctottgirqkkmjmutoon.supabase.co/storage/v1/object/public/dept56-images/{acc_image_path}"
            
            accessory_updates.append({
                'id': acc_id,
                'photo_url': acc_public_url
            })
            matched_accessories += 1

print(f"\nMatched {matched_houses} houses")
print(f"Matched {matched_accessories} accessories")

# Update database in batches
print("\nUpdating database...")

if house_updates:
    for update in house_updates:
        supabase.table('houses').update({
            'photo_url': update['photo_url']
        }).eq('id', update['id']).execute()
    print(f"✓ Updated {len(house_updates)} houses")

if accessory_updates:
    for update in accessory_updates:
        supabase.table('accessories').update({
            'photo_url': update['photo_url']
        }).eq('id', update['id']).execute()
    print(f"✓ Updated {len(accessory_updates)} accessories")

print("\nDone!")
