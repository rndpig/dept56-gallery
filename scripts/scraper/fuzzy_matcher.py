"""
Fuzzy Matcher for Department 56 Products
Matches items from your database against the crawled index
"""

import re
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process


class FuzzyMatcher:
    """Matches product names using normalization and fuzzy matching"""
    
    def __init__(self, product_index: Dict):
        """
        Initialize matcher with product index
        
        Args:
            product_index: Dictionary of {url: product_data}
        """
        self.index = product_index
        self._build_search_index()
    
    def _build_search_index(self):
        """Build searchable lists for fuzzy matching"""
        self.search_data = []
        
        for url, product in self.index.items():
            name = product.get('name', '')
            sku = product.get('sku', '')
            
            if name:
                self.search_data.append({
                    'url': url,
                    'name': name,
                    'sku': sku,
                    'normalized_name': self._normalize_text(name),
                    'normalized_sku': self._normalize_text(sku) if sku else '',
                    'product': product
                })
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for matching
        
        - Lowercase
        - Remove punctuation (except hyphens in SKUs)
        - Normalize whitespace
        - Handle common variations
        """
        if not text:
            return ""
        
        text = text.lower()
        
        # Common Department 56 normalizations
        text = text.replace("department 56", "dept 56")
        text = text.replace("dept.", "dept")
        text = text.replace("'s", "s")
        text = text.replace("'", "")
        text = text.replace('"', '')
        
        # Remove most punctuation but keep hyphens and periods in SKUs
        text = re.sub(r'[^\w\s\-\.]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def match(self, query_name: str, query_sku: Optional[str] = None, 
             min_score: float = 60.0) -> Optional[Tuple[Dict, float]]:
        """
        Find best match for a query item
        
        Args:
            query_name: Item name to search for
            query_sku: Optional SKU for more precise matching
            min_score: Minimum fuzzy match score (0-100)
            
        Returns:
            Tuple of (product_data, confidence_score) or None if no good match
        """
        if not self.search_data:
            return None
        
        normalized_query = self._normalize_text(query_name)
        normalized_sku = self._normalize_text(query_sku) if query_sku else None
        
        # Strategy 1: Try exact SKU match first (highest confidence)
        if normalized_sku:
            for item in self.search_data:
                if item['normalized_sku'] == normalized_sku:
                    print(f"  ✅ Exact SKU match: {item['name']}")
                    return (item['product'], 1.0)
        
        # Strategy 2: Try exact normalized name match
        for item in self.search_data:
            if item['normalized_name'] == normalized_query:
                print(f"  ✅ Exact name match: {item['name']}")
                return (item['product'], 0.95)
        
        # Strategy 3: Fuzzy matching on names
        names = [item['normalized_name'] for item in self.search_data]
        
        # Use token_sort_ratio for flexibility with word order
        best_match = process.extractOne(
            normalized_query,
            names,
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= min_score:
            best_name, score, best_idx = best_match
            matched_item = self.search_data[best_idx]
            
            # Convert score from 0-100 to 0-1 confidence
            # Scale fuzzy scores: 60 = 0.6, 80 = 0.8, 100 = 0.9
            confidence = min(score / 100.0, 0.9)
            
            print(f"  🎯 Fuzzy match: {matched_item['name']} (score: {score:.1f}, confidence: {confidence:.2f})")
            
            # Bonus confidence if SKU partially matches
            if normalized_sku and matched_item['normalized_sku']:
                if normalized_sku in matched_item['normalized_sku'] or matched_item['normalized_sku'] in normalized_sku:
                    confidence = min(confidence + 0.05, 1.0)
                    print(f"     Bonus: SKU partial match → confidence: {confidence:.2f}")
            
            return (matched_item['product'], confidence)
        
        # No good match found
        print(f"  ❌ No match found above threshold ({min_score})")
        return None
    
    def match_batch(self, items: List[Dict], min_score: float = 60.0) -> List[Dict]:
        """
        Match a batch of items
        
        Args:
            items: List of dicts with 'name' and optional 'sku' keys
            min_score: Minimum fuzzy match score
            
        Returns:
            List of match results with original item, matched product, and confidence
        """
        results = []
        
        for i, item in enumerate(items, 1):
            name = item.get('name', item.get('title', ''))
            sku = item.get('sku', item.get('item_number', item.get('item_no', '')))
            
            print(f"\n{i}/{len(items)} Matching: {name}")
            if sku:
                print(f"  SKU: {sku}")
            
            match_result = self.match(name, sku, min_score)
            
            result = {
                'original_item': item,
                'matched': match_result is not None,
            }
            
            if match_result:
                product, confidence = match_result
                result.update({
                    'matched_product': product,
                    'confidence': confidence,
                    'name_match': product.get('name'),
                    'url': product.get('url')
                })
            
            results.append(result)
        
        return results
    
    def get_stats(self, results: List[Dict]) -> Dict:
        """Calculate matching statistics"""
        total = len(results)
        matched = sum(1 for r in results if r['matched'])
        
        if matched > 0:
            avg_confidence = sum(r['confidence'] for r in results if r['matched']) / matched
            high_confidence = sum(1 for r in results if r.get('confidence', 0) >= 0.8)
        else:
            avg_confidence = 0
            high_confidence = 0
        
        return {
            'total': total,
            'matched': matched,
            'unmatched': total - matched,
            'match_rate': matched / total if total > 0 else 0,
            'avg_confidence': avg_confidence,
            'high_confidence_count': high_confidence,
            'high_confidence_rate': high_confidence / matched if matched > 0 else 0
        }


# Test function
if __name__ == "__main__":
    # Simulated index for testing
    test_index = {
        'https://example.com/product1': {
            'name': "Robbie's Robot Factory",
            'sku': '56.54305',
            'series': 'North Pole Series',
            'url': 'https://example.com/product1'
        },
        'https://example.com/product2': {
            'name': "Santa's Wonderland House",
            'sku': '56.56.720',
            'series': 'North Pole Series',
            'url': 'https://example.com/product2'
        },
        'https://example.com/product3': {
            'name': "Fezziwig's Warehouse",
            'sku': '56.58440',
            'series': 'Dickens Village',
            'url': 'https://example.com/product3'
        }
    }
    
    matcher = FuzzyMatcher(test_index)
    
    # Test items with variations
    test_items = [
        {'name': "Robbie's Robot Factory", 'sku': '56.54305'},
        {'name': "Santa Wonderland House", 'sku': None},  # Missing apostrophe
        {'name': "Fezziwigs Warehouse", 'sku': '56.58440'},  # Different apostrophe
    ]
    
    print("🧪 Testing Fuzzy Matcher\n")
    print("=" * 70)
    
    results = matcher.match_batch(test_items)
    
    print("\n" + "=" * 70)
    print("📊 Results Summary")
    print("=" * 70)
    
    stats = matcher.get_stats(results)
    print(f"Total items: {stats['total']}")
    print(f"Matched: {stats['matched']} ({stats['match_rate']:.1%})")
    print(f"Average confidence: {stats['avg_confidence']:.2f}")
    print(f"High confidence (≥0.8): {stats['high_confidence_count']}")
