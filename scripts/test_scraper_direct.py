#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add the scraper directory to path
sys.path.append(str(Path(__file__).parent / "scraper"))

from enhanced_sitemap_scraper import SitemapBasedScraper

def test_scraper_search():
    """Test the actual scraper search functionality"""
    scraper = SitemapBasedScraper()
    
    print("Building indices...")
    scraper.build_indices()
    
    print(f"\nLoaded indices for sites: {list(scraper.indices.keys())}")
    for site, products in scraper.indices.items():
        print(f"  {site}: {len(products)} products")
    
    # Test search
    print("\nTesting search for 'Adobe House':")
    results = scraper.search_multi_source("Adobe House", item_type="house")
    
    print(f"Search results: {results}")
    
    if results:
        print("\nDetailed results:")
        for site, result in results.items():
            print(f"  {site}: {result['product'].name} (score: {result['score']})")
    else:
        print("No results found")

if __name__ == "__main__":
    test_scraper_search()