#!/usr/bin/env python3
import json
import os

# Change to scraper directory
os.chdir('scraper')

# Load the product index
with open('product_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get sample products
products = data.get('index', data)
sample = list(products.values())[:10]

print("Sample products from index:")
for item in sample:
    name = item.get('name', 'N/A')
    print(f"- {name}")

print(f"\nTotal products in index: {len(products)}")

# Test search for "PEZ" related items
pez_items = [item for item in products.values() if 'pez' in item.get('name', '').lower()]
print(f"\nPEZ-related items found: {len(pez_items)}")
for item in pez_items[:5]:
    print(f"- {item.get('name', 'N/A')}")

# Test search for "Imperial" related items  
imperial_items = [item for item in products.values() if 'imperial' in item.get('name', '').lower()]
print(f"\nImperial-related items found: {len(imperial_items)}")
for item in imperial_items[:5]:
    print(f"- {item.get('name', 'N/A')}")

# Test search for "Palace" related items
palace_items = [item for item in products.values() if 'palace' in item.get('name', '').lower()]
print(f"\nPalace-related items found: {len(palace_items)}")
for item in palace_items[:5]:
    print(f"- {item.get('name', 'N/A')}")