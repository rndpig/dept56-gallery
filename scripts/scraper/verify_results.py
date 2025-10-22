"""Verify staged results in database"""
import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

supabase = create_client(os.getenv("VITE_SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

print("=" * 70)
print("🔍 Verification Report - Staged Houses")
print("=" * 70)

# Get staged houses
result = supabase.table('staged_houses')\
    .select('*')\
    .eq('status', 'pending')\
    .order('created_at', desc=True)\
    .limit(5)\
    .execute()

print(f"\n📦 Found {len(result.data)} staged houses:\n")

for i, house in enumerate(result.data, 1):
    print(f"{i}. {house['name']}")
    print(f"   Item Number: {house.get('item_number', 'N/A')}")
    print(f"   Series: {house.get('discovered_series', 'N/A')}")
    print(f"   Intro Year: {house.get('intro_year', 'N/A')}")
    print(f"   Retire Year: {house.get('retire_year', 'N/A')}")
    print(f"   Description: {house.get('description', 'N/A')[:100]}...")
    
    images = json.loads(house.get('additional_images', '[]'))
    print(f"   Images: {len(images)} available")
    if images:
        print(f"      Primary: {images[0][:60]}...")
    
    print(f"   Confidence Score: {house['overall_confidence_score']:.2f}")
    print(f"   Name Match: {house['name_match_score']:.2f}")
    print(f"   Source URL: {house.get('dept56_retired_url', 'N/A')[:60]}...")
    print(f"   Status: {house['status']}")
    print()

# Check scraping logs
print("=" * 70)
print("📝 Recent Scraping Logs")
print("=" * 70)

logs = supabase.table('scraping_log')\
    .select('*')\
    .order('created_at', desc=True)\
    .limit(5)\
    .execute()

print(f"\n✅ Successful: {sum(1 for log in logs.data if log['success'])}")
print(f"❌ Failed: {sum(1 for log in logs.data if not log['success'])}")

print("\n" + "=" * 70)
print("✅ Verification Complete!")
print("=" * 70)
