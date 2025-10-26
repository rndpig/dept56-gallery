"""
Collection & Series Discovery for Existing Houses

This script analyzes your current houses database and uses the enhanced scraper
to discover series and collection information for items that don't have it yet.

Process:
1. Query existing houses without series/collection data
2. Search for each house using the multi-source scraper
3. Extract discovered series/collection information
4. Stage updates for admin review
"""

import os
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import our enhanced scraper components
from enhanced_sitemap_scraper import SitemapBasedScraper, ProductData
from enhanced_confidence import EnhancedConfidenceCalculator, ConfidenceFactors

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

class CollectionSeriesDiscovery:
    """Discovers and updates collection/series data for existing houses"""
    
    def __init__(self):
        self.scraper = SitemapBasedScraper()
        self.confidence_calculator = EnhancedConfidenceCalculator()
        self.stats = {
            'total_houses': 0,
            'houses_needing_update': 0,
            'successful_discoveries': 0,
            'high_confidence_updates': 0,
            'staged_for_review': 0,
            'errors': 0
        }
    
    async def analyze_existing_houses(self, limit: int = None, dry_run: bool = True) -> Dict:
        """
        Analyze existing houses and discover missing collection/series data
        
        Args:
            limit: Maximum number of houses to process (None = all)
            dry_run: If True, don't actually stage updates
            
        Returns:
            Dictionary with analysis results
        """
        print("🏠 Starting Collection & Series Discovery for Existing Houses")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print(f"   Limit: {limit or 'No limit'}")
        
        # Build scraper indices first
        print("\n📚 Building scraper indices...")
        self.scraper.build_indices(['dept56_retired'], force_rebuild=False)
        
        # Get houses that need collection/series data
        houses_to_analyze = self._get_houses_needing_update(limit)
        self.stats['total_houses'] = len(houses_to_analyze)
        self.stats['houses_needing_update'] = len(houses_to_analyze)
        
        print(f"\n🔍 Found {len(houses_to_analyze)} houses needing collection/series data")
        
        if not houses_to_analyze:
            print("✅ All houses already have complete collection/series data!")
            return self.stats
        
        # Process each house
        discoveries = []
        for i, house in enumerate(houses_to_analyze):
            print(f"\n📦 [{i+1}/{len(houses_to_analyze)}] Processing: {house['name']}")
            
            try:
                discovery = await self._analyze_house(house)
                if discovery:
                    discoveries.append(discovery)
                    self.stats['successful_discoveries'] += 1
                    
                    if discovery['confidence_factors'].overall_confidence >= 0.8:
                        self.stats['high_confidence_updates'] += 1
                
                # Rate limiting
                time.sleep(1.0)
                
            except Exception as e:
                print(f"❌ Error processing {house['name']}: {e}")
                self.stats['errors'] += 1
        
        # Stage discoveries for review
        if discoveries and not dry_run:
            staged_count = await self._stage_discoveries(discoveries)
            self.stats['staged_for_review'] = staged_count
        
        # Print summary
        self._print_summary(discoveries, dry_run)
        
        return {
            'stats': self.stats,
            'discoveries': discoveries
        }
    
    def _get_houses_needing_update(self, limit: int = None) -> List[Dict]:
        """Get houses that are missing collection or series information"""
        try:
            query = supabase.table("houses").select(
                "id, name, year, sku, notes, photo_url"
            )
            
            # Add limit if specified
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Filter houses that need updates
            houses_needing_update = []
            for house in response.data:
                needs_update = False
                
                # Check if series/collection info is missing from notes
                notes = house.get('notes', '') or ''
                notes_lower = notes.lower()
                
                # Simple heuristic: if notes don't contain series/collection keywords
                series_keywords = ['series', 'village', 'collection']
                has_series_info = any(keyword in notes_lower for keyword in series_keywords)
                
                if not has_series_info:
                    needs_update = True
                
                # Also check for obvious missing data (very short or empty notes)
                if len(notes.strip()) < 20:
                    needs_update = True
                
                if needs_update:
                    houses_needing_update.append(house)
            
            return houses_needing_update
            
        except Exception as e:
            print(f"❌ Error fetching houses: {e}")
            return []
    
    async def _analyze_house(self, house: Dict) -> Optional[Dict]:
        """Analyze a single house to discover collection/series data"""
        house_name = house['name']
        house_sku = house.get('sku', '') or ''
        
        # Search using multi-source scraper
        search_results = self.scraper.search_multi_source(house_name, house_sku)
        
        if not search_results:
            print(f"   ❌ No matches found")
            return None
        
        # Calculate confidence
        confidence_factors = self.confidence_calculator.calculate_detailed_confidence(
            house_name, house_sku, search_results
        )
        
        print(f"   📊 Confidence: {confidence_factors.overall_confidence:.2f} ({self.confidence_calculator.get_confidence_category(confidence_factors.overall_confidence)})")
        
        # Extract best discoveries
        best_discoveries = self._extract_best_discoveries(search_results)
        
        if best_discoveries['series'] or best_discoveries['collection']:
            print(f"   🎯 Discovered:")
            if best_discoveries['series']:
                print(f"      Series: {best_discoveries['series']}")
            if best_discoveries['collection']:
                print(f"      Collection: {best_discoveries['collection']}")
            
            return {
                'house': house,
                'discoveries': best_discoveries,
                'search_results': search_results,
                'confidence_factors': confidence_factors,
                'recommendation': self.confidence_calculator.get_recommendation(confidence_factors)
            }
        else:
            print(f"   ⚠️  No series/collection data found")
            return None
    
    def _extract_best_discoveries(self, search_results: Dict) -> Dict:
        """Extract the best series/collection discoveries from search results"""
        series_candidates = []
        collection_candidates = []
        
        for site, result in search_results.items():
            product = result['product']
            
            if product.discovered_series:
                series_candidates.append({
                    'value': product.discovered_series,
                    'source': site,
                    'confidence': result['score']
                })
            
            if product.discovered_collection:
                collection_candidates.append({
                    'value': product.discovered_collection,
                    'source': site,
                    'confidence': result['score']
                })
        
        # Pick best series (highest confidence)
        best_series = ""
        if series_candidates:
            best_series = max(series_candidates, key=lambda x: x['confidence'])['value']
        
        # Pick best collection (highest confidence)
        best_collection = ""
        if collection_candidates:
            best_collection = max(collection_candidates, key=lambda x: x['confidence'])['value']
        
        return {
            'series': best_series,
            'collection': best_collection,
            'series_candidates': series_candidates,
            'collection_candidates': collection_candidates
        }
    
    async def _stage_discoveries(self, discoveries: List[Dict]) -> int:
        """Stage discoveries for admin review in staging table"""
        staged_count = 0
        
        for discovery in discoveries:
            try:
                house = discovery['house']
                best = discovery['discoveries']
                confidence = discovery['confidence_factors']
                
                # Create enhanced notes with discovered information
                current_notes = house.get('notes', '') or ''
                
                # Build new notes section
                new_info_parts = []
                if best['series']:
                    new_info_parts.append(f"Series: {best['series']}")
                if best['collection']:
                    new_info_parts.append(f"Collection: {best['collection']}")
                
                if new_info_parts:
                    new_info = "\\n".join(new_info_parts)
                    
                    # Append to existing notes or create new
                    if current_notes:
                        enhanced_notes = f"{current_notes}\\n\\n{new_info}"
                    else:
                        enhanced_notes = new_info
                    
                    # Stage the update
                    staging_data = {
                        'original_house_id': house['id'],
                        'item_number': house.get('sku', '') or '',
                        'name': house['name'],
                        'intro_year': house.get('year'),
                        'description': enhanced_notes,
                        'discovered_series': best['series'],
                        'discovered_collection': best['collection'],
                        'name_match_score': confidence.name_match_score,
                        'details_confidence_score': confidence.data_completeness,
                        'overall_confidence_score': confidence.overall_confidence,
                        'status': 'pending'
                    }
                    
                    response = supabase.table('staged_houses').insert(staging_data).execute()
                    if response.data:
                        staged_count += 1
                        print(f"   ✅ Staged for review")
                    else:
                        print(f"   ❌ Failed to stage")
                
            except Exception as e:
                print(f"   ❌ Error staging discovery: {e}")
        
        return staged_count
    
    def _print_summary(self, discoveries: List[Dict], dry_run: bool):
        """Print analysis summary"""
        print(f"\n{'='*60}")
        print(f"📊 COLLECTION & SERIES DISCOVERY SUMMARY")
        print(f"{'='*60}")
        
        print(f"Total Houses Analyzed: {self.stats['total_houses']}")
        print(f"Houses Needing Updates: {self.stats['houses_needing_update']}")
        print(f"Successful Discoveries: {self.stats['successful_discoveries']}")
        print(f"High Confidence (≥80%): {self.stats['high_confidence_updates']}")
        print(f"Errors: {self.stats['errors']}")
        
        if not dry_run:
            print(f"Staged for Review: {self.stats['staged_for_review']}")
        
        # Show confidence distribution
        if discoveries:
            print(f"\\n📈 Confidence Distribution:")
            excellent = sum(1 for d in discoveries if d['confidence_factors'].overall_confidence >= 0.9)
            good = sum(1 for d in discoveries if 0.8 <= d['confidence_factors'].overall_confidence < 0.9)
            fair = sum(1 for d in discoveries if 0.7 <= d['confidence_factors'].overall_confidence < 0.8)
            poor = sum(1 for d in discoveries if d['confidence_factors'].overall_confidence < 0.7)
            
            print(f"   Excellent (≥90%): {excellent}")
            print(f"   Good (80-89%): {good}")
            print(f"   Fair (70-79%): {fair}")
            print(f"   Poor (<70%): {poor}")
        
        # Show top discoveries
        if discoveries:
            print(f"\\n🎯 Top Discoveries:")
            sorted_discoveries = sorted(discoveries, 
                                      key=lambda x: x['confidence_factors'].overall_confidence, 
                                      reverse=True)
            
            for i, discovery in enumerate(sorted_discoveries[:5]):
                house = discovery['house']
                best = discovery['discoveries']
                conf = discovery['confidence_factors'].overall_confidence
                
                print(f"   {i+1}. {house['name']} ({conf:.2f})")
                if best['series']:
                    print(f"      Series: {best['series']}")
                if best['collection']:
                    print(f"      Collection: {best['collection']}")
        
        print(f"\\n{'='*60}")


# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover collection/series data for existing houses')
    parser.add_argument('--limit', type=int, help='Limit number of houses to process')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t stage updates, just analyze')
    parser.add_argument('--force-rebuild', action='store_true', help='Force rebuild scraper indices')
    
    args = parser.parse_args()
    
    discovery = CollectionSeriesDiscovery()
    
    # Force rebuild indices if requested
    if args.force_rebuild:
        print("🔄 Force rebuilding scraper indices...")
        discovery.scraper.build_indices(['dept56_retired'], force_rebuild=True)
    
    # Run analysis
    results = await discovery.analyze_existing_houses(
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    # Save results to file for review
    if results['discoveries']:
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"collection_series_discovery_{timestamp}.json"
        
        # Convert data for JSON serialization
        json_results = {
            'stats': results['stats'],
            'discoveries': [
                {
                    'house_name': d['house']['name'],
                    'house_id': d['house']['id'],
                    'discovered_series': d['discoveries']['series'],
                    'discovered_collection': d['discoveries']['collection'],
                    'confidence': d['confidence_factors'].overall_confidence,
                    'recommendation': d['recommendation']
                }
                for d in results['discoveries']
            ]
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())