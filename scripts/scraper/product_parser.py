"""
Product Parser for Department 56 Websites
Extracts structured data from Shopify product pages
"""

from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Optional, List
from datetime import datetime


class ProductParser:
    """Parses Department 56 product pages (both main and retired sites)"""
    
    def __init__(self, soup: BeautifulSoup, url: str, source: str):
        """
        Initialize parser
        
        Args:
            soup: BeautifulSoup object of the product page
            url: Product page URL
            source: 'main' or 'retired'
        """
        self.soup = soup
        self.url = url
        self.source = source
    
    def extract_data(self) -> Dict:
        """Extract all available product data"""
        data = {
            'url': self.url,
            'source': self.source,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Try JSON-LD first (most reliable)
        json_ld_data = self._extract_json_ld()
        if json_ld_data:
            data.update(json_ld_data)
        
        # Extract from HTML structure
        data.update({
            'name': self._extract_name(),
            'sku': self._extract_sku(),
            'series': self._extract_series(),
            'description': self._extract_description(),
            'intro_year': self._extract_intro_year(),
            'retired_year': self._extract_retired_year(),
            'srp': self._extract_srp(),
            'images': self._extract_images(),
        })
        
        # Clean up None values
        data = {k: v for k, v in data.items() if v is not None}
        
        return data
    
    def _extract_json_ld(self) -> Optional[Dict]:
        """Extract JSON-LD structured data if available"""
        try:
            scripts = self.soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if script.string:
                    json_data = json.loads(script.string)
                    
                    # Handle Product schema
                    if json_data.get('@type') == 'Product':
                        return {
                            'name': json_data.get('name'),
                            'sku': json_data.get('sku'),
                            'description': json_data.get('description'),
                            'images': [json_data.get('image')] if json_data.get('image') else [],
                            'srp': json_data.get('offers', {}).get('price')
                        }
        except:
            pass
        return None
    
    def _extract_name(self) -> Optional[str]:
        """Extract product name/title"""
        # Try multiple selectors
        selectors = [
            'h1.product-title',
            'h1.product__title',
            'h1[itemprop="name"]',
            '.product-single__title',
            'h1.productitem--title'
        ]
        
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        # Fallback to first h1
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return None
    
    def _extract_sku(self) -> Optional[str]:
        """Extract SKU/item number"""
        # Try meta tags
        meta_sku = self.soup.find('meta', property='product:retailer_item_id')
        if meta_sku:
            return meta_sku.get('content', '').strip()
        
        # Try visible SKU labels
        sku_patterns = [
            r'SKU[:\s]+([A-Z0-9\.\-]+)',
            r'Item\s*#[:\s]*([A-Z0-9\.\-]+)',
            r'Product\s*Code[:\s]*([A-Z0-9\.\-]+)',
            r'Item\s*Number[:\s]*([A-Z0-9\.\-]+)'
        ]
        
        text = self.soup.get_text()
        for pattern in sku_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try specific elements
        sku_elem = self.soup.select_one('.product-sku, .sku, [class*="sku"]')
        if sku_elem:
            text = sku_elem.get_text(strip=True)
            # Remove "SKU:" prefix
            return re.sub(r'^SKU[:\s]*', '', text, flags=re.IGNORECASE)
        
        return None
    
    def _extract_series(self) -> Optional[str]:
        """Extract series/collection name"""
        # Common series keywords with normalized names
        series_map = {
            'north pole': 'North Pole Series',
            'dickens': "Dickens' Village",
            'snow village': 'Original Snow Village',
            'new england': 'New England Village',
            'alpine': 'Alpine Village',
            'christmas in the city': 'Christmas in the City',
            'bethlehem': 'Little Town of Bethlehem',
            'halloween': 'Halloween Village',
            'department 56': 'Department 56'
        }
        
        # Try URL path first (most reliable on retired site)
        if '/north-pole-series' in self.url.lower():
            return 'North Pole Series'
        elif '/dickens-village' in self.url.lower():
            return "Dickens' Village"
        elif '/original-snow-village' in self.url.lower():
            return 'Original Snow Village'
        elif '/new-england-village' in self.url.lower():
            return 'New England Village'
        elif '/alpine-village' in self.url.lower():
            return 'Alpine Village'
        elif '/christmas-in-the-city' in self.url.lower():
            return 'Christmas in the City'
        elif '/little-town-of-bethlehem' in self.url.lower():
            return 'Little Town of Bethlehem'
        
        # Try breadcrumbs
        breadcrumbs = self.soup.select('.breadcrumb a, [class*="breadcrumb"] a')
        for crumb in breadcrumbs:
            text = crumb.get_text(strip=True).lower()
            for keyword, series_name in series_map.items():
                if keyword in text:
                    return series_name
        
        # Try product description text
        text = self.soup.get_text().lower()
        for keyword, series_name in series_map.items():
            # Look for "NP" prefix (North Pole) or series in description
            if keyword == 'north pole' and ' np ' in text:
                return 'North Pole Series'
            elif keyword in text:
                return series_name
        
        return None
    
    def _extract_description(self) -> Optional[str]:
        """Extract product description"""
        # Try multiple selectors
        selectors = [
            '.product-description',
            '.product__description',
            '[itemprop="description"]',
            '.rte.product-single__description',
            '.productitem--description'
        ]
        
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                # Get text, clean up extra whitespace
                text = elem.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
                return text[:1000] if text else None  # Limit to 1000 chars
        
        # Try meta description
        meta_desc = self.soup.find('meta', property='og:description')
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        return None
    
    def _extract_intro_year(self) -> Optional[int]:
        """Extract introduction year"""
        # Common patterns in Department 56 descriptions
        patterns = [
            r'Introduced\s+(?:in\s+)?([A-Z][a-z]+)\s+(\d{4})',  # "Introduced May 2003"
            r'Introduced[:\s]+(\d{4})',  # "Introduced: 2003"
            r'First\s+Released[:\s]+(\d{4})',
            r'Year[:\s]+(\d{4})',
            r'©\s*(\d{4})'
        ]
        
        text = self.soup.get_text()
        
        # Try month + year pattern first (most common on retired site)
        month_year_match = re.search(r'Introduced\s+([A-Z][a-z]+)\s+(\d{4})', text, re.IGNORECASE)
        if month_year_match:
            year = int(month_year_match.group(2))
            if 1976 <= year <= datetime.now().year:
                return year
        
        # Try other patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Get the last group (the year)
                year_str = match.group(match.lastindex)
                try:
                    year = int(year_str)
                    # Sanity check (Department 56 founded in 1976)
                    if 1976 <= year <= datetime.now().year:
                        return year
                except ValueError:
                    continue
        
        return None
    
    def _extract_retired_year(self) -> Optional[int]:
        """Extract retirement year"""
        patterns = [
            r'Retired\s+(?:in\s+)?([A-Z][a-z]+)\s+(\d{4})',  # "Retired December 2004"
            r'Retired[:\s]+(\d{4})',
            r'Retired\s+in[:\s]+(\d{4})',
            r'Discontinued[:\s]+(\d{4})'
        ]
        
        text = self.soup.get_text()
        
        # Try month + year pattern first
        month_year_match = re.search(r'Retired\s+([A-Z][a-z]+)\s+(\d{4})', text, re.IGNORECASE)
        if month_year_match:
            year = int(month_year_match.group(2))
            if 1976 <= year <= datetime.now().year:
                return year
        
        # Try other patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year_str = match.group(match.lastindex)
                try:
                    year = int(year_str)
                    if 1976 <= year <= datetime.now().year:
                        return year
                except ValueError:
                    continue
        
        return None
    
    def _extract_srp(self) -> Optional[float]:
        """Extract original suggested retail price"""
        # Look for price patterns
        patterns = [
            r'SRP[:\s]*\$?([\d,]+\.?\d*)',
            r'Original\s+Price[:\s]*\$?([\d,]+\.?\d*)',
            r'Retail\s+Price[:\s]*\$?([\d,]+\.?\d*)',
            r'MSRP[:\s]*\$?([\d,]+\.?\d*)'
        ]
        
        text = self.soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        # Try structured price elements
        price_elem = self.soup.select_one('.price, [itemprop="price"], .product-price')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        return None
    
    def _extract_images(self) -> List[str]:
        """Extract all product image URLs"""
        images = []
        
        # Try Open Graph image
        og_image = self.soup.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content', '').strip()
            if img_url:
                images.append(img_url)
        
        # Try product image elements
        img_selectors = [
            '.product-image img',
            '.product__image img',
            '[class*="product-gallery"] img',
            '.productitem--image img'
        ]
        
        for selector in img_selectors:
            img_elems = self.soup.select(selector)
            for img in img_elems:
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http'):
                    # Remove size parameters for full resolution
                    src = re.sub(r'_\d+x\d+\.', '.', src)
                    if src not in images:
                        images.append(src)
        
        return images


# Test function
if __name__ == "__main__":
    import requests
    
    # Test on a sample URL
    test_url = "https://retiredproducts.department56.com/products/56-54305-robbies-robot-factory"
    
    print(f"🧪 Testing parser on: {test_url}\n")
    
    try:
        response = requests.get(test_url, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')
        
        parser = ProductParser(soup, test_url, 'retired')
        data = parser.extract_data()
        
        print("Extracted data:")
        for key, value in data.items():
            if key == 'images':
                print(f"  {key}: {len(value)} images")
                for i, img in enumerate(value[:2]):
                    print(f"    {i+1}. {img[:80]}...")
            else:
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
