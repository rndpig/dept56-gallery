"""
Clear Supabase Storage Bucket
Removes all files from the dept56-images bucket
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
user_id = os.getenv("SUPABASE_USER_ID")

supabase = create_client(supabase_url, supabase_key)
bucket_name = "dept56-images"

print(f"\n{'='*70}")
print(f"CLEARING BUCKET: {bucket_name}")
print(f"{'='*70}\n")

# List and delete all files in user folder
try:
    user_files = supabase.storage.from_(bucket_name).list(user_id)
    
    if user_files:
        print(f"Found {len(user_files)} files in user folder")
        
        # Delete in batches
        file_paths = [f"{user_id}/{f['name']}" for f in user_files]
        
        # Supabase allows batch deletes
        for i in range(0, len(file_paths), 100):
            batch = file_paths[i:i+100]
            supabase.storage.from_(bucket_name).remove(batch)
            print(f"  Deleted batch {i//100 + 1}: {len(batch)} files")
        
        print(f"\n✅ Deleted {len(file_paths)} files from {user_id}/")
    else:
        print("✅ User folder is already empty")
        
except Exception as e:
    print(f"Error: {str(e)}")

# Verify bucket is empty
try:
    remaining = supabase.storage.from_(bucket_name).list(user_id)
    if remaining:
        print(f"\n⚠️  Warning: {len(remaining)} files still in bucket")
    else:
        print(f"\n✅ Bucket {bucket_name}/{user_id} is now empty")
except Exception as e:
    print(f"\n✅ Bucket cleared (folder may not exist yet)")

print(f"{'='*70}\n")
