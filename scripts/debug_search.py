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

# Search for "Adobe House" specifically
print("Searching for 'Adobe House' in the index:")
adobe_matches = []
for key, item in products.items():
    name = item.get('name', '')
    if 'adobe' in name.lower():
        adobe_matches.append({
            'key': key,
            'name': name,
            'item_type': item.get('item_type', 'unknown'),
            'description': item.get('description', '')[:100]
        })

if adobe_matches:
    print("Found Adobe-related items:")
    for match in adobe_matches:
        print(f"  Key: {match['key']}")
        print(f"  Name: {match['name']}")
        print(f"  Type: {match['item_type']}")
        print(f"  Description: {match['description']}")
        print()
else:
    print("No Adobe-related items found")

# Let's also try searching for "48 Doughty"
print("\nSearching for '48 Doughty' in the index:")
doughty_matches = []
for key, item in products.items():
    name = item.get('name', '')
    if 'doughty' in name.lower() or '48' in name:
        doughty_matches.append({
            'key': key,
            'name': name,
            'item_type': item.get('item_type', 'unknown')
        })

if doughty_matches:
    print("Found Doughty/48-related items:")
    for match in doughty_matches:
        print(f"  Name: {match['name']}")
        print(f"  Type: {match['item_type']}")
        print()
else:
    print("No Doughty/48-related items found")

# Let's look at a few random items to see the structure
print("\nSample of first 5 items in index:")
sample_items = list(products.items())[:5]
for key, item in sample_items:
    print(f"  Key: {key}")
    print(f"  Name: {item.get('name', 'N/A')}")
    print(f"  Type: {item.get('item_type', 'unknown')}")
    print()