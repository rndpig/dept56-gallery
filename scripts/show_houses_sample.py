"""
Show sample of items currently in houses table to verify what we're dealing with
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("CURRENT HOUSES TABLE - FIRST 100 ITEMS")
print("=" * 80)

houses = supabase.table('houses').select('name').order('name').limit(100).execute()

for i, house in enumerate(houses.data, 1):
    print(f"{i:3d}. {house['name']}")

print(f"\nTotal shown: {len(houses.data)}")
print(f"\nDo any of these look like accessories to you?")
