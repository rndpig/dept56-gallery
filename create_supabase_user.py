"""
Create a Supabase user account for data ingestion.
This script signs up a new user with the credentials from .env
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")
USER_EMAIL = os.getenv("SUPABASE_USER_EMAIL")
USER_PASSWORD = os.getenv("SUPABASE_USER_PASSWORD")

if not all([SUPABASE_URL, SUPABASE_KEY, USER_EMAIL, USER_PASSWORD]):
    print("❌ Missing environment variables in .env file")
    exit(1)

try:
    # Create Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Sign up the user
    print(f"Creating user account: {USER_EMAIL}")
    response = supabase.auth.sign_up({
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    
    if response.user:
        print(f"✅ User created successfully!")
        print(f"   User ID: {response.user.id}")
        print(f"   Email: {response.user.email}")
        print(f"\n⚠️  Check your email ({USER_EMAIL}) for a confirmation link")
        print(f"   After confirming, you can run the ingestion script")
    else:
        print("❌ Failed to create user - user may already exist")
        print("   Try signing in instead:")
        
        # Try signing in
        sign_in_response = supabase.auth.sign_in_with_password({
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        
        if sign_in_response.user:
            print(f"✅ Successfully signed in as {USER_EMAIL}")
            print(f"   User ID: {sign_in_response.user.id}")
        else:
            print("❌ Could not sign in either. Check your credentials.")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure your Supabase project has Email Auth enabled")
    print("2. Check Settings → Authentication → Providers → Email")
    print("3. Disable 'Confirm email' if you want to skip email verification")
