# Quick script to verify data and photo URLs in Supabase
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables 
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("VITE_SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def get_stats():
    # Get total counts
    houses = supabase.table("houses").select("*").execute()
    accessories = supabase.table("accessories").select("*").execute()
    
    # Count items with photos
    houses_with_photos = [h for h in houses.data if h.get("photo_url")]
    accessories_with_photos = [a for a in accessories.data if a.get("photo_url")]
    
    print("HOUSES")
    print(f"Total: {len(houses.data)}")
    print(f"With photos: {len(houses_with_photos)}")
    print(f"Missing photos: {len(houses.data) - len(houses_with_photos)}")
    print()
    print("ACCESSORIES") 
    print(f"Total: {len(accessories.data)}")
    print(f"With photos: {len(accessories_with_photos)}")
    print(f"Missing photos: {len(accessories.data) - len(accessories_with_photos)}")
    print()
    
    # Sample some records with photos
    print("SAMPLE HOUSES WITH PHOTOS:")
    for house in houses_with_photos[:3]:
        print(f"{house['name']}: {house['photo_url']}")
    print()
    
    print("SAMPLE ACCESSORIES WITH PHOTOS:")
    for acc in accessories_with_photos[:3]:
        print(f"{acc['name']}: {acc['photo_url']}")

if __name__ == "__main__":
    get_stats()