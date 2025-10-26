#!/usr/bin/env python3
"""
Bulk Import Scraper for Department 56 Gallery
Processes multiple house names and returns structured results for the import workflow
"""

import sys
import json
import time
import asyncio
from pathlib import Path

# Add the scraper directory to path
sys.path.append(str(Path(__file__).parent / "scraper"))

try:
    from enhanced_sitemap_scraper import SitemapBasedScraper
except ImportError as e:
    print(json.dumps({
        "error": f"Failed to import scraper: {e}",
        "success": False
    }))
    sys.exit(1)

def bulk_search_houses(house_names: list) -> dict:
    """
    Search for multiple house names and return structured results
    
    Args:
        house_names: List of house names to search for
        
    Returns:
        Dict with search results
    """
    scraper = SitemapBasedScraper()
    
    # Load indices for all sites
    print("Loading product indices...")
    scraper.build_indices()
    
    results = []
    
    for house_name in house_names:
        print(f"Searching for: {house_name}")
        
        # Search across all sources
        search_result = scraper.search_multi_source(house_name, item_type="house")
        
        # Find the best match across all sources
        best_match = None
        best_confidence = 0
        best_source = None
        
        for source, result in search_result.items():
            if result and isinstance(result, dict):
                # Each result is a dict with 'product', 'score', 'url'
                confidence = result.get('score', 0) / 100.0  # Convert score to confidence 0-1
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = result
                    best_source = source
        
        # Structure the result
        if best_match and best_confidence > 0.5:  # Minimum confidence threshold
            product = best_match['product']  # Extract the ProductData object
            result = {
                "input_name": house_name,
                "status": "found",
                "confidence": best_confidence,
                "source": best_source,
                "scraped_data": {
                    "name": product.name,
                    "year": product.intro_year,
                    "description": product.description,
                    "sku": product.item_number,
                    "collection": product.discovered_collection,
                    "photo_url": product.primary_image_url,
                    "url": product.source_url
                }
            }
        else:
            result = {
                "input_name": house_name,
                "status": "not_found",
                "confidence": best_confidence,
                "source": None,
                "scraped_data": None
            }
        
        results.append(result)
    
    return {
        "success": True,
        "results": results,
        "total_searched": len(house_names),
        "found_count": len([r for r in results if r["status"] == "found"]),
        "timestamp": time.time()
    }

def main():
    """
    Main entry point - reads house names from stdin (JSON) and outputs results
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            print(json.dumps({
                "error": "No input provided",
                "success": False
            }))
            return
        
        # Parse JSON input
        try:
            data = json.loads(input_data)
            house_names = data.get("house_names", [])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error": f"Invalid JSON input: {e}",
                "success": False
            }))
            return
        
        if not house_names:
            print(json.dumps({
                "error": "No house names provided",
                "success": False
            }))
            return
        
        # Process the search
        results = bulk_search_houses(house_names)
        
        # Output results as JSON
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "success": False
        }))

if __name__ == "__main__":
    main()