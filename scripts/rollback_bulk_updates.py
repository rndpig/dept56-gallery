#!/usr/bin/env python3
"""
Rollback script for bulk collection/series updates
Clears the notes field for the 15 houses that were updated in the previous bulk operation
"""

import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("VITE_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# List of house names that were updated in the previous bulk operation
UPDATED_HOUSES = [
    "Jolly Fellow's Toy Company",
    "S'mores & Hot Chocolate Stand", 
    "Fisher Price Pull Toy Factory",
    "Flight Training",
    "Kringle Street Snowman",
    "Coca-Cola Sliding Hill",
    "Holiday Skating Party",
    "Loading The Sleigh",
    "Lucky's Pony Rides",
    "Home For Holidays",
    "Santa's Sleigh Maker",
    "Gingerbread Cookie Mill",
    "Santa Water Tower",
    "The Christmas Candy Mill",
    "Reindeer Stables"
]

async def rollback_updates():
    """Roll back the bulk updates by clearing notes for the updated houses"""
    
    print("🔄 ROLLING BACK BULK UPDATES")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for house_name in UPDATED_HOUSES:
        try:
            # Find the house by name
            response = supabase.table('houses').select('id, name, notes').eq('name', house_name).execute()
            
            if not response.data:
                print(f"   ⚠️  House not found: {house_name}")
                error_count += 1
                continue
                
            house = response.data[0]
            house_id = house['id']
            current_notes = house.get('notes', '')
            
            # Show what we're about to clear
            print(f"   🔍 Found: {house_name}")
            if current_notes:
                print(f"       Current notes: {current_notes[:100]}{'...' if len(current_notes) > 100 else ''}")
            else:
                print(f"       Current notes: (empty)")
            
            # Clear the notes field
            update_response = supabase.table('houses').update({
                'notes': None,
                'updated_at': 'now()'
            }).eq('id', house_id).execute()
            
            if update_response.data:
                print(f"   ✅ Cleared notes for: {house_name}")
                success_count += 1
            else:
                print(f"   ❌ Failed to update: {house_name}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error processing {house_name}: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print("📊 ROLLBACK SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully rolled back: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📋 Total houses processed: {len(UPDATED_HOUSES)}")
    
    if success_count == len(UPDATED_HOUSES):
        print("\n🎉 All updates successfully rolled back!")
    elif success_count > 0:
        print(f"\n⚠️  Partially successful. {success_count}/{len(UPDATED_HOUSES)} updates rolled back.")
    else:
        print("\n💥 Rollback failed. No changes were reverted.")

def main():
    """Main function"""
    print("🚨 BULK UPDATE ROLLBACK TOOL")
    print("=" * 60)
    print("This will CLEAR the notes field for the following 15 houses:")
    print()
    
    for i, house_name in enumerate(UPDATED_HOUSES, 1):
        print(f"  {i:2d}. {house_name}")
    
    print("\n" + "=" * 60)
    
    # Confirm the rollback
    confirm = input("⚠️  Are you sure you want to roll back these updates? (y/N): ").strip().lower()
    
    if confirm == 'y':
        asyncio.run(rollback_updates())
    else:
        print("❌ Rollback cancelled.")

if __name__ == "__main__":
    main()