import os, json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

with open("ingestion_output/manifest_20251016_193056.json", 'r', encoding='utf-8') as f:
    manifest = json.load(f)

houses = supabase.table('houses').select('id, name').execute()
houses_by_name = {h['name']: h['id'] for h in houses.data}

print(f"Updating {len(manifest)} entries...")
count = 0

for entry in manifest:
    if entry['success'] and entry['metadata']['primary_title'] in houses_by_name:
        house_id = houses_by_name[entry['metadata']['primary_title']]
        stem = entry['file'].replace('.docx', '')
        url = f"https://xctottgirqkkmjmutoon.supabase.co/storage/v1/object/public/dept56-images/ingestion/{stem}_primary.jpeg"
        supabase.table('houses').update({'photo_url': url}).eq('id', house_id).execute()
        count += 1

print(f"Updated {count} houses!")
