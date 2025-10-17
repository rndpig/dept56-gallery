"""Check what users exist in Supabase"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Query auth.users table
try:
    # Using service role key, we can query auth.users
    response = supabase.auth.admin.list_users()
    
    if response and len(response) > 0:
        print(f"Found {len(response)} user(s):\n")
        for user in response:
            print(f"  User ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Created: {user.created_at}")
            print(f"  Confirmed: {user.email_confirmed_at is not None}")
            print()
    else:
        print("No users found in database")
        print("\n💡 Solution: Remove the NOT NULL constraint from user_id in the database schema")
        print("   OR create a system user for bulk imports")
        
except Exception as e:
    print(f"Error querying users: {e}")
    print("\n💡 The database schema requires user_id, but we're doing bulk imports")
    print("   with a service role key that bypasses authentication.")
    print("\n   Options:")
    print("   1. Make user_id nullable in the database (ALTER TABLE)")
    print("   2. Create a 'system' user for bulk imports")
    print("   3. Remove the foreign key constraint temporarily")
