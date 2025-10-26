"""
Complete Multi-Source Scraper Integration

This script demonstrates the full enhanced scraping workflow:
1. Multi-source scraping with confidence scoring
2. House-accessory linking
3. Collection/series discovery
4. Staging for admin review

Usage Examples:
- python enhanced_scraper_integration.py --test-houses --limit 3
- python enhanced_scraper_integration.py --test-accessories --dry-run
- python enhanced_scraper_integration.py --discover-collections --limit 10
"""

import os
import asyncio
import argparse
from typing import List, Dict, Optional
from datetime import datetime

# Import our enhanced components
from enhanced_sitemap_scraper import SitemapBasedScraper, ProductData
from enhanced_confidence import EnhancedConfidenceCalculator, ConfidenceFactors
from house_accessory_linker import HouseAccessoryLinker, AccessoryData, LinkingMatch
from collection_series_discovery import CollectionSeriesDiscovery

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    exit(1)

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class EnhancedScraperWorkflow:
    """Complete enhanced scraper workflow"""
    
    def __init__(self):
        self.scraper = SitemapBasedScraper()
        self.confidence_calculator = EnhancedConfidenceCalculator()
        self.house_linker = HouseAccessoryLinker()
        self.collection_discovery = CollectionSeriesDiscovery()
    
    async def initialize(self):
        """Initialize all components"""
        print("🚀 Initializing Enhanced Scraper Workflow...")
        
        # Build scraper indices
        print("📚 Building sitemap indices...")
        self.scraper.build_indices(['dept56_retired'], force_rebuild=False)
        
        # Load house cache for linking
        print("🏠 Loading house cache for linking...")
        await self.house_linker.load_houses_cache()
        
        print("✅ Initialization complete!")
    
    async def test_house_enhancement(self, house_names: List[str]) -> Dict:
        """Test enhanced scraping for houses"""
        print(f"\n🏠 Testing House Enhancement for {len(house_names)} houses...")
        
        results = []
        
        for i, house_name in enumerate(house_names):
            print(f"\n[{i+1}/{len(house_names)}] Processing: {house_name}")
            
            try:
                # Search multi-source
                search_results = self.scraper.search_multi_source(house_name)
                
                if search_results:
                    # Calculate confidence
                    confidence = self.confidence_calculator.calculate_detailed_confidence(
                        house_name, "", search_results
                    )
                    
                    print(f"   📊 Confidence: {confidence.overall_confidence:.2f} ({self.confidence_calculator.get_confidence_category(confidence.overall_confidence)})")
                    print(f"   🎯 Recommendation: {self.confidence_calculator.get_recommendation(confidence)}")
                    
                    # Extract best result
                    best_result = max(search_results.values(), key=lambda x: x['score'])
                    product = best_result['product']
                    
                    result = {
                        'name': house_name,
                        'found_name': product.name,
                        'confidence': confidence.overall_confidence,
                        'recommendation': self.confidence_calculator.get_recommendation(confidence),
                        'discovered_series': product.discovered_series,
                        'discovered_collection': product.discovered_collection,
                        'sources': list(search_results.keys()),
                        'confidence_breakdown': confidence.to_dict()
                    }
                    
                    results.append(result)
                    
                    if product.discovered_series:
                        print(f"   📚 Series: {product.discovered_series}")
                    if product.discovered_collection:
                        print(f"   📦 Collection: {product.discovered_collection}")
                else:
                    print(f"   ❌ No matches found")
                    results.append({
                        'name': house_name,
                        'found_name': None,
                        'confidence': 0.0,
                        'recommendation': 'NOT_FOUND'
                    })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'name': house_name,
                    'error': str(e)
                })
        
        return {'houses': results}
    
    async def test_accessory_linking(self, accessory_names: List[str]) -> Dict:
        """Test accessory to house linking"""
        print(f"\n🎯 Testing Accessory Linking for {len(accessory_names)} accessories...")
        
        results = []
        
        for i, acc_name in enumerate(accessory_names):
            print(f"\n[{i+1}/{len(accessory_names)}] Processing: {acc_name}")
            
            try:
                # Search for accessory details
                search_results = self.scraper.search_multi_source(acc_name)
                
                if search_results:
                    # Get best result
                    best_result = max(search_results.values(), key=lambda x: x['score'])
                    product = best_result['product']
                    
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
                    house_matches = await self.house_linker.find_compatible_houses(accessory_data)
                    
                    print(f"   🔗 Found {len(house_matches)} compatible houses")
                    
                    if house_matches:
                        best_match = house_matches[0]
                        print(f"   🎯 Best match: {best_match.house.name} (Score: {best_match.match_score:.2f})")
                        print(f"   📝 Reasons: {', '.join(best_match.match_reasons[:2])}")
                    
                    result = {
                        'name': acc_name,
                        'found_name': product.name,
                        'discovered_series': product.discovered_series,
                        'discovered_collection': product.discovered_collection,
                        'compatible_houses': [
                            {
                                'house_name': match.house.name,
                                'match_score': match.match_score,
                                'confidence_level': match.confidence_level,
                                'reasons': match.match_reasons
                            }
                            for match in house_matches[:3]
                        ]
                    }
                    
                    results.append(result)
                else:
                    print(f"   ❌ No accessory data found")
                    results.append({
                        'name': acc_name,
                        'found_name': None,
                        'compatible_houses': []
                    })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'name': acc_name,
                    'error': str(e)
                })
        
        return {'accessories': results}
    
    async def run_collection_discovery(self, limit: int = None, dry_run: bool = True) -> Dict:
        """Run collection/series discovery on existing houses"""
        print(f"\n📚 Running Collection/Series Discovery...")
        
        return await self.collection_discovery.analyze_existing_houses(limit, dry_run)
    
    def print_summary_report(self, results: Dict):
        """Print a comprehensive summary report"""
        print(f"\n{'='*80}")
        print(f"📊 ENHANCED SCRAPER WORKFLOW SUMMARY")
        print(f"{'='*80}")
        
        if 'houses' in results:
            houses = results['houses']
            print(f"\n🏠 HOUSE ENHANCEMENT RESULTS:")
            print(f"   Total Processed: {len(houses)}")
            
            successful = [h for h in houses if h.get('confidence', 0) > 0]
            high_confidence = [h for h in successful if h.get('confidence', 0) >= 0.8]
            
            print(f"   Successful Matches: {len(successful)}")
            print(f"   High Confidence (≥80%): {len(high_confidence)}")
            
            if successful:
                print(f"\\n   Top Results:")
                for house in sorted(successful, key=lambda x: x.get('confidence', 0), reverse=True)[:3]:
                    print(f"     • {house['name']} → {house.get('found_name', 'N/A')}")
                    print(f"       Confidence: {house.get('confidence', 0):.2f} ({house.get('recommendation', 'N/A')})")
                    if house.get('discovered_series'):
                        print(f"       Series: {house['discovered_series']}")
        
        if 'accessories' in results:
            accessories = results['accessories']
            print(f"\\n🎯 ACCESSORY LINKING RESULTS:")
            print(f"   Total Processed: {len(accessories)}")
            
            successful = [a for a in accessories if a.get('compatible_houses')]
            well_linked = [a for a in successful if len(a.get('compatible_houses', [])) >= 2]
            
            print(f"   Successfully Linked: {len(successful)}")
            print(f"   Well Linked (≥2 houses): {len(well_linked)}")
            
            if successful:
                print(f"\\n   Best Linking Examples:")
                for acc in sorted(successful, key=lambda x: len(x.get('compatible_houses', [])), reverse=True)[:3]:
                    print(f"     • {acc['name']}")
                    houses = acc.get('compatible_houses', [])[:2]
                    for house in houses:
                        print(f"       → {house['house_name']} (Score: {house['match_score']:.2f})")
        
        if 'stats' in results:
            stats = results['stats']
            print(f"\\n📚 COLLECTION DISCOVERY RESULTS:")
            print(f"   Houses Analyzed: {stats.get('total_houses', 0)}")
            print(f"   Successful Discoveries: {stats.get('successful_discoveries', 0)}")
            print(f"   High Confidence Updates: {stats.get('high_confidence_updates', 0)}")
            print(f"   Staged for Review: {stats.get('staged_for_review', 0)}")
        
        print(f"\\n{'='*80}")


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Enhanced Department 56 Scraper Integration')
    
    parser.add_argument('--test-houses', action='store_true', help='Test house enhancement')
    parser.add_argument('--test-accessories', action='store_true', help='Test accessory linking')
    parser.add_argument('--discover-collections', action='store_true', help='Run collection discovery')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of items to process')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t stage updates, just analyze')
    
    args = parser.parse_args()
    
    # Initialize workflow
    workflow = EnhancedScraperWorkflow()
    await workflow.initialize()
    
    results = {}
    
    # Test houses
    if args.test_houses:
        test_houses = [
            "Robbie's Robot Factory",
            "Santa's Wonderland House", 
            "Christmas Carol Cottages",
            "Fezziwig's Warehouse"
        ][:args.limit]
        
        house_results = await workflow.test_house_enhancement(test_houses)
        results.update(house_results)
    
    # Test accessories
    if args.test_accessories:
        test_accessories = [
            "Village Animated Neon Sign",
            "Santa's Workshop Sign",
            "Christmas Tree Lot",
            "Snow Village Fence"
        ][:args.limit]
        
        accessory_results = await workflow.test_accessory_linking(test_accessories)
        results.update(accessory_results)
    
    # Collection discovery
    if args.discover_collections:
        discovery_results = await workflow.run_collection_discovery(args.limit, args.dry_run)
        results.update(discovery_results)
    
    # Print summary
    if results:
        workflow.print_summary_report(results)
        
        # Save results
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"enhanced_scraper_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results saved to: {results_file}")
    else:
        print("⚠️ No operations selected. Use --help for options.")

if __name__ == "__main__":
    asyncio.run(main())