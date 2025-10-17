#!/usr/bin/env python3
"""
Test that the React app can access the data with the anon key.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

def test_anon_key_access():
    load_dotenv()
    
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    anon_key = os.getenv("VITE_SUPABASE_ANON_KEY")
    
    print("=" * 70)
    print("🔍 TESTING ANON KEY ACCESS TO DATABASE")
    print("=" * 70)
    print()
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Using anon key: {anon_key[:20]}...")
    print()
    
    # Create client with anon key (same as React app uses)
    supabase = create_client(supabase_url, anon_key)
    
    try:
        # Try to fetch houses
        print("Attempting to fetch houses with anon key...")
        response = supabase.table("houses").select("*").limit(5).execute()
        
        if response.data:
            print(f"✅ SUCCESS! Found {len(response.data)} houses")
            print(f"   Sample: {response.data[0]['name']}")
        else:
            print("❌ No data returned (but no error)")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("This means the React app cannot access the data.")
        print()
        print("SOLUTION: The anon key needs RLS policies OR we need to use service role key in React.")
        print()
        
    try:
        # Try to fetch accessories
        print()
        print("Attempting to fetch accessories with anon key...")
        response = supabase.table("accessories").select("*").limit(5).execute()
        
        if response.data:
            print(f"✅ SUCCESS! Found {len(response.data)} accessories")
            print(f"   Sample: {response.data[0]['name']}")
        else:
            print("❌ No data returned (but no error)")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        
    print()
    print("=" * 70)

if __name__ == "__main__":
    test_anon_key_access()
