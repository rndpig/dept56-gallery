#!/usr/bin/env python3
import json
import os

# Change to scraper directory
os.chdir('scripts/scraper')

# Load the product index
with open('product_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all products
products = data.get('index', data)

# Filter for items that are likely houses (not accessories)
house_candidates = []
for item in products.values():
    name = item.get('name', '').lower()
    item_type = item.get('item_type', '').lower()
    
    # Look for items that are likely houses
    if (item_type == 'house' or 
        any(house_word in name for house_word in ['house', 'home', 'cottage', 'manor', 'palace', 'castle', 'inn', 'shop', 'store', 'church', 'school', 'mill', 'barn', 'station']) and
        not any(acc_word in name for acc_word in ['accessory', 'set of', 'ornament', 'figurine', 'tree', 'fence'])):
        house_candidates.append({
            'name': item.get('name'),
            'year': item.get('year'),
            'collection': item.get('collection', ''),
            'sku': item.get('item_number', ''),
            'description': item.get('description', '')[:100] + '...' if len(item.get('description', '')) > 100 else item.get('description', '')
        })

# Sort by name and show first 20
house_candidates.sort(key=lambda x: x['name'])

print("Sample house titles from scraped data:")
print("=" * 50)
for i, house in enumerate(house_candidates[:20]):
    print(f"{i+1:2}. {house['name']}")
    if house['year']:
        print(f"    Year: {house['year']}")
    if house['collection']:
        print(f"    Collection: {house['collection']}")
    if house['sku']:
        print(f"    SKU: {house['sku']}")
    print()

print(f"\nTotal house candidates found in scraped data: {len(house_candidates)}")