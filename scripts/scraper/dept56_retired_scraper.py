# Web Scraper for Department 56 Data Enhancement
# Prototype scraper for retired products site

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

# Third-party imports (need to install)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from fuzzywuzzy import fuzz
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    print("\nInstall required packages with:")
    print("pip install selenium webdriver-manager fuzzywuzzy python-Levenshtein supabase python-dotenv")
    exit(1)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    print("Required: VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

# Initialize Supabase client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Scraper configuration
DEPT56_RETIRED_BASE_URL = "https://retiredproducts.department56.com"
REQUEST_DELAY = 2  # seconds between requests


class Dept56RetiredScraper:
    """Scraper for retiredproducts.department56.com"""
    
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Selenium WebDriver"""
        self.headless = headless
        self.driver = None
        
    def __enter__(self):
        """Context manager entry - setup driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup driver"""
        if self.driver:
            self.driver.quit()
    
    def search_item(self, item_name: str, item_number: str = None) -> Optional[Dict]:
        """
        Search for an item on the retired products site
        
        Args:
            item_name: Name of the item to search for
            item_number: Optional item number for more specific search
            
        Returns:
            Dictionary with scraped data or None if not found
        """
        start_time = time.time()
        
        try:
            # Build search query
            search_query = item_number if item_number else item_name
            search_url = f"{DEPT56_RETIRED_BASE_URL}/search?q={quote_plus(search_query)}"
            
            print(f"\n🔍 Searching for: {search_query}")
            print(f"📍 URL: {search_url}")
            
            # Load search results page
            self.driver.get(search_url)
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "productgrid--item"))
                )
            except TimeoutException:
                print("⚠️  No results found or page timeout")
                self._log_scrape(search_query, "dept56_retired", 0, False, "timeout", 
                                int((time.time() - start_time) * 1000))
                return None
            
            # Get all product results
            products = self.driver.find_elements(By.CLASS_NAME, "productgrid--item")
            
            if not products:
                print("❌ No products found")
                self._log_scrape(search_query, "dept56_retired", 0, False, "not_found",
                                int((time.time() - start_time) * 1000))
                return None
            
            print(f"✅ Found {len(products)} result(s)")
            
            # Find best match using fuzzy matching
            best_match = None
            best_score = 0
            
            for product in products[:5]:  # Check first 5 results
                try:
                    title_elem = product.find_element(By.CLASS_NAME, "productitem--title")
                    title = title_elem.text.strip()
                    
                    # Calculate fuzzy match score
                    score = fuzz.token_sort_ratio(item_name.lower(), title.lower()) / 100.0
                    
                    print(f"  📦 {title} (score: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_match = product
                        best_match_title = title
                except Exception as e:
                    continue
            
            if best_match and best_score >= 0.6:  # Minimum 60% match
                print(f"🎯 Best match: {best_match_title} (score: {best_score:.2f})")
                
                # Click on the best match to get details
                link = best_match.find_element(By.CSS_SELECTOR, "a.productitem--image-link")
                product_url = link.get_attribute("href")
                
                print(f"📖 Loading product page...")
                self.driver.get(product_url)
                
                # Wait for product details to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-main"))
                )
                
                # Extract product details
                details = self._extract_product_details(product_url)
                details['name_match_score'] = best_score
                details['search_query'] = search_query
                
                execution_time = int((time.time() - start_time) * 1000)
                self._log_scrape(search_query, "dept56_retired", len(products), True, None, 
                                execution_time, best_match_title, product_url, best_score)
                
                return details
            else:
                print(f"❌ No good match found (best score: {best_score:.2f})")
                self._log_scrape(search_query, "dept56_retired", len(products), False, "low_confidence",
                                int((time.time() - start_time) * 1000))
                return None
                
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            self._log_scrape(search_query, "dept56_retired", 0, False, "error",
                            int((time.time() - start_time) * 1000), error_message=str(e))
            return None
    
    def _extract_product_details(self, product_url: str) -> Dict:
        """Extract details from product page"""
        details = {
            'dept56_retired_url': product_url,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Product name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.product-title")
                details['name'] = name_elem.text.strip()
            except NoSuchElementException:
                details['name'] = None
            
            # Item number
            try:
                sku_elem = self.driver.find_element(By.CLASS_NAME, "product-sku")
                details['item_number'] = sku_elem.text.replace("SKU:", "").strip()
            except NoSuchElementException:
                details['item_number'] = None
            
            # Description
            try:
                desc_elem = self.driver.find_element(By.CLASS_NAME, "product-description")
                details['description'] = desc_elem.text.strip()
            except NoSuchElementException:
                details['description'] = None
            
            # Year (from description or metadata)
            try:
                meta_items = self.driver.find_elements(By.CLASS_NAME, "product-meta-item")
                for item in meta_items:
                    text = item.text.lower()
                    if "introduced" in text or "year" in text:
                        # Extract year from text
                        import re
                        year_match = re.search(r'(19|20)\d{2}', item.text)
                        if year_match:
                            details['intro_year'] = int(year_match.group())
            except:
                details['intro_year'] = None
            
            # Images
            details['images'] = []
            try:
                image_elems = self.driver.find_elements(By.CLASS_NAME, "product-image")
                for img in image_elems:
                    img_url = img.get_attribute("src")
                    if img_url and img_url.startswith("http"):
                        details['images'].append(img_url)
            except:
                pass
            
            details['primary_image_url'] = details['images'][0] if details['images'] else None
            
            print(f"✅ Extracted details:")
            print(f"   Name: {details.get('name')}")
            print(f"   SKU: {details.get('item_number')}")
            print(f"   Year: {details.get('intro_year')}")
            print(f"   Images: {len(details['images'])}")
            
        except Exception as e:
            print(f"⚠️  Error extracting details: {str(e)}")
        
        return details
    
    def _log_scrape(self, search_query: str, source: str, results_found: int, 
                   success: bool, error_type: str = None, execution_time_ms: int = 0,
                   best_match_name: str = None, best_match_url: str = None, 
                   best_match_score: float = None, error_message: str = None):
        """Log scraping operation to database"""
        try:
            supabase.table("scraping_log").insert({
                "search_query": search_query,
                "item_type": "house",  # Assume house for now
                "source_site": source,
                "results_found": results_found,
                "best_match_name": best_match_name,
                "best_match_url": best_match_url,
                "best_match_score": best_match_score,
                "success": success,
                "error_type": error_type,
                "error_message": error_message,
                "execution_time_ms": execution_time_ms
            }).execute()
        except Exception as e:
            print(f"⚠️  Failed to log scrape: {str(e)}")


def calculate_confidence(scraped_data: Dict, original_name: str) -> float:
    """Calculate overall confidence score for scraped data"""
    scores = []
    
    # Name match score (already calculated)
    if 'name_match_score' in scraped_data:
        scores.append(scraped_data['name_match_score'] * 0.5)  # 50% weight
    
    # Data completeness score
    required_fields = ['name', 'item_number', 'description', 'primary_image_url']
    present_fields = sum([1 for field in required_fields if scraped_data.get(field)])
    completeness = (present_fields / len(required_fields)) * 0.3  # 30% weight
    scores.append(completeness)
    
    # Has multiple images (bonus)
    if len(scraped_data.get('images', [])) > 1:
        scores.append(0.1)  # 10% weight
    
    # Has year information (bonus)
    if scraped_data.get('intro_year'):
        scores.append(0.1)  # 10% weight
    
    overall = sum(scores)
    return round(overall, 2)


def insert_staged_house(scraped_data: Dict, original_house_id: str = None) -> bool:
    """Insert scraped data into staged_houses table"""
    try:
        confidence = calculate_confidence(scraped_data, scraped_data.get('search_query', ''))
        
        staged_house = {
            "original_house_id": original_house_id,
            "item_number": scraped_data.get('item_number'),
            "name": scraped_data.get('name'),
            "intro_year": scraped_data.get('intro_year'),
            "description": scraped_data.get('description'),
            "primary_image_url": scraped_data.get('primary_image_url'),
            "additional_images": json.dumps(scraped_data.get('images', [])),
            "dept56_retired_url": scraped_data.get('dept56_retired_url'),
            "name_match_score": scraped_data.get('name_match_score'),
            "details_confidence_score": confidence,
            "overall_confidence_score": confidence,
            "status": "pending"
        }
        
        result = supabase.table("staged_houses").insert(staged_house).execute()
        print(f"✅ Inserted into staged_houses (confidence: {confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert staged house: {str(e)}")
        return False


# Test with a few sample items
if __name__ == "__main__":
    print("=" * 70)
    print("🎄 Department 56 Web Scraper - Prototype Test")
    print("=" * 70)
    
    # Sample items to test
    test_items = [
        {"name": "Robbie's Robot Factory", "item_number": "56.54305"},
        {"name": "Santa's Wonderland House", "item_number": None},
        {"name": "Fezziwig's Warehouse", "item_number": None},
    ]
    
    with Dept56RetiredScraper(headless=False) as scraper:  # headless=False to see browser
        for item in test_items:
            print(f"\n{'='*70}")
            result = scraper.search_item(item['name'], item['item_number'])
            
            if result:
                # Insert into staging
                insert_staged_house(result)
            
            # Respectful delay between requests
            print(f"\n⏳ Waiting {REQUEST_DELAY} seconds before next request...")
            time.sleep(REQUEST_DELAY)
    
    print("\n" + "="*70)
    print("✅ Scraping test complete!")
    print("🔍 Check your Supabase staged_houses table for results")
    print("="*70)
