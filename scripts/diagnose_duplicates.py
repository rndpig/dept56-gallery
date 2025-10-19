"""
Diagnostic script to check for duplicate houses in Supabase
Runs the diagnostic queries and displays results
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key
url: str = os.environ.get("VITE_SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)

def run_query(query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results"""
    try:
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        return result.data
    except Exception as e:
        # Fallback: use direct table queries
        print(f"Note: Direct SQL execution not available, using table queries")
        return []

def find_duplicate_names():
    """Find houses with duplicate names"""
    print("\n" + "="*80)
    print("FINDING DUPLICATE HOUSE NAMES")
    print("="*80)
    
    # Get all houses
    result = supabase.table('houses').select('id, name, created_at, sku, year, price').execute()
    houses = result.data
    
    # Find duplicates
    name_map = {}
    for house in houses:
        name = house['name']
        if name not in name_map:
            name_map[name] = []
        name_map[name].append(house)
    
    duplicates = {name: records for name, records in name_map.items() if len(records) > 1}
    
    if not duplicates:
        print("✅ No duplicate house names found!")
        return
    
    print(f"\n⚠️  Found {len(duplicates)} duplicate house names:")
    print(f"   Total duplicate records: {sum(len(records) for records in duplicates.values())}")
    print("\n")
    
    for name, records in sorted(duplicates.items()):
        print(f"📦 {name}")
        print(f"   {len(records)} records found:")
        
        for i, record in enumerate(records, 1):
            # Get accessory count for this house
            links = supabase.table('house_accessory_links').select('id').eq('house_id', record['id']).execute()
            accessory_count = len(links.data) if links.data else 0
            
            print(f"   {i}. ID: {record['id'][:8]}... | Created: {record['created_at'][:19]} | "
                  f"Accessories: {accessory_count} | SKU: {record.get('sku', 'N/A')} | "
                  f"Year: {record.get('year', 'N/A')} | Price: ${record.get('price', 'N/A')}")
        print()

def show_duplicate_details():
    """Show detailed information about duplicates including which should be kept"""
    print("\n" + "="*80)
    print("RECOMMENDED ACTIONS (Houses with accessories will be kept)")
    print("="*80)
    
    # Get all houses
    result = supabase.table('houses').select('id, name, created_at, sku, year, price').execute()
    houses = result.data
    
    # Find duplicates
    name_map = {}
    for house in houses:
        name = house['name']
        if name not in name_map:
            name_map[name] = []
        name_map[name].append(house)
    
    duplicates = {name: records for name, records in name_map.items() if len(records) > 1}
    
    if not duplicates:
        return
    
    keep_count = 0
    delete_count = 0
    
    for name, records in sorted(duplicates.items()):
        # Get accessory counts for each record
        records_with_counts = []
        for record in records:
            links = supabase.table('house_accessory_links').select('id').eq('house_id', record['id']).execute()
            accessory_count = len(links.data) if links.data else 0
            records_with_counts.append((record, accessory_count))
        
        # Sort by accessory count (descending), then by created_at (ascending)
        records_with_counts.sort(key=lambda x: (-x[1], x[0]['created_at']))
        
        # First record is kept, rest are deleted
        kept_record, kept_count = records_with_counts[0]
        
        print(f"\n📦 {name}")
        print(f"   ✅ KEEP: ID {kept_record['id'][:8]}... | {kept_count} accessories | Created: {kept_record['created_at'][:19]}")
        keep_count += 1
        
        for record, acc_count in records_with_counts[1:]:
            print(f"   ❌ DELETE: ID {record['id'][:8]}... | {acc_count} accessories | Created: {record['created_at'][:19]}")
            delete_count += 1
    
    print("\n" + "="*80)
    print(f"SUMMARY: Will keep {keep_count} houses, delete {delete_count} duplicates")
    print("="*80)

def count_totals():
    """Show total counts"""
    print("\n" + "="*80)
    print("DATABASE TOTALS")
    print("="*80)
    
    houses = supabase.table('houses').select('id', count='exact').execute()
    accessories = supabase.table('accessories').select('id', count='exact').execute()
    links = supabase.table('house_accessory_links').select('id', count='exact').execute()
    
    print(f"Total houses: {houses.count}")
    print(f"Total accessories: {accessories.count}")
    print(f"Total house-accessory links: {links.count}")

if __name__ == "__main__":
    print("\n🔍 DUPLICATE HOUSE DIAGNOSTIC TOOL")
    print("="*80)
    
    try:
        count_totals()
        find_duplicate_names()
        show_duplicate_details()
        
        print("\n✨ Diagnostic complete!")
        print("\nNext steps:")
        print("1. Review the recommendations above")
        print("2. Run fix_duplicates.sql in Supabase SQL Editor (backs up first!)")
        print("3. Or use scripts/fix_duplicates.py for automated fix")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
