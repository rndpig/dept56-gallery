#!/usr/bin/env python3
"""
Analyze the scraped data to identify accessories and their potential house relationships
"""

import json
import os

# Change to scraper directory
os.chdir('scripts/scraper')

# Load the product index
with open('product_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all products
products = data.get('index', data)

# Categorize items
houses = []
accessories = []
other = []

for url, product in products.items():
    name = product.get('name', '').lower()
    
    # Check if it's likely a house
    if any(house_word in name for house_word in [
        'house', 'home', 'cottage', 'manor', 'palace', 'castle', 
        'inn', 'shop', 'store', 'church', 'school', 'mill', 'barn', 
        'station', 'hall', 'tower', 'factory', 'warehouse', 'clinic'
    ]) and not any(acc_word in name for acc_word in [
        'accessory', 'set of', 'ornament', 'figurine', 'tree', 'fence'
    ]):
        houses.append({
            'name': product.get('name'),
            'series': product.get('series', ''),
            'url': url
        })
    
    # Check if it's likely an accessory
    elif any(acc_word in name for acc_word in [
        'tree', 'fence', 'lamp', 'sign', 'bench', 'accessory', 
        'figurine', 'set of', 'ornament', 'decoration', 'light',
        'person', 'people', 'car', 'truck', 'vehicle'
    ]) or any(type_word in name for type_word in [
        'st/', 'set/', 'pkg/', 'assorted'
    ]):
        accessories.append({
            'name': product.get('name'),
            'series': product.get('series', ''),
            'url': url
        })
    else:
        other.append({
            'name': product.get('name'),
            'series': product.get('series', ''),
            'url': url
        })

print("ANALYSIS OF SCRAPED DATA:")
print("=" * 50)
print(f"Houses: {len(houses)}")
print(f"Accessories: {len(accessories)}")
print(f"Other/Unclear: {len(other)}")

print("\nSAMPLE ACCESSORIES:")
for i, acc in enumerate(accessories[:10]):
    print(f"{i+1:2}. {acc['name']} ({acc['series']})")

print("\nSAMPLE HOUSES:")
for i, house in enumerate(houses[:10]):
    print(f"{i+1:2}. {house['name']} ({house['series']})")

# Look for potential relationships (same series)
series_groups = {}
for item in houses + accessories:
    series = item['series']
    if series:
        if series not in series_groups:
            series_groups[series] = {'houses': [], 'accessories': []}
        
        if item in houses:
            series_groups[series]['houses'].append(item['name'])
        else:
            series_groups[series]['accessories'].append(item['name'])

print(f"\nSERIES WITH BOTH HOUSES AND ACCESSORIES:")
for series, items in series_groups.items():
    if len(items['houses']) > 0 and len(items['accessories']) > 0:
        print(f"\n{series}:")
        print(f"  Houses ({len(items['houses'])}): {', '.join(items['houses'][:3])}{'...' if len(items['houses']) > 3 else ''}")
        print(f"  Accessories ({len(items['accessories'])}): {', '.join(items['accessories'][:3])}{'...' if len(items['accessories']) > 3 else ''}")