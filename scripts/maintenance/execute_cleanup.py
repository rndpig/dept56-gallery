import json
import os
from datetime import datetime
from supabase import create_client, Client
import sys

def load_cleanup_plan(filename: str) -> dict:
    """Load the cleanup plan from file."""
    with open(filename, 'r') as f:
        return json.load(f)

def execute_cleanup(plan: dict) -> None:
    """Execute the cleanup plan using the Supabase client."""
    # Initialize Supabase client
    url: str = os.environ.get("SUPABASE_URL", "")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
    
    supabase: Client = create_client(url, key)
    
    records_to_delete = plan['cleanup_plan']['records_to_delete']
    primary_records = plan['cleanup_plan']['primary_records']
    by_group = plan['cleanup_plan']['by_group']
    
    print("\nExecuting cleanup plan...")
    print(f"Total records to delete: {len(records_to_delete)}")
    
    try:
        # Execute deletions in chunks to avoid potential request size limits
        chunk_size = 10
        for i in range(0, len(records_to_delete), chunk_size):
            chunk = records_to_delete[i:i + chunk_size]
            print(f"\nDeleting chunk of {len(chunk)} records...")
            result = supabase.table('houses').delete().in_('id', chunk).execute()
            print(f"Successfully deleted {len(chunk)} records")
        
        print("\nCleanup completed successfully!")
        
        # Print summary of kept records
        print("\nKept primary records:")
        for name, record in primary_records.items():
            print(f"\n{name}:")
            print(f"  ID: {record['id']}")
            print(f"  Year: {record.get('year', 'None')}")
            print(f"  Has photo: {'Yes' if record.get('photo_url') else 'No'}")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        sys.exit(1)

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Please provide the path to the cleanup plan JSON file")
        print("Usage: python execute_cleanup.py <cleanup_plan.json>")
        sys.exit(1)
    
    plan_file = sys.argv[1]
    if not os.path.exists(plan_file):
        print(f"Error: Cleanup plan file '{plan_file}' not found")
        sys.exit(1)
    
    # Load and validate plan
    try:
        plan = load_cleanup_plan(plan_file)
        if not all(k in plan for k in ['timestamp', 'total_groups', 'total_duplicates', 'cleanup_plan']):
            print("Error: Invalid cleanup plan file format")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading cleanup plan: {e}")
        sys.exit(1)
    
    # Confirm execution
    print(f"\nLoaded cleanup plan from {plan_file}")
    print(f"Plan timestamp: {plan['timestamp']}")
    print(f"Total duplicate groups: {plan['total_groups']}")
    print(f"Total records to remove: {plan['total_duplicates']}")
    
    response = input("\nProceed with cleanup? This action cannot be undone! (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled")
        sys.exit(0)
    
    # Execute cleanup
    execute_cleanup(plan)

if __name__ == "__main__":
    main()