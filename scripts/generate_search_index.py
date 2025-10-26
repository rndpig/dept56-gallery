#!/usr/bin/env python3
"""
Generate a searchable JSON index from the scraped product data for client-side searching
"""

import json
import os
import sys
from pathlib import Path

# Add the scraper directory to path
sys.path.append(str(Path(__file__).parent / "scraper"))

def generate_search_index():
    """Generate a client-side searchable index"""
    
    # Load the product index from scraper
    scraper_dir = Path(__file__).parent / "scraper"
    index_file = scraper_dir / "product_index.json"
    
    if not index_file.exists():
        print(f"Error: {index_file} not found")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('index', data)
    
    # Create simplified search index for houses
    search_index = []
    
    for url, product in products.items():
        name = product.get('name', '')
        item_type = product.get('item_type', 'unknown')
        
        # Filter for likely houses (same logic as before)
        if (item_type == 'house' or 
            any(house_word in name.lower() for house_word in [
                'house', 'home', 'cottage', 'manor', 'palace', 'castle', 
                'inn', 'shop', 'store', 'church', 'school', 'mill', 'barn', 
                'station', 'hall', 'tower', 'factory', 'warehouse', 'clinic'
            ]) and
            not any(acc_word in name.lower() for acc_word in [
                'accessory', 'set of', 'ornament', 'figurine', 'tree', 
                'fence', 'lamp', 'sign', 'bench'
            ])):
            
            search_item = {
                'name': name,
                'year': product.get('intro_year'),
                'description': product.get('description', ''),
                'sku': product.get('item_number', ''),
                'collection': product.get('discovered_collection', ''),
                'photo_url': product.get('primary_image_url', ''),
                'url': url,
                'search_terms': name.lower()  # For client-side fuzzy search
            }
            search_index.append(search_item)
    
    # Sort by name for easier searching
    search_index.sort(key=lambda x: x['name'])
    
    # Save to public directory so it can be loaded by the client
    output_file = Path(__file__).parent.parent / "public" / "house_search_index.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': '2025-10-25',
            'total_houses': len(search_index),
            'houses': search_index
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated search index with {len(search_index)} houses")
    print(f"📁 Saved to: {output_file}")
    
    # Show sample entries
    print("\n🏠 Sample houses in index:")
    for i, house in enumerate(search_index[:5]):
        print(f"  {i+1}. {house['name']} ({house['year']})")

if __name__ == "__main__":
    generate_search_index()