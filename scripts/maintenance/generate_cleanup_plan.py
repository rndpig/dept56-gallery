import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import sys

def load_duplicate_analysis(filename: str) -> dict:
    """Load the duplicate analysis from file."""
    with open(filename, 'r') as f:
        data = json.load(f)
        return data.get('duplicates', {})

def select_primary_record(duplicates: List[dict]) -> Tuple[dict, List[dict]]:
    """Select the best record to keep from a group of duplicates."""
    # Sort duplicates by criteria
    sorted_dupes = sorted(duplicates, key=lambda x: (
        1 if x.get('photo_url') else 0,  # Prefer records with photos
        1 if x.get('year') else 0,       # Prefer records with years
        x.get('updated_at', ''),         # Prefer more recent updates
        x.get('id', '')                  # Use ID for stable sorting
    ), reverse=True)
    
    return sorted_dupes[0], sorted_dupes[1:]

def process_duplicates(analysis_file: str) -> Dict[str, dict]:
    """
    Process the duplicate analysis file and generate cleanup recommendations.
    Returns a dict containing the cleanup plan.
    """
    duplicates = load_duplicate_analysis(analysis_file)
    
    cleanup_plan = {
        'primary_records': {},
        'records_to_delete': [],
        'by_group': {}
    }
    
    # Process each group of duplicates
    for name, group in duplicates.items():
        primary, to_delete = select_primary_record(group)
        
        # Add to cleanup plan
        cleanup_plan['primary_records'][name] = primary
        cleanup_plan['records_to_delete'].extend(d['id'] for d in to_delete)
        cleanup_plan['by_group'][name] = {
            'primary': primary['id'],
            'to_delete': [d['id'] for d in to_delete]
        }
    
    return cleanup_plan

def save_cleanup_plan(plan: dict, timestamp: str):
    """Save the cleanup plan to a file."""
    output = {
        'timestamp': timestamp,
        'total_groups': len(plan['by_group']),
        'total_duplicates': len(plan['records_to_delete']),
        'cleanup_plan': plan
    }
    
    filename = f'cleanup_plan_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    return filename

def print_cleanup_summary(plan: dict):
    """Print a detailed summary of the cleanup plan."""
    print("\nCleanup Plan Summary:")
    print(f"Total duplicate groups: {len(plan['by_group'])}")
    print(f"Total records to remove: {len(plan['records_to_delete'])}")
    
    print("\nBy Group:")
    for name, group in plan['by_group'].items():
        primary = plan['primary_records'][name]
        print(f"\n{name}:")
        print(f"  Keeping: {primary['id']}")
        print(f"    Year: {primary.get('year', 'None')}")
        print(f"    Has photo: {'Yes' if primary.get('photo_url') else 'No'}")
        print(f"    Last updated: {primary.get('updated_at', 'Unknown')}")
        print(f"  Removing: {len(group['to_delete'])} duplicate(s)")
        for id in group['to_delete']:
            print(f"    - {id}")

def main():
    """Main execution function."""
    # Check if analysis file was provided
    if len(sys.argv) < 2:
        print("Please provide the path to the duplicate analysis JSON file")
        print("Usage: python cleanup_plan.py <analysis_file>")
        sys.exit(1)
    
    analysis_file = sys.argv[1]
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file '{analysis_file}' not found")
        sys.exit(1)
    
    # Process duplicates
    print(f"Processing duplicate analysis from {analysis_file}...")
    cleanup_plan = process_duplicates(analysis_file)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save cleanup plan
    plan_file = save_cleanup_plan(cleanup_plan, timestamp)
    
    # Print summary
    print_cleanup_summary(cleanup_plan)
    print(f"\nDetailed plan saved to: {plan_file}")
    
    print("\nNext steps:")
    print("1. Review the cleanup plan in the generated JSON file")
    print("2. Execute the changes using the Supabase dashboard or API")
    print("3. Verify the changes after execution")

if __name__ == "__main__":
    main()