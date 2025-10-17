"""
Fix missing photo_url values in database by generating correct URLs
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, service_key)

print("\n🔧 Fixing photo URLs in database...\n")

# Get all houses
houses = supabase.table('houses').select('id, name').execute().data
print(f"📦 Found {len(houses)} houses")

# Get all accessories  
accessories = supabase.table('accessories').select('id, name').execute().data
print(f"📦 Found {len(accessories)} accessories\n")

# Function to sanitize filename (same logic as ingestion script)
def sanitize_filename(s: str) -> str:
    """Remove special characters for filename"""
    import re
    s = s.replace('�', "'")  # Fix encoding issue
    s = re.sub(r'[^\w\s\'-]', '', s)  # Remove special chars
    s = re.sub(r'\s+', ' ', s).strip()  # Normalize whitespace
    return s.replace(' ', '_')

updated_houses = 0
updated_accessories = 0
errors = []

# Update houses
print("🏠 Updating house photo URLs...")
for house in houses:
    safe_name = sanitize_filename(house['name'])
    # The ingestion script saves images as: "{name}_primary.jpeg"
    image_path = f"ingestion/{safe_name}_primary.jpeg"
    
    # Generate public URL
    public_url = supabase.storage.from_('dept56-images').get_public_url(image_path)
    
    # Update database
    try:
        supabase.table('houses').update({'photo_url': public_url}).eq('id', house['id']).execute()
        updated_houses += 1
        if updated_houses <= 3:  # Show first 3 examples
            print(f"  ✅ {house['name'][:40]}")
    except Exception as e:
        errors.append(f"House '{house['name']}': {e}")

print(f"\n🎭 Updating accessory photo URLs...")
for acc in accessories:
    safe_name = sanitize_filename(acc['name'])
    # The ingestion script saves images as: "ACC {name}_primary.jpeg"
    image_path = f"ingestion/ACC_{safe_name}_primary.jpeg"
    
    # Generate public URL
    public_url = supabase.storage.from_('dept56-images').get_public_url(image_path)
    
    # Update database
    try:
        supabase.table('accessories').update({'photo_url': public_url}).eq('id', acc['id']).execute()
        updated_accessories += 1
        if updated_accessories <= 3:  # Show first 3 examples
            print(f"  ✅ {acc['name'][:40]}")
    except Exception as e:
        errors.append(f"Accessory '{acc['name']}': {e}")

print("\n" + "="*60)
print(f"✅ Updated {updated_houses} houses")
print(f"✅ Updated {updated_accessories} accessories")

if errors:
    print(f"\n⚠️  {len(errors)} errors:")
    for err in errors[:5]:  # Show first 5
        print(f"  - {err}")
else:
    print("\n🎉 All photo URLs updated successfully!")
    print("\n💡 Now refresh your browser - images should appear!")

print("="*60 + "\n")
