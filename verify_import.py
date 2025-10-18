# Quick script to verify data imported to Supabase
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

# Get counts
def get_counts():
    # Get houses count
    houses = supabase.table("houses").select("*").execute()
    print(f"Houses: {len(houses.data)}")

    # Get accessories count
    accessories = supabase.table("accessories").select("*").execute() 
    print(f"Accessories: {len(accessories.data)}")

    # Sample a house
    if houses.data:
        house = houses.data[0]
        print("\nSample House:")
        print(f"Name: {house['name']}")
        print(f"Year: {house['year']}")
        print(f"Photo URL: {house['photo_url']}")

        # Get accessories for this house
        related = supabase.table("accessories").select("*").eq("house_id", house["id"]).execute()
        print(f"\nLinked Accessories: {len(related.data)}")
        for acc in related.data[:3]:
            print(f"- {acc['name']}")

if __name__ == "__main__":
    get_counts()