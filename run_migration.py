"""
Fix user_id constraint in Supabase database
Makes user_id nullable to support bulk imports
"""
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

# Read SQL file
with open("fix_user_id_constraint.sql", "r") as f:
    sql = f.read()

print("Executing SQL to make user_id nullable...")
print(sql)
print("\n" + "="*60)

try:
    # Execute the SQL
    # Note: Supabase Python client doesn't have direct SQL execution
    # You'll need to run this in the Supabase SQL Editor instead
    
    print("\n⚠️  The Supabase Python client doesn't support direct SQL execution.")
    print("   Please run this SQL in the Supabase Dashboard:")
    print(f"\n   1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}")
    print("   2. Click 'SQL Editor' in the left sidebar")
    print("   3. Click 'New Query'")
    print("   4. Paste the SQL above")
    print("   5. Click 'Run'")
    print("\n   Or copy this SQL:\n")
    print(sql)
    
except Exception as e:
    print(f"Error: {e}")
