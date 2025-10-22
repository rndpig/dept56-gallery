"""Check scraping logs to diagnose issues"""
import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

supabase = create_client(os.getenv("VITE_SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

print("📝 Recent scraping log entries:\n")
result = supabase.table("scraping_log").select("*").order("created_at", desc=True).limit(5).execute()

for log in result.data:
    print(f"Query: {log['search_query']}")
    print(f"  Source: {log['source_site']}")
    print(f"  Success: {log['success']}")
    print(f"  Results: {log['results_found']}")
    if log['error_type']:
        print(f"  Error: {log['error_type']}")
    if log['error_message']:
        print(f"  Message: {log['error_message']}")
    print(f"  Time: {log['execution_time_ms']}ms")
    print()
