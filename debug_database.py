"""
Debug database connection and analyze photo issues
"""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

def get_supabase_client() -> Client:
    """Get Supabase client with error handling"""
    load_dotenv()
    
    url = os.getenv('VITE_SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials!")
        sys.exit(1)
    
    return create_client(url, key)

def main():
    print("\n🔍 Testing database connection...")
    
    try:
        supabase = get_supabase_client()
        
        # Test houses table
        print("\nTesting houses table...")
        houses = supabase.table('houses').select('*').execute()
        print(f"Houses response: {houses}")
        print(f"Number of houses: {len(houses.data) if houses.data else 0}")
        
        if houses.data:
            print("\nFirst house record:")
            print(houses.data[0])
        
        # Test accessories table
        print("\nTesting accessories table...")
        accessories = supabase.table('accessories').select('*').execute()
        print(f"Accessories response: {accessories}")
        print(f"Number of accessories: {len(accessories.data) if accessories.data else 0}")
        
        if accessories.data:
            print("\nFirst accessory record:")
            print(accessories.data[0])
        
    except Exception as e:
        print(f"\n❌ Error accessing database: {str(e)}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()