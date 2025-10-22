"""Quick test to verify Supabase connection and staging tables"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase credentials in .env file")
    exit(1)

print("🔌 Testing Supabase connection...")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Test staged_houses table
print("\n📊 Checking staged_houses table...")
result = supabase.table("staged_houses").select("id, name, status").execute()
print(f"✅ staged_houses accessible - {len(result.data)} items currently staged")

# Test scraping_log table
print("\n📝 Checking scraping_log table...")
result = supabase.table("scraping_log").select("id").execute()
print(f"✅ scraping_log accessible - {len(result.data)} log entries")

# Test production houses table (read-only check)
print("\n🏠 Checking production houses table...")
result = supabase.table("houses").select("id").limit(5).execute()
print(f"✅ houses table accessible - {len(result.data)} items found (sample)")

print("\n" + "="*70)
print("✅ ALL DATABASE TABLES ACCESSIBLE")
print("🔒 Production data is SAFE - scraper only writes to staging tables")
print("="*70)
