"""
Test authenticated access to the database
"""
import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    anon_key = os.getenv("VITE_SUPABASE_ANON_KEY")
    email = os.getenv("SUPABASE_USER_EMAIL")
    password = os.getenv("SUPABASE_USER_PASSWORD")
    
    print("=" * 70)
    print("🔍 TESTING AUTHENTICATED ACCESS TO DATABASE")
    print("=" * 70)
    print()
    
    supabase = create_client(supabase_url, anon_key)
    
    try:
        print("Signing in...")
        auth = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        print("✅ Successfully signed in!")
        print()
        
        print("Fetching houses...")
        houses = supabase.table("houses").select("*").execute()
        total_houses = len(houses.data)
        missing_photos = len([h for h in houses.data if not h.get('photo_url')])
        print(f"Found {total_houses} houses")
        print(f"Houses missing photos: {missing_photos}")
        
        if houses.data:
            print("\nSample houses missing photos:")
            for h in [h for h in houses.data if not h.get('photo_url')][:5]:
                print(f"- {h['name']}")
        
        print("\nFetching accessories...")
        accessories = supabase.table("accessories").select("*").execute()
        total_acc = len(accessories.data)
        missing_acc_photos = len([a for a in accessories.data if not a.get('photo_url')])
        print(f"Found {total_acc} accessories")
        print(f"Accessories missing photos: {missing_acc_photos}")
        
        if accessories.data:
            print("\nSample accessories missing photos:")
            for a in [a for a in accessories.data if not a.get('photo_url')][:5]:
                print(f"- {a['name']}")
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()