"""
Scraper Differentiation Logic

This module implements different scraping strategies for houses vs accessories:

HOUSES:
- Focus on series/collection discovery
- Emphasize architectural details
- Look for retirement information
- Extract dimension data

ACCESSORIES:
- Focus on house compatibility
- Look for "goes with" relationships  
- Emphasize linking opportunities
- Check for set completeness
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

from enhanced_sitemap_scraper import ProductData, SitemapBasedScraper
from house_accessory_linker import HouseAccessoryLinker, AccessoryData, LinkingMatch
from enhanced_confidence import EnhancedConfidenceCalculator

@dataclass
class ScrapingStrategy:
    """Defines how to scrape based on item type"""
    focus_areas: List[str]
    required_fields: List[str]
    bonus_fields: List[str]
    confidence_weights: Dict[str, float]
    post_processing: List[str]

class DifferentiatedScraper(SitemapBasedScraper):
    """Enhanced scraper with different strategies for houses vs accessories"""
    
    def __init__(self):
        super().__init__()
        self.house_linker = HouseAccessoryLinker()
        self.confidence_calculator = EnhancedConfidenceCalculator()
        
        # Define strategies
        self.strategies = {
            'house': ScrapingStrategy(
                focus_areas=[
                    'series_discovery',
                    'collection_discovery', 
                    'architectural_details',
                    'retirement_info',
                    'dimensions'
                ],
                required_fields=[
                    'name', 'item_number', 'intro_year', 'description', 'primary_image_url'
                ],
                bonus_fields=[
                    'retire_year', 'dimensions', 'discovered_series', 'discovered_collection'
                ],
                confidence_weights={
                    'series_collection_bonus': 0.15,
                    'architectural_detail_bonus': 0.10,
                    'retirement_info_bonus': 0.05
                },
                post_processing=[
                    'extract_series_collection',
                    'parse_dimensions', 
                    'detect_retirement_info'
                ]
            ),
            'accessory': ScrapingStrategy(
                focus_areas=[
                    'house_compatibility',
                    'relationship_discovery',
                    'set_completeness',
                    'usage_context'
                ],
                required_fields=[
                    'name', 'item_number', 'description', 'primary_image_url'
                ],
                bonus_fields=[
                    'compatible_houses', 'set_info', 'usage_instructions'
                ],
                confidence_weights={
                    'compatibility_bonus': 0.20,
                    'relationship_bonus': 0.15,
                    'set_completeness_bonus': 0.10
                },
                post_processing=[
                    'find_compatible_houses',
                    'extract_relationship_hints',
                    'detect_set_info'
                ]
            )
        }
    
    async def scrape_with_strategy(self, item_name: str, item_number: str = None, item_type: str = "house") -> Dict:
        """
        Scrape using differentiated strategy based on item type
        
        Args:
            item_name: Name to search for
            item_number: Optional SKU
            item_type: "house" or "accessory"
            
        Returns:
            Enhanced results with strategy-specific data
        """
        print(f"🎯 Scraping {item_type.upper()}: {item_name}")
        
        # Get base search results
        search_results = await self.search_multi_source(item_name, item_number, item_type)
        
        if not search_results:
            return {'item_type': item_type, 'results': None}
        
        # Apply strategy-specific enhancements
        strategy = self.strategies[item_type]
        enhanced_results = await self._apply_strategy(search_results, strategy, item_type)
        
        # Calculate strategy-specific confidence
        confidence = self._calculate_strategy_confidence(enhanced_results, strategy, item_name, item_number or "")
        
        return {
            'item_type': item_type,
            'item_name': item_name,
            'search_results': search_results,
            'enhanced_results': enhanced_results,
            'confidence': confidence,
            'strategy_applied': strategy.focus_areas
        }
    
    async def _apply_strategy(self, search_results: Dict, strategy: ScrapingStrategy, item_type: str) -> Dict:
        """Apply strategy-specific post-processing"""
        enhanced = {
            'best_product': None,
            'strategy_data': {}
        }
        
        # Get best result
        if search_results:
            best_result = max(search_results.values(), key=lambda x: x['score'])
            enhanced['best_product'] = best_result['product']
        
        # Apply post-processing based on strategy
        for process in strategy.post_processing:
            if process == 'extract_series_collection':
                enhanced['strategy_data']['series_collection'] = self._extract_enhanced_series_collection(search_results)
            
            elif process == 'parse_dimensions':
                enhanced['strategy_data']['dimensions'] = self._extract_dimensions(search_results)
            
            elif process == 'detect_retirement_info':
                enhanced['strategy_data']['retirement_info'] = self._extract_retirement_info(search_results)
            
            elif process == 'find_compatible_houses':
                enhanced['strategy_data']['compatible_houses'] = await self._find_compatible_houses_for_accessory(enhanced['best_product'])
            
            elif process == 'extract_relationship_hints':
                enhanced['strategy_data']['relationship_hints'] = self._extract_relationship_hints(search_results)
            
            elif process == 'detect_set_info':
                enhanced['strategy_data']['set_info'] = self._detect_set_info(search_results)
        
        return enhanced
    
    def _extract_enhanced_series_collection(self, search_results: Dict) -> Dict:
        """Enhanced series/collection extraction for houses"""
        series_candidates = {}
        collection_candidates = {}
        
        for site, result in search_results.items():
            product = result['product']
            
            # Collect series info with confidence
            if product.discovered_series:
                if product.discovered_series not in series_candidates:
                    series_candidates[product.discovered_series] = []
                series_candidates[product.discovered_series].append({
                    'site': site,
                    'confidence': result['score']
                })
            
            # Collect collection info
            if product.discovered_collection:
                if product.discovered_collection not in collection_candidates:
                    collection_candidates[product.discovered_collection] = []
                collection_candidates[product.discovered_collection].append({
                    'site': site,
                    'confidence': result['score']
                })
        
        # Rank by cross-source validation
        best_series = self._rank_candidates(series_candidates)
        best_collection = self._rank_candidates(collection_candidates)
        
        return {
            'best_series': best_series,
            'best_collection': best_collection,
            'all_series_candidates': series_candidates,
            'all_collection_candidates': collection_candidates
        }
    
    def _rank_candidates(self, candidates: Dict) -> Optional[Dict]:
        """Rank candidates by cross-source validation and confidence"""
        if not candidates:
            return None
        
        ranked = []
        for name, sources in candidates.items():
            avg_confidence = sum(s['confidence'] for s in sources) / len(sources)
            cross_source_score = len(sources)  # More sources = better
            
            total_score = avg_confidence * 0.7 + cross_source_score * 30  # Favor cross-validation
            
            ranked.append({
                'name': name,
                'total_score': total_score,
                'avg_confidence': avg_confidence,
                'source_count': cross_source_score,
                'sources': sources
            })
        
        ranked.sort(key=lambda x: x['total_score'], reverse=True)
        return ranked[0] if ranked else None
    
    def _extract_dimensions(self, search_results: Dict) -> Dict:
        """Extract dimensional information for houses"""
        dimensions = {}
        
        for site, result in search_results.items():
            product = result['product']
            text = f"{product.description} {product.dimensions}".lower()
            
            # Look for dimension patterns
            patterns = [
                r'(\d+\.?\d*)\s*["\']?\s*[wx]\s*(\d+\.?\d*)\s*["\']?\s*[wx]\s*(\d+\.?\d*)\s*["\']?',  # LxWxH
                r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)',  # Simple LxWxH
                r'dimensions?\s*:?\s*(\d+\.?\d*)["\']?\s*x\s*(\d+\.?\d*)["\']?\s*x\s*(\d+\.?\d*)["\']?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dimensions[site] = {
                        'length': match.group(1),
                        'width': match.group(2), 
                        'height': match.group(3),
                        'raw_text': match.group(0)
                    }
                    break
        
        return dimensions
    
    def _extract_retirement_info(self, search_results: Dict) -> Dict:
        """Extract retirement information for houses"""
        retirement_info = {}
        
        for site, result in search_results.items():
            product = result['product']
            text = f"{product.description}".lower()
            
            # Look for retirement patterns
            patterns = [
                r'retired\s+(?:in\s+)?(\d{4})',
                r'discontinue[d]?\s+(?:in\s+)?(\d{4})',
                r'(?:last\s+)?produced\s+(?:in\s+)?(\d{4})',
                r'(\d{4})\s*-\s*(\d{4})'  # Year range
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 2:  # Year range
                        retirement_info[site] = {
                            'intro_year': match.group(1),
                            'retire_year': match.group(2),
                            'type': 'range'
                        }
                    else:
                        retirement_info[site] = {
                            'retire_year': match.group(1),
                            'type': 'retired'
                        }
                    break
        
        return retirement_info
    
    async def _find_compatible_houses_for_accessory(self, product: ProductData) -> Dict:
        """Find compatible houses for accessories"""
        if not product:
            return {}
        
        # Convert to AccessoryData
        accessory_data = AccessoryData(
            name=product.name,
            item_number=product.item_number,
            intro_year=product.intro_year,
            description=product.description,
            discovered_series=product.discovered_series,
            discovered_collection=product.discovered_collection,
            source_site=product.source_site
        )
        
        # Find compatible houses
        try:
            matches = await self.house_linker.find_compatible_houses(accessory_data)
            
            return {
                'top_matches': [
                    {
                        'house_name': match.house.name,
                        'house_id': match.house.id,
                        'match_score': match.match_score,
                        'confidence_level': match.confidence_level,
                        'reasons': match.match_reasons
                    }
                    for match in matches[:5]
                ],
                'total_matches': len(matches),
                'high_confidence_matches': len([m for m in matches if m.match_score >= 0.7])
            }
        except Exception as e:
            print(f"Error finding compatible houses: {e}")
            return {}
    
    def _extract_relationship_hints(self, search_results: Dict) -> Dict:
        """Extract relationship hints for accessories"""
        hints = {}
        
        patterns = {
            'goes_with': r'goes\s+with\s+([^.]+)',
            'coordinates_with': r'coordinates\s+with\s+([^.]+)',
            'designed_for': r'designed\s+for\s+([^.]+)',
            'complements': r'complements\s+([^.]+)',
            'pairs_with': r'pairs\s+with\s+([^.]+)'
        }
        
        for site, result in search_results.items():
            product = result['product']
            text = product.description.lower()
            
            site_hints = {}
            for hint_type, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    site_hints[hint_type] = matches
            
            if site_hints:
                hints[site] = site_hints
        
        return hints
    
    def _detect_set_info(self, search_results: Dict) -> Dict:
        """Detect set information for accessories"""
        set_info = {}
        
        patterns = {
            'set_of': r'set\s+of\s+(\d+)',
            'includes': r'includes\s+([^.]+)',
            'piece_count': r'(\d+)\s*(?:pc|piece|pcs|pieces)',
            'assortment': r'assortment\s+of\s+([^.]+)'
        }
        
        for site, result in search_results.items():
            product = result['product']
            text = f"{product.name} {product.description}".lower()
            
            site_set_info = {}
            for info_type, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    site_set_info[info_type] = matches
            
            if site_set_info:
                set_info[site] = site_set_info
        
        return set_info
    
    def _calculate_strategy_confidence(self, enhanced_results: Dict, strategy: ScrapingStrategy, 
                                     item_name: str, item_number: str) -> Dict:
        """Calculate confidence with strategy-specific bonuses"""
        
        # Base confidence from standard calculation
        search_results = enhanced_results.get('search_results', {})
        base_confidence = self.confidence_calculator.calculate_detailed_confidence(
            item_name, item_number, search_results
        )
        
        # Strategy-specific bonuses
        strategy_bonus = 0.0
        bonus_details = {}
        
        strategy_data = enhanced_results.get('strategy_data', {})
        
        # Apply strategy-specific bonuses
        for bonus_type, weight in strategy.confidence_weights.items():
            bonus = 0.0
            
            if bonus_type == 'series_collection_bonus':
                series_collection = strategy_data.get('series_collection', {})
                if series_collection.get('best_series') or series_collection.get('best_collection'):
                    bonus = weight
                    
            elif bonus_type == 'architectural_detail_bonus':
                dimensions = strategy_data.get('dimensions', {})
                if dimensions:
                    bonus = weight
                    
            elif bonus_type == 'retirement_info_bonus':
                retirement = strategy_data.get('retirement_info', {})
                if retirement:
                    bonus = weight
                    
            elif bonus_type == 'compatibility_bonus':
                compatible = strategy_data.get('compatible_houses', {})
                if compatible.get('high_confidence_matches', 0) > 0:
                    bonus = weight
                    
            elif bonus_type == 'relationship_bonus':
                hints = strategy_data.get('relationship_hints', {})
                if hints:
                    bonus = weight
                    
            elif bonus_type == 'set_completeness_bonus':
                set_info = strategy_data.get('set_info', {})
                if set_info:
                    bonus = weight
            
            if bonus > 0:
                strategy_bonus += bonus
                bonus_details[bonus_type] = bonus
        
        # Calculate final confidence
        final_confidence = min(base_confidence.overall_confidence + strategy_bonus, 1.0)
        
        return {
            'base_confidence': base_confidence.overall_confidence,
            'strategy_bonus': strategy_bonus,
            'final_confidence': final_confidence,
            'bonus_details': bonus_details,
            'base_breakdown': base_confidence.to_dict()
        }


# Test the differentiated scraper
async def test_differentiated_scraping():
    """Test scraper with different strategies"""
    scraper = DifferentiatedScraper()
    
    # Initialize
    scraper.build_indices(['dept56_retired'], force_rebuild=False)
    await scraper.house_linker.load_houses_cache()
    
    # Test houses
    test_houses = [
        "Robbie's Robot Factory",
        "Santa's Wonderland House"
    ]
    
    # Test accessories  
    test_accessories = [
        "Village Animated Neon Sign",
        "Christmas Tree Lot"
    ]
    
    print("🏠 TESTING HOUSE STRATEGY:")
    for house_name in test_houses:
        result = await scraper.scrape_with_strategy(house_name, item_type="house")
        
        print(f"\\n📦 {house_name}:")
        print(f"   Strategy Focus: {result['strategy_applied']}")
        print(f"   Base Confidence: {result['confidence']['base_confidence']:.2f}")
        print(f"   Strategy Bonus: +{result['confidence']['strategy_bonus']:.2f}")
        print(f"   Final Confidence: {result['confidence']['final_confidence']:.2f}")
        
        strategy_data = result['enhanced_results']['strategy_data']
        if 'series_collection' in strategy_data:
            sc = strategy_data['series_collection']
            if sc.get('best_series'):
                print(f"   🎯 Best Series: {sc['best_series']['name']}")
        
        if 'dimensions' in strategy_data and strategy_data['dimensions']:
            print(f"   📏 Dimensions Found: {len(strategy_data['dimensions'])} sources")
    
    print(f"\\n\\n🎯 TESTING ACCESSORY STRATEGY:")
    for acc_name in test_accessories:
        result = await scraper.scrape_with_strategy(acc_name, item_type="accessory")
        
        print(f"\\n📦 {acc_name}:")
        print(f"   Strategy Focus: {result['strategy_applied']}")
        print(f"   Base Confidence: {result['confidence']['base_confidence']:.2f}")
        print(f"   Strategy Bonus: +{result['confidence']['strategy_bonus']:.2f}")
        print(f"   Final Confidence: {result['confidence']['final_confidence']:.2f}")
        
        strategy_data = result['enhanced_results']['strategy_data']
        if 'compatible_houses' in strategy_data:
            houses = strategy_data['compatible_houses']
            print(f"   🔗 Compatible Houses: {houses.get('total_matches', 0)}")
            print(f"   🎯 High Confidence: {houses.get('high_confidence_matches', 0)}")
        
        if 'relationship_hints' in strategy_data and strategy_data['relationship_hints']:
            print(f"   💡 Relationship Hints Found: {len(strategy_data['relationship_hints'])} sources")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_differentiated_scraping())