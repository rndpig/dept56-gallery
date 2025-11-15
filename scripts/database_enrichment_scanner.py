#!/usr/bin/env python3
"""
Database Enrichment Scanner
Scans existing database items against scraped data to identify data enrichment opportunities
"""

import json
import sys
import os
from pathlib import Path

# Add the scraper directory to path
sys.path.append(str(Path(__file__).parent / "scraper"))

try:
    from rapidfuzz import fuzz
except ImportError:
    print("Warning: rapidfuzz not available, using simple string matching")
    fuzz = None

def load_search_index():
    """Load the search index"""
    index_path = Path(__file__).parent.parent / "public" / "house_search_index.json"
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_match_score(db_name, scraped_name):
    """Calculate fuzzy match score between database and scraped names"""
    if fuzz:
        return fuzz.token_sort_ratio(db_name.lower(), scraped_name.lower())
    else:
        # Simple fallback matching
        db_lower = db_name.lower()
        scraped_lower = scraped_name.lower()
        if db_lower == scraped_lower:
            return 100
        elif db_lower in scraped_lower or scraped_lower in db_lower:
            return 80
        else:
            return 0

def find_enrichment_opportunities(db_items, search_index):
    """
    Find enrichment opportunities for database items
    
    Args:
        db_items: List of items from database with structure: [{'name': str, 'id': str, 'sku': str, ...}]
        search_index: Loaded search index data
        
    Returns:
        List of enrichment opportunities
    """
    opportunities = []
    scraped_houses = search_index['houses']
    
    for db_item in db_items:
        db_name = db_item.get('name', '')
        db_sku = db_item.get('sku', '')
        
        # Find potential matches in scraped data
        best_match = None
        best_score = 0
        
        for scraped_item in scraped_houses:
            # Try name matching
            name_score = calculate_match_score(db_name, scraped_item['name'])
            
            # Try SKU matching if both have SKUs
            sku_score = 0
            if db_sku and scraped_item.get('sku'):
                sku_score = calculate_match_score(db_sku, scraped_item['sku'])
            
            # Use the better score
            match_score = max(name_score, sku_score)
            
            if match_score > best_score and match_score >= 70:  # Minimum confidence threshold
                best_score = match_score
                best_match = scraped_item
        
        if best_match:
            # Analyze what data could be enriched
            enrichments = []
            
            # Check for missing/different data
            if not db_item.get('year') and best_match.get('intro_year'):
                enrichments.append({
                    'field': 'introduction_year',
                    'current': db_item.get('year'),
                    'suggested': best_match.get('intro_year'),
                    'type': 'missing'
                })
            
            if not db_item.get('retired_year') and best_match.get('retired_year'):
                enrichments.append({
                    'field': 'retired_year', 
                    'current': None,
                    'suggested': best_match.get('retired_year'),
                    'type': 'missing'
                })
            
            if not db_item.get('sku') and best_match.get('sku'):
                enrichments.append({
                    'field': 'sku',
                    'current': db_item.get('sku'),
                    'suggested': best_match.get('sku'),
                    'type': 'missing'
                })
            
            if not db_item.get('description') and best_match.get('description'):
                enrichments.append({
                    'field': 'description',
                    'current': db_item.get('description'),
                    'suggested': best_match.get('description'),
                    'type': 'missing'
                })
            
            if not db_item.get('photo_url') and best_match.get('photo_url'):
                enrichments.append({
                    'field': 'primary_image',
                    'current': db_item.get('photo_url'),
                    'suggested': best_match.get('photo_url'),
                    'type': 'missing'
                })
            
            if not db_item.get('collection') and best_match.get('collection'):
                enrichments.append({
                    'field': 'collection',
                    'current': db_item.get('collection'),
                    'suggested': best_match.get('collection'),
                    'type': 'missing'
                })
            
            # Check for additional images
            if best_match.get('images') and len(best_match['images']) > 1:
                enrichments.append({
                    'field': 'additional_images',
                    'current': 'Single image' if db_item.get('photo_url') else 'No images',
                    'suggested': f"{len(best_match['images'])} high-quality images available",
                    'type': 'enhancement',
                    'images': best_match['images']
                })
            
            # Check for pricing data
            if best_match.get('srp') and not db_item.get('price'):
                enrichments.append({
                    'field': 'retail_price',
                    'current': db_item.get('price'),
                    'suggested': f"${best_match.get('srp')}",
                    'type': 'missing'
                })
            
            if enrichments:
                opportunities.append({
                    'db_item': db_item,
                    'matched_item': best_match,
                    'match_score': best_score,
                    'match_type': 'sku' if db_sku and scraped_item.get('sku') else 'name',
                    'enrichments': enrichments,
                    'priority': 'high' if best_score >= 90 else 'medium' if best_score >= 80 else 'low'
                })
    
    return opportunities

def main():
    """Main entry point for CLI usage"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python database_enrichment_scanner.py <database_items_json>",
            "success": False
        }))
        return
    
    try:
        # Read database items from stdin or file
        if sys.argv[1] == '-':
            input_data = sys.stdin.read()
        else:
            with open(sys.argv[1], 'r') as f:
                input_data = f.read()
        
        db_items = json.loads(input_data)
        
        # Load search index
        search_index = load_search_index()
        
        # Find enrichment opportunities
        opportunities = find_enrichment_opportunities(db_items, search_index)
        
        # Output results
        result = {
            "success": True,
            "total_items_scanned": len(db_items),
            "opportunities_found": len(opportunities),
            "high_priority": len([o for o in opportunities if o['priority'] == 'high']),
            "medium_priority": len([o for o in opportunities if o['priority'] == 'medium']),
            "low_priority": len([o for o in opportunities if o['priority'] == 'low']),
            "opportunities": opportunities,
            "generated_at": "2025-10-25",
            "search_index_houses": len(search_index['houses'])
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "error": f"Error processing enrichment scan: {str(e)}",
            "success": False
        }))

if __name__ == "__main__":
    main()