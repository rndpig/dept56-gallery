"""
Enhanced Multi-Source Scraper (Sitemap-Based)
Builds on existing efficient sitemap.xml approach with multi-source validation

Uses your proven architecture:
- Sitemap.xml for efficient product discovery  
- requests + BeautifulSoup for parsing
- Index-based search for fast lookups
- Cross-source validation for confidence scoring
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin

# Standard library imports
import xml.etree.ElementTree as ET

# Third-party imports (existing dependencies)
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from bs4 import BeautifulSoup
    from rapidfuzz import fuzz
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install -r requirements.txt")
    exit(1)

# Load environment
load_dotenv()

# Supabase configuration (optional for testing)
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Connected to Supabase")
else:
    supabase = None
    print("⚠️ Running without Supabase connection (testing mode)")

# Site configurations
SITES = {
    'dept56_official': {
        'base_url': 'https://www.department56.com',
        'sitemap_url': 'https://www.department56.com/sitemap.xml',
        'product_path': '/products/',
        'index_file': 'dept56_official_index.json'
    },
    'dept56_retired': {
        'base_url': 'https://retiredproducts.department56.com',
        'sitemap_url': 'https://retiredproducts.department56.com/sitemap.xml',
        'product_path': '/products/',
        'index_file': 'dept56_retired_index.json'
    },
    'replacements': {
        'base_url': 'https://www.replacements.com',
        'sitemap_url': 'https://www.replacements.com/sitemap.xml',
        'product_path': '/p/',
        'index_file': 'replacements_index.json'
    }
}

REQUEST_DELAY = 1.0  # Be respectful
USER_AGENT = "Department56GalleryBot/2.0 (Educational/Personal Collection; +mailto:rndpig@gmail.com)"

@dataclass
class ProductData:
    """Structured product data"""
    name: str
    item_number: str = ""
    intro_year: Optional[int] = None
    retire_year: Optional[int] = None
    description: str = ""
    dimensions: str = ""
    primary_image_url: str = ""
    additional_images: List[str] = field(default_factory=list)
    discovered_series: str = ""
    discovered_collection: str = ""
    source_url: str = ""
    source_site: str = ""
    item_type: str = "house"  # house or accessory
    related_items: List[str] = field(default_factory=list)


class SitemapBasedScraper:
    """Enhanced multi-source scraper using sitemap.xml approach"""
    
    def __init__(self):
        self.session = self._create_session()
        self.indices = {}  # Cache indices for each site
        
    def _create_session(self) -> requests.Session:
        """Create session with your proven retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
        session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def build_indices(self, sites: List[str] = None, force_rebuild: bool = False):
        """Build/load product indices for specified sites"""
        sites = sites or list(SITES.keys())
        
        for site_name in sites:
            print(f"\n🔍 Building index for {site_name}...")
            
            config = SITES[site_name]
            index_file = config['index_file']
            
            # Check if we can use the existing product_index.json from working scraper
            script_dir = os.path.dirname(os.path.abspath(__file__))
            existing_index_path = os.path.join(script_dir, 'product_index.json')
            if not force_rebuild and os.path.exists(existing_index_path):
                try:
                    print(f"📂 Loading existing product index...")
                    with open(existing_index_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    
                    # Extract products from nested structure
                    products_data = existing_data.get('index', existing_data)
                    self.indices[site_name] = products_data
                    print(f"✅ Loaded existing index: {len(self.indices[site_name])} products")
                    continue
                except Exception as e:
                    print(f"⚠️ Failed to load existing index: {e}")
            
            # Try to load our cached index
            if not force_rebuild and os.path.exists(index_file):
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.indices[site_name] = data.get('products', {})
                        print(f"✅ Loaded cached index: {len(self.indices[site_name])} products")
                        continue
                except Exception as e:
                    print(f"⚠️ Cache load failed: {e}")
            
            # Build fresh index
            self.indices[site_name] = self._build_site_index(site_name, config)
            
            # Save to cache
            self._save_index(site_name, index_file)
    
    def _build_site_index(self, site_name: str, config: Dict) -> Dict[str, ProductData]:
        """Build index for a single site using sitemap approach"""
        products = {}
        
        try:
            # Get sitemap URLs
            sitemap_url = config['sitemap_url']
            print(f"📋 Fetching sitemap: {sitemap_url}")
            
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            # Parse sitemap XML
            root = ET.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Extract product URLs
            urls = root.findall('.//ns:url/ns:loc', namespace)
            product_urls = [
                url.text for url in urls 
                if config['product_path'] in url.text
            ]
            
            print(f"📦 Found {len(product_urls)} product URLs")
            
            # Crawl each product (limit for initial testing)
            for i, url in enumerate(product_urls[:50]):  # Start with 50 products
                time.sleep(REQUEST_DELAY)
                
                product_data = self._parse_product_page(url, site_name)
                if product_data:
                    products[url] = product_data
                    
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{min(len(product_urls), 50)}")
            
        except Exception as e:
            print(f"❌ Error building {site_name} index: {e}")
        
        return products
    
    def _parse_product_page(self, url: str, site_name: str) -> Optional[ProductData]:
        """Parse individual product page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Site-specific parsing logic
            if site_name == 'dept56_retired':
                return self._parse_dept56_retired(soup, url)
            elif site_name == 'dept56_official':
                return self._parse_dept56_official(soup, url)
            elif site_name == 'replacements':
                return self._parse_replacements(soup, url)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error parsing {url}: {e}")
            return None
    
    def _parse_dept56_retired(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Parse retiredproducts.department56.com page"""
        try:
            # Extract product name
            name_elem = (soup.find('h1') or 
                        soup.find('title') or 
                        soup.find('h2', class_='product-title'))
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            
            # Create product data
            product = ProductData(
                name=name,
                source_url=url,
                source_site='dept56_retired'
            )
            
            # Extract SKU/item number
            sku_patterns = ['SKU:', 'Item #:', 'Product Code:']
            for pattern in sku_patterns:
                sku_elem = soup.find(string=lambda text: text and pattern in text)
                if sku_elem:
                    product.item_number = sku_elem.split(pattern)[-1].strip()
                    break
            
            # Extract description
            desc_elem = (soup.find('div', class_='description') or 
                        soup.find('div', class_='product-description') or
                        soup.find('p', class_='description'))
            if desc_elem:
                product.description = desc_elem.get_text(strip=True)
            
            # Extract years from text
            text_content = soup.get_text()
            years = self._extract_years(text_content)
            if years:
                product.intro_year = years.get('intro')
                product.retire_year = years.get('retire')
            
            # Extract series/collection from breadcrumbs
            breadcrumbs = soup.find('nav', class_='breadcrumb') or soup.find('ol', class_='breadcrumb')
            if breadcrumbs:
                links = breadcrumbs.find_all('a')
                for link in links:
                    text = link.get_text(strip=True).lower()
                    if 'village' in text or 'series' in text:
                        product.discovered_series = link.get_text(strip=True)
                    elif 'collection' in text:
                        product.discovered_collection = link.get_text(strip=True)
            
            # Extract primary image
            img_elem = soup.find('img', src=True)
            if img_elem and 'product' in img_elem['src'].lower():
                product.primary_image_url = urljoin(url, img_elem['src'])
            
            # Determine if accessory or house
            product.item_type = self._determine_item_type(name, product.description)
            
            return product
            
        except Exception as e:
            print(f"Error parsing retired product: {e}")
            return None
    
    def _parse_dept56_official(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Parse department56.com page (current products)"""
        # Similar structure to retired, but adapt selectors for current site
        # Implementation would be similar to _parse_dept56_retired
        # but with different CSS selectors for the main site
        pass
    
    def _parse_replacements(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Parse replacements.com page for cross-reference data"""
        # Focus on extracting relationship data and cross-references
        pass
    
    def _extract_years(self, text: str) -> Dict[str, Optional[int]]:
        """Extract intro/retire years from text"""
        import re
        
        years = {'intro': None, 'retire': None}
        
        # Look for year patterns
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        valid_years = [int(y) for y in year_matches if 1976 <= int(y) <= datetime.now().year]
        
        if valid_years:
            years['intro'] = min(valid_years)  # Earliest year is likely intro
            if len(valid_years) > 1:
                years['retire'] = max(valid_years)  # Latest year is likely retire
        
        return years
    
    def _determine_item_type(self, name: str, description: str) -> str:
        """Determine if item is house or accessory"""
        house_keywords = ['house', 'building', 'church', 'shop', 'store', 'factory', 'mill']
        accessory_keywords = ['accessory', 'figure', 'tree', 'fence', 'sign', 'car', 'sleigh']
        
        text = f"{name} {description}".lower()
        
        house_score = sum(1 for keyword in house_keywords if keyword in text)
        accessory_score = sum(1 for keyword in accessory_keywords if keyword in text)
        
        return "accessory" if accessory_score > house_score else "house"
    
    def _save_index(self, site_name: str, filename: str):
        """Save index to cache file"""
        try:
            data = {
                'site': site_name,
                'created_at': datetime.now().isoformat(),
                'product_count': len(self.indices[site_name]),
                'products': {
                    url: {
                        'name': product.name,
                        'item_number': product.item_number,
                        'intro_year': product.intro_year,
                        'retire_year': product.retire_year,
                        'description': product.description,
                        'primary_image_url': product.primary_image_url,
                        'discovered_series': product.discovered_series,
                        'discovered_collection': product.discovered_collection,
                        'source_site': product.source_site,
                        'item_type': product.item_type
                    }
                    for url, product in self.indices[site_name].items()
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {site_name} index: {len(self.indices[site_name])} products")
            
        except Exception as e:
            print(f"❌ Error saving {site_name} index: {e}")
    
    def search_multi_source(self, item_name: str, item_number: str = None, item_type: str = "house") -> Dict:
        """
        Search across all loaded indices with differentiated strategy
        
        Args:
            item_name: Name to search for
            item_number: Optional SKU/item number  
            item_type: "house" or "accessory" for strategy differentiation
        """
        print(f"🔍 Multi-source {item_type.upper()} search for: {item_name}")
        results = {}
        
        search_terms = [item_name]
        if item_number:
            search_terms.append(item_number)
        
        for site_name, products in self.indices.items():
            best_match = None
            best_score = 0
            
            for url, product in products.items():
                # Handle both ProductData objects and dict data
                if isinstance(product, dict):
                    product_name = product.get('name', '')
                    product_item_number = product.get('item_number', '')
                else:
                    product_name = product.name
                    product_item_number = product.item_number
                
                # Calculate fuzzy match scores
                for search_term in search_terms:
                    name_score = fuzz.token_sort_ratio(search_term.lower(), product_name.lower())
                    sku_score = 0
                    if item_number and product_item_number:
                        sku_score = fuzz.ratio(item_number, product_item_number)
                    
                    combined_score = max(name_score, sku_score)
                    
                    if combined_score > best_score and combined_score >= 60:
                        best_score = combined_score
                        best_match = {
                            'product': product if not isinstance(product, dict) else ProductData(
                                name=product.get('name', ''),
                                item_number=product.get('item_number', ''),
                                intro_year=product.get('intro_year'),
                                retire_year=product.get('retire_year'),
                                description=product.get('description', ''),
                                primary_image_url=product.get('primary_image_url', ''),
                                source_url=url,
                                source_site=site_name,
                                discovered_series=product.get('discovered_series', ''),
                                discovered_collection=product.get('discovered_collection', ''),
                                dimensions=product.get('dimensions', '')
                            ),
                            'score': combined_score,
                            'url': url
                        }
            
            if best_match:
                results[site_name] = best_match
        
        return results
    
    def calculate_confidence(self, search_name: str, multi_results: Dict) -> Dict:
        """Calculate confidence scores based on multi-source validation"""
        if not multi_results:
            return {'overall': 0.0, 'name_match': 0.0, 'details': 0.0, 'cross_source': 0.0}
        
        # Best name match score
        best_name_score = max(result['score'] for result in multi_results.values()) / 100
        
        # Details completeness (average across sources)
        details_scores = []
        for result in multi_results.values():
            product = result['product']
            required_fields = ['item_number', 'description', 'intro_year', 'primary_image_url']
            available = sum(1 for field in required_fields if getattr(product, field))
            details_scores.append(available / len(required_fields))
        
        details_score = sum(details_scores) / len(details_scores) if details_scores else 0
        
        # Cross-source validation bonus
        cross_source_score = min(len(multi_results) / 3, 1.0)  # Max bonus for 3+ sources
        
        # Overall confidence
        overall = (best_name_score * 0.5 + details_score * 0.3 + cross_source_score * 0.2)
        
        return {
            'overall': overall,
            'name_match': best_name_score,
            'details': details_score,
            'cross_source': cross_source_score
        }
    
    def apply_strategy_enhancements(self, results: Dict, item_type: str, item_name: str) -> Dict:
        """
        Apply strategy-specific enhancements based on item type
        
        Args:
            results: Search results from search_multi_source
            item_type: "house" or "accessory"
            item_name: Original search term
            
        Returns:
            Enhanced results with strategy-specific data
        """
        enhanced = {
            'original_results': results,
            'item_type': item_type,
            'strategy_data': {}
        }
        
        if item_type == "house":
            enhanced['strategy_data'] = self._apply_house_strategy(results, item_name)
        elif item_type == "accessory":
            enhanced['strategy_data'] = self._apply_accessory_strategy(results, item_name)
        
        return enhanced
    
    def _apply_house_strategy(self, results: Dict, item_name: str) -> Dict:
        """Apply house-specific strategy enhancements"""
        strategy_data = {
            'focus': 'series_collection_discovery',
            'enhanced_series': {},
            'enhanced_collection': {},
            'architectural_details': {},
            'retirement_info': {}
        }
        
        # Extract enhanced series/collection info across sources
        for site, result in results.items():
            product = result['product']
            
            # Look for series patterns in description
            if product.description:
                desc_lower = product.description.lower()
                
                # Series patterns
                series_patterns = [
                    r'(\w+(?:\s+\w+)*)\s+series',
                    r'from\s+the\s+(\w+(?:\s+\w+)*)\s+collection',
                    r'part\s+of\s+(\w+(?:\s+\w+)*)'
                ]
                
                for pattern in series_patterns:
                    import re
                    match = re.search(pattern, desc_lower)
                    if match:
                        series_name = match.group(1).title()
                        if series_name not in strategy_data['enhanced_series']:
                            strategy_data['enhanced_series'][series_name] = []
                        strategy_data['enhanced_series'][series_name].append(site)
        
        return strategy_data
    
    def _apply_accessory_strategy(self, results: Dict, item_name: str) -> Dict:
        """Apply accessory-specific strategy enhancements"""
        strategy_data = {
            'focus': 'house_compatibility',
            'compatibility_hints': {},
            'relationship_signals': {},
            'set_indicators': {}
        }
        
        # Look for compatibility hints across sources
        for site, result in results.items():
            product = result['product']
            
            if product.description:
                desc_lower = product.description.lower()
                
                # Compatibility patterns
                compatibility_patterns = {
                    'goes_with': r'goes\s+with\s+([^.]+)',
                    'designed_for': r'designed\s+for\s+([^.]+)',
                    'coordinates_with': r'coordinates\s+with\s+([^.]+)',
                    'complements': r'complements\s+([^.]+)'
                }
                
                site_hints = {}
                for hint_type, pattern in compatibility_patterns.items():
                    import re
                    matches = re.findall(pattern, desc_lower)
                    if matches:
                        site_hints[hint_type] = matches
                
                if site_hints:
                    strategy_data['compatibility_hints'][site] = site_hints
                    
                # Set indicators
                set_patterns = [
                    r'set\s+of\s+(\d+)',
                    r'(\d+)\s*(?:pc|piece|pcs)',
                    r'includes\s+([^.]+)'
                ]
                
                for pattern in set_patterns:
                    import re
                    match = re.search(pattern, desc_lower)
                    if match:
                        if 'set_info' not in strategy_data['set_indicators']:
                            strategy_data['set_indicators']['set_info'] = []
                        strategy_data['set_indicators']['set_info'].append({
                            'site': site,
                            'info': match.group(0)
                        })
        
        return strategy_data


# Test function
async def test_enhanced_scraper():
    """Test the enhanced sitemap-based scraper with differentiated strategies"""
    scraper = SitemapBasedScraper()
    
    # Build indices (start with just retired site)
    scraper.build_indices(['dept56_retired'], force_rebuild=False)
    
    # Test houses with actual products from the index
    test_houses = [
        {"name": "Have a Seat Elves", "number": "56.56437", "type": "house"},
        {"name": "Santa's Wonderland House", "number": "", "type": "house"}
    ]
    
    # Test accessories  
    test_accessories = [
        {"name": "15th Anniversary Santa", "number": "", "type": "accessory"},
        {"name": "Christmas Tree Lot", "number": "", "type": "accessory"}
    ]
    
    all_tests = test_houses + test_accessories
    
    for item in all_tests:
        print(f"\n{'='*60}")
        print(f"🔍 Testing {item['type'].upper()}: {item['name']}")
        
        # Basic search with strategy
        results = scraper.search_multi_source(item['name'], item['number'], item['type'])
        
        if results:
            # Apply strategy enhancements
            enhanced = scraper.apply_strategy_enhancements(results, item['type'], item['name'])
            
            print(f"   📊 Found {len(results)} sources")
            print(f"   🎯 Strategy: {enhanced['strategy_data']['focus']}")
            
            # Show strategy-specific findings
            if item['type'] == 'house':
                series_data = enhanced['strategy_data']['enhanced_series']
                if series_data:
                    print(f"   🏠 Enhanced Series Discovery:")
                    for series, sites in series_data.items():
                        print(f"      - {series} (found on: {', '.join(sites)})")
                        
            elif item['type'] == 'accessory':
                compat_data = enhanced['strategy_data']['compatibility_hints']
                if compat_data:
                    print(f"   🔗 House Compatibility Hints:")
                    for site, hints in compat_data.items():
                        print(f"      - {site}: {hints}")
                
                set_data = enhanced['strategy_data']['set_indicators']
                if set_data:
                    print(f"   📦 Set Information:")
                    for info_type, infos in set_data.items():
                        for info in infos:
                            print(f"      - {info['site']}: {info['info']}")
            
            # Calculate confidence
            confidence = scraper.calculate_confidence(item['name'], results)
            print(f"   📈 Confidence: {confidence['overall']:.2f}")
        else:
            print(f"   ❌ No results found")
    
    print(f"\n{'='*60}")
    print("✅ Differentiated scraper test complete!")

if __name__ == "__main__":
    # Test without database dependencies
    print("🧪 Testing Enhanced Sitemap Scraper with Differentiated Strategies")
    print("Note: Running in test mode without database connection")
    import asyncio
    asyncio.run(test_enhanced_scraper())