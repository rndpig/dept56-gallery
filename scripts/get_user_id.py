"""
Get User ID from Supabase
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
email = os.getenv("SUPABASE_USER_EMAIL")
password = os.getenv("SUPABASE_USER_PASSWORD")

supabase = create_client(supabase_url, supabase_key)

print(f"Authenticating as {email}...")
response = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

print(f"\n✅ User ID: {response.user.id}")
print(f"\nAdd this to your .env file:")
print(f"SUPABASE_USER_ID={response.user.id}")
