import json
import os
from datetime import datetime
from supabase import create_client, Client
from typing import Dict, List, Optional
import sys

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL", "https://xctottgirqkkmjmutoon.supabase.co")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)

def find_duplicates() -> Dict[str, List[dict]]:
    """Find all duplicate houses in the database."""
    # Get all houses
    response = supabase.table('houses').select('*').execute()
    houses = response.data
    
    # Group by name
    by_name: Dict[str, List[dict]] = {}
    for house in houses:
        name = house.get('name', '').strip()
        if name:
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(house)
    
    # Filter for duplicates
    duplicates: Dict[str, List[dict]] = {
        name: group for name, group in by_name.items() if len(group) > 1
    }
    
    return duplicates

def analyze_duplicates(duplicates: Dict[str, List[dict]]) -> dict:
    """Analyze duplicate entries and generate a report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_houses': 0,
        'duplicate_groups': len(duplicates),
        'total_duplicates': sum(len(group) - 1 for group in duplicates.values()),
        'duplicates': {}
    }
    
    # Add duplicate details
    for name, group in duplicates.items():
        report['duplicates'][name] = [
            {
                'id': house['id'],
                'name': house['name'],
                'year': house.get('year'),
                'photo_url': house.get('photo_url'),
                'updated_at': house.get('updated_at')
            }
            for house in group
        ]
    
    return report

def save_report(report: dict) -> str:
    """Save the analysis report to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'duplicate_analysis_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filename

def print_report(report: dict) -> None:
    """Print a summary of the duplicate analysis."""
    print("\nDuplicate Analysis Summary:")
    print(f"Total duplicate groups: {report['duplicate_groups']}")
    print(f"Total duplicate records: {report['total_duplicates']}")
    
    print("\nDuplicate Groups:")
    for name, duplicates in report['duplicates'].items():
        print(f"\n{name}:")
        for house in duplicates:
            print(f"  • ID: {house['id']}")
            print(f"    Year: {house.get('year')}")
            print(f"    Has photo: {'Yes' if house.get('photo_url') else 'No'}")
            if house.get('photo_url'):
                print(f"    Photo URL: {house['photo_url']}")
            print(f"    Last updated: {house.get('updated_at')}")

def main():
    """Main execution function."""
    print("Analyzing database for duplicates...")
    
    try:
        # Find duplicates
        duplicates = find_duplicates()
        
        # Analyze and generate report
        report = analyze_duplicates(duplicates)
        
        # Save report
        filename = save_report(report)
        print(f"\nDetailed analysis saved to: {filename}")
        
        # Print summary
        print_report(report)
        
        return report, filename
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    _, output_file = main()
    # Print the output filename for the next script
    print(f"\nOUTPUT_FILE={output_file}")
    sys.exit(0)