"""
Analyze photo issues in the database
"""
import os
from collections import defaultdict
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use service role key for admin operations
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def analyze_photo_issues():
    """Find and report on photo issues in the database"""
    print("\n🔍 Analyzing database for photo issues...")
    
    # Get all houses
    print("\nChecking houses...")
    houses = supabase.table('houses').select('*').execute()
    total_houses = len(houses.data)
    missing_photos = [h for h in houses.data if not h.get('photo_url')]
    has_photos = [h for h in houses.data if h.get('photo_url')]
    
    print(f"Total houses: {total_houses}")
    print(f"Houses with photos: {len(has_photos)}")
    print(f"Houses missing photos: {len(missing_photos)}")
    
    if missing_photos:
        print("\nFirst 10 houses missing photos:")
        for h in missing_photos[:10]:
            print(f"- {h['name']} (Year: {h.get('year', 'Unknown')})")
    
    # Get all accessories
    print("\nChecking accessories...")
    accessories = supabase.table('accessories').select('*').execute()
    total_accessories = len(accessories.data)
    missing_acc_photos = [a for a in accessories.data if not a.get('photo_url')]
    has_acc_photos = [a for a in accessories.data if a.get('photo_url')]
    
    print(f"Total accessories: {total_accessories}")
    print(f"Accessories with photos: {len(has_acc_photos)}")
    print(f"Accessories missing photos: {len(missing_acc_photos)}")
    
    if missing_acc_photos:
        print("\nFirst 10 accessories missing photos:")
        for a in missing_acc_photos[:10]:
            print(f"- {a['name']} (Year: {a.get('year', 'Unknown')})")
    
    # Check photo URLs
    print("\nAnalyzing photo URLs...")
    
    # Group houses by URL pattern
    url_patterns = defaultdict(list)
    for h in has_photos:
        url = h['photo_url']
        # Get the part after /ingestion/
        pattern = url.split('/ingestion/')[-1].split('_')[0] if '/ingestion/' in url else 'other'
        url_patterns[pattern].append(h['name'])
    
    print("\nPhoto URL patterns found:")
    for pattern, items in url_patterns.items():
        print(f"\nPattern: {pattern}")
        print(f"Count: {len(items)}")
        print("Examples:")
        for name in items[:3]:
            print(f"- {name}")

    # Final summary
    print("\n📊 Summary:")
    print(f"Total items: {total_houses + total_accessories}")
    print(f"Items with photos: {len(has_photos) + len(has_acc_photos)}")
    print(f"Items missing photos: {len(missing_photos) + len(missing_acc_photos)}")
    
    return {
        'houses': houses.data,
        'accessories': accessories.data,
        'missing_photos': missing_photos,
        'missing_acc_photos': missing_acc_photos,
        'url_patterns': url_patterns
    }

if __name__ == '__main__':
    analyze_photo_issues()