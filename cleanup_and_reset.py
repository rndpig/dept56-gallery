"""
Cleanup and Reset Script for Department 56 Gallery
===================================================
This script will:
1. Delete all records from houses and accessories tables
2. Delete the ingestion state file to force full re-processing
3. Optionally clear images from Supabase Storage

Run this before re-importing data with the updated ingestion script.
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STATE_FILE = r"C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app\ingestion_output\ingestion_state.json"

def cleanup_database():
    """Delete all records from houses and accessories tables."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print("\n🗑️  Cleaning up database...")
        
        # Delete all accessories first (due to foreign key constraint)
        print("   Deleting accessories...")
        response = supabase.table("accessories").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        acc_count = len(response.data) if response.data else 0
        print(f"   ✅ Deleted {acc_count} accessory record(s)")
        
        # Delete all houses
        print("   Deleting houses...")
        response = supabase.table("houses").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        house_count = len(response.data) if response.data else 0
        print(f"   ✅ Deleted {house_count} house record(s)")
        
        print(f"\n✅ Database cleanup complete!")
        print(f"   Total records deleted: {acc_count + house_count}")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        return False

def reset_ingestion_state():
    """Delete the ingestion state file to force full re-processing."""
    try:
        if os.path.exists(STATE_FILE):
            # Backup the old state file
            backup_file = STATE_FILE.replace(".json", "_backup.json")
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(STATE_FILE, backup_file)
            print(f"\n✅ Backed up ingestion state to: {backup_file}")
            print(f"✅ Reset ingestion state - full re-processing will occur")
        else:
            print(f"\n⚠️  No ingestion state file found at: {STATE_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error resetting ingestion state: {e}")
        return False

def main():
    print("=" * 60)
    print("Department 56 Gallery - Cleanup and Reset")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete all data from the database!")
    print("   - All house records will be deleted")
    print("   - All accessory records will be deleted")
    print("   - Ingestion state will be reset")
    print("   - Images in Supabase Storage will remain")
    
    response = input("\n❓ Are you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("\n❌ Cleanup cancelled")
        return
    
    print("\n🚀 Starting cleanup process...\n")
    
    # Step 1: Clean database
    db_success = cleanup_database()
    
    # Step 2: Reset ingestion state
    state_success = reset_ingestion_state()
    
    # Summary
    print("\n" + "=" * 60)
    if db_success and state_success:
        print("✅ Cleanup complete! You can now run the ingestion script.")
        print("\nNext steps:")
        print("1. Run: python ingest_docx.py")
        print("2. Wait for all 456 documents to be processed")
        print("3. Check the database to verify proper house-accessory links")
    else:
        print("⚠️  Cleanup completed with errors. Check the output above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
