#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

# Add the scraper directory to path
sys.path.append(str(Path(__file__).parent / "scraper"))

from rapidfuzz import fuzz

# Change to scraper directory
os.chdir('scripts/scraper')

# Load the product index
with open('product_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all products
products = data.get('index', data)

def test_fuzzy_search(search_term, min_score=60):
    """Test fuzzy search like the scraper does"""
    print(f"Testing fuzzy search for: '{search_term}'")
    print(f"Minimum score threshold: {min_score}")
    print("-" * 50)
    
    matches = []
    for url, product in products.items():
        product_name = product.get('name', '')
        score = fuzz.token_sort_ratio(search_term.lower(), product_name.lower())
        
        if score >= min_score:
            matches.append({
                'name': product_name,
                'score': score,
                'url': url
            })
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    if matches:
        print(f"Found {len(matches)} matches:")
        for i, match in enumerate(matches[:10]):  # Show top 10
            print(f"{i+1:2}. {match['name']} (score: {match['score']})")
    else:
        print("No matches found above threshold")
    
    return matches

# Test with the houses we know exist
test_houses = ["Adobe House", "48 Doughty St Home", "Buckingham Palace"]

for house in test_houses:
    matches = test_fuzzy_search(house)
    print(f"\nBest match for '{house}': {matches[0]['name'] if matches else 'None'}")
    print("=" * 70)
    print()