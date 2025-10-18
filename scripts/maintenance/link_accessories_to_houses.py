"""
Link Accessories to Houses based on Ingestion Manifest

This script reads the ingestion manifest files to identify which accessories
originated from the same Word document as each house, then creates the
appropriate links in the house_accessory_links table.

Usage:
    $env:SUPABASE_URL = "your-project-url"
    $env:SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
    python link_accessories_to_houses.py
"""

import json
import os
from datetime import datetime
from supabase import create_client, Client
from typing import Dict, List, Tuple
import glob

def load_latest_manifest() -> List[Dict]:
    """Load the most recent manifest file from ingestion_output/."""
    manifest_files = glob.glob("ingestion_output/manifest_*.json")
    if not manifest_files:
        raise FileNotFoundError("No manifest files found in ingestion_output/")
    
    # Get the latest manifest by timestamp in filename
    latest_manifest = max(manifest_files)
    print(f"Loading manifest: {latest_manifest}")
    
    with open(latest_manifest, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_house_accessory_mappings(manifest: List[Dict]) -> List[Tuple[str, str]]:
    """
    Extract (house_id, accessory_id) pairs from the manifest.
    
    Returns:
        List of tuples (house_id, accessory_id) to create links
    """
    mappings = []
    
    for entry in manifest:
        if not entry.get('success'):
            continue
            
        house_id = entry.get('house_id')
        accessory_ids = entry.get('accessory_ids', [])
        
        if house_id and accessory_ids:
            for accessory_id in accessory_ids:
                mappings.append((house_id, accessory_id))
    
    return mappings

def get_current_links(supabase: Client) -> set:
    """Get all existing house-accessory links."""
    response = supabase.table('house_accessory_links').select('house_id, accessory_id').execute()
    return {(link['house_id'], link['accessory_id']) for link in response.data}

def verify_ids_exist(supabase: Client, mappings: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    Verify that house and accessory IDs exist in the database.
    
    Returns:
        Tuple of (valid_mappings, invalid_mappings)
    """
    # Get all house IDs
    houses_response = supabase.table('houses').select('id').execute()
    house_ids = {h['id'] for h in houses_response.data}
    
    # Get all accessory IDs
    accessories_response = supabase.table('accessories').select('id').execute()
    accessory_ids = {a['id'] for a in accessories_response.data}
    
    valid = []
    invalid = []
    
    for house_id, accessory_id in mappings:
        if house_id in house_ids and accessory_id in accessory_ids:
            valid.append((house_id, accessory_id))
        else:
            invalid.append((house_id, accessory_id))
            if house_id not in house_ids:
                print(f"  Warning: House ID not found: {house_id}")
            if accessory_id not in accessory_ids:
                print(f"  Warning: Accessory ID not found: {accessory_id}")
    
    return valid, invalid

def create_links(supabase: Client, mappings: List[Tuple[str, str]], existing_links: set) -> Dict:
    """
    Create house-accessory links in batches.
    
    Returns:
        Dictionary with statistics about created links
    """
    # Filter out existing links
    new_mappings = [(h, a) for h, a in mappings if (h, a) not in existing_links]
    
    if not new_mappings:
        return {
            'total_mappings': len(mappings),
            'already_existed': len(mappings),
            'newly_created': 0,
            'errors': 0
        }
    
    print(f"\nCreating {len(new_mappings)} new links...")
    
    # Create links in batches of 100
    batch_size = 100
    created = 0
    errors = 0
    
    for i in range(0, len(new_mappings), batch_size):
        batch = new_mappings[i:i + batch_size]
        
        # Convert to list of dicts for Supabase insert
        links_to_insert = [
            {'house_id': house_id, 'accessory_id': accessory_id}
            for house_id, accessory_id in batch
        ]
        
        try:
            response = supabase.table('house_accessory_links').insert(links_to_insert).execute()
            created += len(response.data)
            print(f"  Created batch {i//batch_size + 1}: {len(response.data)} links")
        except Exception as e:
            print(f"  Error creating batch {i//batch_size + 1}: {e}")
            errors += len(batch)
    
    return {
        'total_mappings': len(mappings),
        'already_existed': len(existing_links),
        'newly_created': created,
        'errors': errors
    }

def generate_report(stats: Dict, invalid_count: int):
    """Generate a summary report."""
    print("\n" + "="*60)
    print("HOUSE-ACCESSORY LINKING REPORT")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTotal house-accessory mappings found: {stats['total_mappings']}")
    print(f"Invalid mappings (IDs not found): {invalid_count}")
    print(f"Links already existed: {stats['already_existed']}")
    print(f"New links created: {stats['newly_created']}")
    print(f"Errors: {stats['errors']}")
    print("="*60)

def main():
    """Main execution function."""
    # Initialize Supabase client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
    
    supabase: Client = create_client(url, key)
    
    print("House-Accessory Linking Script")
    print("="*60)
    
    # Load manifest
    manifest = load_latest_manifest()
    print(f"Loaded {len(manifest)} manifest entries")
    
    # Extract mappings
    print("\nExtracting house-accessory mappings...")
    mappings = extract_house_accessory_mappings(manifest)
    print(f"Found {len(mappings)} house-accessory relationships")
    
    # Verify IDs exist
    print("\nVerifying IDs exist in database...")
    valid_mappings, invalid_mappings = verify_ids_exist(supabase, mappings)
    print(f"Valid mappings: {len(valid_mappings)}")
    print(f"Invalid mappings: {len(invalid_mappings)}")
    
    if not valid_mappings:
        print("\nNo valid mappings to process. Exiting.")
        return
    
    # Get existing links
    print("\nChecking for existing links...")
    existing_links = get_current_links(supabase)
    print(f"Found {len(existing_links)} existing links")
    
    # Confirm before proceeding
    new_count = len([m for m in valid_mappings if m not in existing_links])
    print(f"\nReady to create {new_count} new links")
    
    response = input("Proceed with creating links? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled")
        return
    
    # Create links
    stats = create_links(supabase, valid_mappings, existing_links)
    
    # Generate report
    generate_report(stats, len(invalid_mappings))
    
    # Save report to file
    report_filename = f"linking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'invalid_mappings_count': len(invalid_mappings),
            'invalid_mappings': [{'house_id': h, 'accessory_id': a} for h, a in invalid_mappings]
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_filename}")

if __name__ == "__main__":
    main()
