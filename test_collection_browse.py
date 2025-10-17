#!/usr/bin/env python3
"""
Updated prototype scraper that:
1. Browses the North Pole retired collection directly
2. Handles gzip compression properly
3. Finds product listings and extracts data
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://retiredproducts.department56.com"
NORTH_POLE_URL = f"{BASE_URL}/collections/north-pole-series"
OUTPUT_FILE = "scraping_analysis.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def browse_north_pole_collection():
    """Browse the North Pole retired collection to see structure"""
    print("=" * 70)
    print("🔍 BROWSING NORTH POLE RETIRED COLLECTION")
    print("=" * 70)
    print(f"\nURL: {NORTH_POLE_URL}\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
    })
    
    try:
        response = session.get(NORTH_POLE_URL, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📦 Content Encoding: {response.headers.get('Content-Encoding', 'none')}")
        print(f"📏 Content Length: {len(response.content)} bytes\n")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save full HTML for manual inspection
        with open('north_pole_collection.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("💾 Saved full HTML to: north_pole_collection.html\n")
        
        # Try to find product listings
        print("🔎 Looking for product elements...\n")
        
        # Common Shopify selectors
        selectors = [
            'div.product-grid-item',
            'div.product-item',
            'div.grid-product',
            'article.product',
            'div[class*="product"]',
            'a[href*="/products/"]',
        ]
        
        results = {}
        for selector in selectors:
            elements = soup.select(selector)
            results[selector] = len(elements)
            if elements:
                print(f"✅ Found {len(elements)} elements matching: {selector}")
                # Show first match
                if len(elements) > 0:
                    print(f"   Example: {str(elements[0])[:200]}...")
            else:
                print(f"❌ No matches for: {selector}")
        
        print()
        
        # Try to find product links
        product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
        print(f"🔗 Found {len(product_links)} product links\n")
        
        if product_links:
            print("📋 Sample product links:")
            for link in product_links[:10]:
                url = urljoin(BASE_URL, link.get('href'))
                title = link.get_text(strip=True) or link.get('title', 'No title')
                print(f"   • {title[:50]}")
                print(f"     {url}")
        
        # Save analysis
        analysis = {
            'url': NORTH_POLE_URL,
            'status_code': response.status_code,
            'selector_results': results,
            'product_link_count': len(product_links),
            'sample_links': [
                {
                    'title': link.get_text(strip=True) or link.get('title', 'No title'),
                    'url': urljoin(BASE_URL, link.get('href'))
                }
                for link in product_links[:10]
            ]
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Analysis saved to: {OUTPUT_FILE}")
        
        # Now try to scrape a sample product page
        if product_links:
            print("\n" + "=" * 70)
            print("📄 TESTING PRODUCT PAGE SCRAPING")
            print("=" * 70)
            
            sample_url = urljoin(BASE_URL, product_links[0].get('href'))
            scrape_product_page(session, sample_url)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def scrape_product_page(session, url):
    """Scrape a single product page to test data extraction"""
    print(f"\n🔍 Scraping: {url}\n")
    
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save product page HTML
        filename = url.split('/')[-1]
        with open(f'product_page_{filename}.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print(f"💾 Saved product page to: product_page_{filename}.html\n")
        
        # Try to extract product data
        data = {}
        
        # Title
        title_selectors = ['h1.product-title', 'h1[class*="title"]', 'h1']
        for selector in title_selectors:
            title = soup.select_one(selector)
            if title:
                data['title'] = title.get_text(strip=True)
                print(f"📝 Title: {data['title']}")
                break
        
        # Images
        images = soup.find_all('img', class_=lambda x: x and 'product' in x.lower() if x else False)
        if not images:
            images = soup.find_all('img')
        
        data['images'] = []
        for img in images[:5]:
            src = img.get('src') or img.get('data-src')
            if src and 'cdn.shopify' in src:
                full_url = urljoin(BASE_URL, src)
                data['images'].append(full_url)
        
        print(f"🖼️  Images found: {len(data['images'])}")
        for img_url in data['images'][:3]:
            print(f"   • {img_url}")
        
        # Product details
        details_div = soup.find('div', class_=['product-description', 'description', 'rte'])
        if details_div:
            data['description'] = details_div.get_text(strip=True)[:500]
            print(f"\n📄 Description: {data['description'][:200]}...")
        
        # Price
        price = soup.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower() if x else False)
        if price:
            data['price'] = price.get_text(strip=True)
            print(f"💰 Price: {data['price']}")
        
        # SKU
        sku = soup.find(['span', 'div'], class_=lambda x: x and 'sku' in x.lower() if x else False)
        if not sku:
            # Try to find in text
            sku_text = soup.find(string=lambda x: x and 'SKU' in x if x else False)
            if sku_text:
                data['sku'] = sku_text.strip()
                print(f"🏷️  SKU: {data['sku']}")
        
        print("\n" + "=" * 70)
        print("📊 DATA EXTRACTION SUMMARY")
        print("=" * 70)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error scraping product page: {e}")
        import traceback
        traceback.print_exc()

def main():
    browse_north_pole_collection()
    
    print("\n" + "=" * 70)
    print("✅ PROTOTYPE ANALYSIS COMPLETE")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("1. Review north_pole_collection.html to see page structure")
    print("2. Review product_page_*.html to see product detail structure")
    print("3. Update selectors based on actual HTML")
    print("4. Build full scraper with correct data extraction")

if __name__ == "__main__":
    main()
