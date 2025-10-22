"""
Index Builder for Department 56 Web Scraper
Crawls both sites and builds a local searchable index of products
"""

import os
import json
import time
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

# Configuration
DEPT56_MAIN_URL = "https://www.department56.com"
DEPT56_RETIRED_URL = "https://retiredproducts.department56.com"
CACHE_FILE = "product_index.json"
MAX_PAGES_PER_COLLECTION = 50  # Safety limit
REQUEST_DELAY = 0.75  # 750ms between requests (1.3 req/sec)

# User agent to identify ourselves
USER_AGENT = "Department56GalleryBot/1.0 (Educational/Personal Collection Management; +mailto:rndpig@gmail.com)"


class IndexBuilder:
    """Builds a local searchable index of Department 56 products"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.session = self._create_session()
        self.index = {}
        self.stats = {
            'total_products': 0,
            'from_retired_site': 0,
            'from_main_site': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat()
        }
        
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic and rate limiting"""
        session = requests.Session()
        
        # Retry strategy: 3 retries with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def load_cached_index(self) -> bool:
        """Load index from cache file if available"""
        if not self.use_cache or not os.path.exists(CACHE_FILE):
            return False
        
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.index = data.get('index', {})
                self.stats = data.get('stats', self.stats)
                print(f"✅ Loaded cached index: {len(self.index)} products")
                print(f"   Cache created: {self.stats.get('started_at', 'unknown')}")
                return True
        except Exception as e:
            print(f"⚠️  Failed to load cache: {e}")
            return False
    
    def save_index(self):
        """Save index to cache file"""
        try:
            self.stats['completed_at'] = datetime.now().isoformat()
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'index': self.index,
                    'stats': self.stats
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved index to {CACHE_FILE}")
        except Exception as e:
            print(f"⚠️  Failed to save index: {e}")
    
    def build_index(self, crawl_main: bool = True, crawl_retired: bool = True):
        """
        Build complete product index from both sites
        
        Args:
            crawl_main: Whether to crawl department56.com
            crawl_retired: Whether to crawl retiredproducts.department56.com
        """
        print("=" * 70)
        print("🏗️  Building Department 56 Product Index")
        print("=" * 70)
        
        # Try loading cache first
        if self.load_cached_index():
            print("\n✅ Using cached index (use use_cache=False to rebuild)")
            return self.index
        
        # Crawl retired products site (easier and more complete)
        if crawl_retired:
            print("\n📦 Crawling retired products site...")
            self._crawl_retired_collections()
        
        # Crawl main site via sitemap
        if crawl_main:
            print("\n🏪 Crawling main site via sitemap...")
            self._crawl_main_sitemap()
        
        # Save the index
        self.save_index()
        
        # Print stats
        print("\n" + "=" * 70)
        print("✅ Index Building Complete")
        print(f"   Total products: {self.stats['total_products']}")
        print(f"   From retired site: {self.stats['from_retired_site']}")
        print(f"   From main site: {self.stats['from_main_site']}")
        print(f"   Errors: {self.stats['errors']}")
        print("=" * 70)
        
        return self.index
    
    def _crawl_retired_collections(self):
        """Crawl retiredproducts.department56.com by collection"""
        # All Department 56 collections/series
        collections = [
            'north-pole-series',
            'dickens-village',
            'original-snow-village',
            'new-england-village',
            'alpine-village',
            'christmas-in-the-city',
            'little-town-of-bethlehem',
            # 'accessories',  # Comment out accessories for now (too many)
            # 'figurines',    # Comment out figurines for now (too many)
        ]
        
        for collection in collections:
            print(f"\n  📚 Collection: {collection}")
            self._crawl_collection_pages(collection)
    
    def _crawl_collection_pages(self, collection: str):
        """Crawl all pages of a collection with pagination"""
        page = 1
        products_found = 0
        
        while page <= MAX_PAGES_PER_COLLECTION:
            url = f"{DEPT56_RETIRED_URL}/collections/{collection}?page={page}"
            
            try:
                # Rate limiting
                time.sleep(REQUEST_DELAY)
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Find all product links on the page
                product_links = soup.select('a.productitem--image-link, a[href*="/products/"]')
                
                if not product_links:
                    print(f"    Page {page}: No more products found")
                    break
                
                page_count = 0
                for link in product_links:
                    href = link.get('href')
                    if href and '/products/' in href:
                        product_url = urljoin(DEPT56_RETIRED_URL, href)
                        
                        # Avoid duplicates
                        if product_url not in self.index:
                            product_data = self._fetch_product_page(product_url, 'dept56_retired')
                            if product_data:
                                self.index[product_url] = product_data
                                products_found += 1
                                page_count += 1
                                self.stats['from_retired_site'] += 1
                                self.stats['total_products'] += 1
                
                print(f"    Page {page}: Found {page_count} products (total: {products_found})")
                
                # Check if there's a next page
                next_button = soup.select_one('a[rel="next"], a.pagination--next')
                if not next_button:
                    break
                
                page += 1
                
            except requests.RequestException as e:
                print(f"    ⚠️  Error on page {page}: {e}")
                self.stats['errors'] += 1
                break
    
    def _crawl_main_sitemap(self):
        """Crawl department56.com via sitemap.xml"""
        sitemap_url = f"{DEPT56_MAIN_URL}/sitemap.xml"
        
        try:
            print(f"  📋 Fetching sitemap: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML sitemap
            root = ET.fromstring(response.content)
            
            # Find all product URLs
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = root.findall('.//ns:url/ns:loc', namespace)
            
            product_urls = [url.text for url in urls if '/products/' in url.text]
            
            print(f"  Found {len(product_urls)} product URLs in sitemap")
            
            # Crawl each product
            for i, url in enumerate(product_urls[:100]):  # Limit to first 100 for now
                if url not in self.index:
                    time.sleep(REQUEST_DELAY)
                    product_data = self._fetch_product_page(url, 'dept56_official')
                    if product_data:
                        self.index[url] = product_data
                        self.stats['from_main_site'] += 1
                        self.stats['total_products'] += 1
                        
                        if (i + 1) % 10 == 0:
                            print(f"    Progress: {i + 1}/{len(product_urls[:100])} products")
            
        except Exception as e:
            print(f"  ⚠️  Error crawling sitemap: {e}")
            self.stats['errors'] += 1
    
    def _fetch_product_page(self, url: str, source: str) -> Optional[Dict]:
        """
        Fetch and parse a product page
        
        Args:
            url: Product page URL
            source: 'main' or 'retired'
            
        Returns:
            Dictionary with product data or None if error
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Import parser (will create this next)
            from product_parser import ProductParser
            parser = ProductParser(soup, url, source)
            
            return parser.extract_data()
            
        except Exception as e:
            print(f"      ⚠️  Error fetching {url}: {e}")
            self.stats['errors'] += 1
            return None


# Test function
if __name__ == "__main__":
    builder = IndexBuilder(use_cache=False)  # Force rebuild
    index = builder.build_index(crawl_main=False, crawl_retired=True)  # Start with retired only
    
    print(f"\n📊 Index contains {len(index)} products")
    
    # Show sample
    if index:
        print("\n📦 Sample products:")
        for i, (url, data) in enumerate(list(index.items())[:3]):
            print(f"\n{i+1}. {data.get('name', 'Unknown')}")
            print(f"   SKU: {data.get('sku', 'N/A')}")
            print(f"   Series: {data.get('series', 'N/A')}")
            print(f"   URL: {url}")
