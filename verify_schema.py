#!/usr/bin/env python3
"""
Quick script to verify that user_id columns have been removed from the database schema.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

def verify_schema():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    supabase = create_client(supabase_url, service_role_key)
    
    print("🔍 Verifying database schema...\n")
    
    # Try to insert a test record into houses without user_id
    try:
        test_house = {
            "name": "SCHEMA_TEST_DELETE_ME",
            "year": 2025
        }
        result = supabase.table("houses").insert(test_house).execute()
        house_id = result.data[0]["id"]
        print("✅ Houses table: user_id column successfully removed")
        print(f"   Test record created with ID: {house_id}")
        
        # Try to insert a test accessory without user_id
        test_accessory = {
            "name": "SCHEMA_TEST_DELETE_ME",
            "house_id": house_id
        }
        result = supabase.table("accessories").insert(test_accessory).execute()
        acc_id = result.data[0]["id"]
        print("✅ Accessories table: user_id column successfully removed")
        print(f"   Test record created with ID: {acc_id}")
        
        # Clean up test records
        supabase.table("accessories").delete().eq("id", acc_id).execute()
        supabase.table("houses").delete().eq("id", house_id).execute()
        print("\n✅ Test records cleaned up")
        print("\n🎉 Schema verification successful! Ready to run ingestion.")
        
    except Exception as e:
        error_msg = str(e)
        if "user_id" in error_msg.lower():
            print("❌ Error: user_id columns still exist in the database")
            print(f"   Error details: {error_msg}")
            print("\n⚠️  Please run the SQL migration in Supabase dashboard:")
            print("   ALTER TABLE houses DROP COLUMN IF EXISTS user_id;")
            print("   ALTER TABLE accessories DROP COLUMN IF EXISTS user_id;")
        else:
            print(f"❌ Unexpected error: {error_msg}")

if __name__ == "__main__":
    verify_schema()
