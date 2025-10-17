#!/usr/bin/env python3
"""
Check the database to verify house-accessory links are properly established.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

def check_links():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    supabase = create_client(supabase_url, service_role_key)
    
    print("=" * 70)
    print("📊 DATABASE VERIFICATION REPORT")
    print("=" * 70)
    print()
    
    # Count total houses
    houses_result = supabase.table("houses").select("*", count="exact").execute()
    total_houses = houses_result.count
    print(f"🏠 Total Houses: {total_houses}")
    
    # Count total accessories
    accessories_result = supabase.table("accessories").select("*", count="exact").execute()
    total_accessories = accessories_result.count
    print(f"🔧 Total Accessories: {total_accessories}")
    
    # Count accessories WITH house_id (linked)
    linked_accessories = supabase.table("accessories").select("*", count="exact").not_.is_("house_id", "null").execute()
    linked_count = linked_accessories.count
    print(f"✅ Accessories with house_id: {linked_count}")
    
    # Count accessories WITHOUT house_id (orphaned)
    orphaned_accessories = supabase.table("accessories").select("*", count="exact").is_("house_id", "null").execute()
    orphaned_count = orphaned_accessories.count
    print(f"❌ Accessories without house_id: {orphaned_count}")
    
    print()
    print("=" * 70)
    
    # Calculate percentage
    if total_accessories > 0:
        percentage = (linked_count / total_accessories) * 100
        print(f"📈 Link Success Rate: {percentage:.1f}%")
    
    print("=" * 70)
    print()
    
    # Show some examples of linked accessories
    if linked_count > 0:
        print("🔗 Sample of linked accessories:")
        print("-" * 70)
        
        sample = supabase.table("accessories").select("id, name, house_id").not_.is_("house_id", "null").limit(5).execute()
        
        for acc in sample.data:
            # Get the house name for this accessory
            house = supabase.table("houses").select("name").eq("id", acc["house_id"]).execute()
            house_name = house.data[0]["name"] if house.data else "Unknown"
            
            print(f"  • {acc['name'][:40]}")
            print(f"    └─ Linked to: {house_name[:40]}")
            print()
    
    print("=" * 70)
    
    # Final verdict
    if orphaned_count == 0:
        print("✅ SUCCESS! All accessories are properly linked to houses! 🎉")
    elif percentage >= 90:
        print("⚠️  Most accessories are linked, but some orphans remain.")
    else:
        print("❌ Many accessories are not linked. There may be an issue.")
    
    print("=" * 70)

if __name__ == "__main__":
    check_links()
