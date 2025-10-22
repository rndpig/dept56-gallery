#!/usr/bin/env python3
"""Quick script to check staged items in database"""

from staging_manager import StagingManager

def main():
    sm = StagingManager()
    
    # Query pending items
    result = sm.supabase.table('staged_houses').select('*').eq('status', 'pending').execute()
    
    items = result.data
    print(f"\n{'='*70}")
    print(f"Found {len(items)} pending items in staged_houses table")
    print(f"{'='*70}\n")
    
    if items:
        for i, item in enumerate(items, 1):
            print(f"{i}. {item['name']}")
            print(f"   ID: {item['id']}")
            print(f"   SKU: {item.get('item_number')}")
            print(f"   Confidence: {item.get('overall_confidence_score', 0):.2f}")
            print(f"   Original House ID: {item.get('original_house_id')}")
            print(f"   Status: {item['status']}")
            print()
    else:
        print("No pending items found!")
        print("\nChecking if ANY items exist in staged_houses...")
        all_result = sm.supabase.table('staged_houses').select('id, name, status').execute()
        print(f"Total items in staged_houses: {len(all_result.data)}")
        if all_result.data:
            print("\nAll statuses found:")
            statuses = {}
            for item in all_result.data:
                status = item['status']
                statuses[status] = statuses.get(status, 0) + 1
            for status, count in statuses.items():
                print(f"  - {status}: {count}")

if __name__ == "__main__":
    main()
