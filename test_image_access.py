"""
Test if Supabase Storage images are publicly accessible
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

url: str = os.environ.get("VITE_SUPABASE_URL")
key: str = os.environ.get("VITE_SUPABASE_ANON_KEY")

# Create Supabase client
supabase: Client = create_client(url, key)

print("\n🔍 Testing image accessibility...\n")

# Fetch a house with a photo
response = supabase.table('houses').select('id, name, photo_url').not_.is_('photo_url', 'null').limit(1).execute()

if response.data and len(response.data) > 0:
    house = response.data[0]
    print(f"📸 Testing image for: {house['name']}")
    print(f"🔗 Image URL: {house['photo_url']}\n")
    
    # Try to fetch the image
    try:
        img_response = requests.get(house['photo_url'], timeout=5)
        if img_response.status_code == 200:
            print("✅ SUCCESS! Image is publicly accessible")
            print(f"   Content-Type: {img_response.headers.get('Content-Type')}")
            print(f"   Size: {len(img_response.content)} bytes")
        elif img_response.status_code == 403:
            print("❌ FORBIDDEN! The storage bucket is NOT public")
            print("   You need to make the 'dept56-images' bucket public in Supabase Dashboard")
            print("\n📝 How to fix:")
            print("   1. Go to: https://supabase.com/dashboard/project/xctottgirqkkmjmutoon/storage/buckets")
            print("   2. Click on 'dept56-images' bucket")
            print("   3. Look for 'Public bucket' toggle and enable it")
        elif img_response.status_code == 404:
            print("❌ NOT FOUND! Image doesn't exist at this URL")
        else:
            print(f"❌ ERROR! HTTP {img_response.status_code}")
            print(f"   Response: {img_response.text[:200]}")
    except Exception as e:
        print(f"❌ ERROR accessing image: {e}")
else:
    print("❌ No houses with photos found in database")

print("\n" + "="*60)
