#!/usr/bin/env python3
"""
Prototype Web Scraper for Department 56 Retired Products
Tests scraping feasibility with a small sample of houses from the database.

This script will:
1. Pull 10 sample houses from Supabase
2. Search for them on retiredproducts.department56.com
3. Extract available metadata (images, descriptions, dates, prices)
4. Generate a report on data quality and feasibility
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

# Configuration
SAMPLE_SIZE = 10
BASE_URL = "https://retiredproducts.department56.com"
SEARCH_URL = f"{BASE_URL}/search"
OUTPUT_FILE = "scraping_prototype_results.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class Dept56Scraper:
    def __init__(self):
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase = create_client(supabase_url, service_role_key)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        self.results = []
        
    def get_sample_houses(self):
        """Retrieve a sample of houses from Supabase"""
        print(f"📥 Fetching {SAMPLE_SIZE} sample houses from database...")
        
        # Get houses with year information (better chance of finding them)
        response = self.supabase.table("houses") \
            .select("id, name, year, notes") \
            .not_.is_("year", "null") \
            .limit(SAMPLE_SIZE) \
            .execute()
        
        houses = response.data
        print(f"✅ Retrieved {len(houses)} houses")
        return houses
    
    def search_product(self, house_name, year=None):
        """Search for a product on the Department 56 retired products site"""
        # Try searching with just the name first
        search_term = house_name.strip()
        
        print(f"\n🔍 Searching for: {search_term}")
        
        try:
            # Build search URL
            url = f"{SEARCH_URL}?q={quote_plus(search_term)}&type=product"
            
            print(f"   URL: {url}")
            
            # Make request
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product results
            # This is a guess - we'll need to inspect the actual HTML structure
            products = soup.find_all('div', class_=['product-item', 'product-card', 'grid-product'])
            
            if not products:
                # Try alternative selectors
                products = soup.find_all('article', class_=['product', 'item'])
            
            if not products:
                # Try even more generic
                products = soup.find_all('a', href=lambda x: x and '/products/' in x)
            
            print(f"   Found {len(products)} potential products")
            
            # Save raw HTML for inspection
            with open(f"scraping_debug_{house_name[:20].replace(' ', '_')}.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            return {
                'url': url,
                'status_code': response.status_code,
                'product_count': len(products),
                'html_snippet': str(soup)[:500]
            }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                'url': url if 'url' in locals() else None,
                'error': str(e)
            }
    
    def scrape_product_page(self, product_url):
        """Scrape detailed information from a product page"""
        print(f"   📄 Scraping product page: {product_url}")
        
        try:
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data (these are educated guesses - need to inspect actual pages)
            data = {
                'url': product_url,
                'title': None,
                'sku': None,
                'description': None,
                'price': None,
                'intro_year': None,
                'retired_year': None,
                'images': [],
                'dimensions': None
            }
            
            # Try to find title
            title_elem = soup.find('h1', class_=['product-title', 'product-name', 'title'])
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
            
            # Try to find images
            img_elements = soup.find_all('img', class_=['product-image', 'main-image'])
            for img in img_elements[:5]:  # Limit to 5 images
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    data['images'].append(urljoin(BASE_URL, img_url))
            
            # Try to find product details
            details = soup.find('div', class_=['product-details', 'product-info'])
            if details:
                data['description'] = details.get_text(strip=True)[:500]
            
            return data
            
        except Exception as e:
            print(f"   ❌ Error scraping product page: {e}")
            return {'error': str(e)}
    
    def run_prototype(self):
        """Run the prototype scraping test"""
        print("=" * 70)
        print("🧪 DEPARTMENT 56 SCRAPER - PROTOTYPE TEST")
        print("=" * 70)
        print()
        
        # Get sample houses
        houses = self.get_sample_houses()
        
        # Test scraping each one
        for i, house in enumerate(houses, 1):
            print(f"\n[{i}/{len(houses)}] Testing: {house['name']}")
            
            result = {
                'database_id': house['id'],
                'database_name': house['name'],
                'database_year': house['year'],
                'search_results': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Search for the product
            search_results = self.search_product(house['name'], house['year'])
            result['search_results'] = search_results
            
            self.results.append(result)
            
            # Be respectful - wait between requests
            time.sleep(2)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
    
    def print_summary(self):
        """Print a summary of findings"""
        print("\n" + "=" * 70)
        print("📊 PROTOTYPE TEST SUMMARY")
        print("=" * 70)
        
        successful = sum(1 for r in self.results if 'error' not in r.get('search_results', {}))
        failed = len(self.results) - successful
        
        print(f"\n✅ Successful searches: {successful}/{len(self.results)}")
        print(f"❌ Failed searches: {failed}/{len(self.results)}")
        
        # Check how many found products
        found_products = sum(1 for r in self.results 
                           if r.get('search_results', {}).get('product_count', 0) > 0)
        
        print(f"🎯 Searches that found products: {found_products}/{len(self.results)}")
        
        print("\n" + "=" * 70)
        print("📝 NEXT STEPS:")
        print("=" * 70)
        print("\n1. Review the saved HTML files (scraping_debug_*.html)")
        print("2. Inspect the actual HTML structure to identify correct selectors")
        print("3. Update the scraper with correct CSS selectors")
        print("4. Re-run prototype to validate data extraction")
        print("\n" + "=" * 70)

def main():
    scraper = Dept56Scraper()
    scraper.run_prototype()

if __name__ == "__main__":
    main()
