"""
Department 56 Data Enhancement Scraper - Main Script
Orchestrates the complete workflow: index building → matching → staging
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from supabase import create_client

from index_builder import IndexBuilder
from fuzzy_matcher import FuzzyMatcher
from staging_manager import StagingManager

load_dotenv()

# Initialize Supabase (using service role for reading your houses)
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class Dept56Scraper:
    """Main scraper orchestrator"""
    
    def __init__(self, use_cached_index: bool = True, min_match_score: float = 60.0):
        """
        Initialize scraper
        
        Args:
            use_cached_index: Whether to use cached product index
            min_match_score: Minimum fuzzy match score (0-100)
        """
        self.use_cached_index = use_cached_index
        self.min_match_score = min_match_score
        self.staging_manager = StagingManager()
        self.index = None
        self.matcher = None
    
    def fetch_houses_from_db(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch houses from your production database
        
        Args:
            limit: Optional limit on number of houses to fetch
            
        Returns:
            List of house dictionaries
        """
        print("📚 Fetching houses from your database...")
        
        try:
            # Try with sku column first (if migration was applied)
            query = supabase.table('houses').select('id, name, sku, year')
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            houses = [{
                'id': h['id'],
                'name': h['name'],
                'sku': h.get('sku'),
                'intro_year': h.get('year')
            } for h in result.data]
            
            print(f"✅ Fetched {len(houses)} houses from database\n")
            return houses
            
        except Exception as e:
            print(f"❌ Error fetching houses: {e}")
            return []
    
    def build_or_load_index(self):
        """Build or load the product index"""
        print("=" * 70)
        print("🏗️  Step 1: Building Product Index")
        print("=" * 70)
        
        builder = IndexBuilder(use_cache=self.use_cached_index)
        self.index = builder.build_index(
            crawl_main=False,  # Start with retired site only for faster testing
            crawl_retired=True
        )
        
        if not self.index:
            raise ValueError("Failed to build product index")
        
        print(f"\n✅ Index ready with {len(self.index)} products\n")
    
    def match_houses(self, houses: List[Dict]) -> List[Dict]:
        """Match houses against the index"""
        print("=" * 70)
        print("🎯 Step 2: Matching Houses Against Index")
        print("=" * 70)
        
        self.matcher = FuzzyMatcher(self.index)
        
        results = self.matcher.match_batch(houses, min_score=self.min_match_score)
        
        # Print matching stats
        stats = self.matcher.get_stats(results)
        print("\n" + "=" * 70)
        print("📊 Matching Statistics")
        print("=" * 70)
        print(f"Total items: {stats['total']}")
        print(f"Matched: {stats['matched']} ({stats['match_rate']:.1%})")
        print(f"Unmatched: {stats['unmatched']}")
        print(f"Average confidence: {stats['avg_confidence']:.2f}")
        print(f"High confidence (≥0.8): {stats['high_confidence_count']} ({stats['high_confidence_rate']:.1%})")
        print("=" * 70 + "\n")
        
        return results
    
    def stage_matches(self, match_results: List[Dict]):
        """Stage matched products to database"""
        print("=" * 70)
        print("💾 Step 3: Staging Matched Products")
        print("=" * 70)
        
        staging_stats = self.staging_manager.stage_batch(match_results)
        
        print("\n" + "=" * 70)
        print("📊 Staging Statistics")
        print("=" * 70)
        print(f"Total: {staging_stats['total']}")
        print(f"Successfully staged: {staging_stats['staged']}")
        print(f"Failed: {staging_stats['failed']}")
        print(f"Skipped (no match): {staging_stats['skipped']}")
        print("=" * 70 + "\n")
        
        return staging_stats
    
    def run(self, limit: Optional[int] = None):
        """
        Run complete scraping workflow
        
        Args:
            limit: Optional limit on number of houses to process
        """
        start_time = time.time()
        
        print("\n" + "=" * 70)
        print("🎄 Department 56 Data Enhancement Scraper")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Using cached index' if self.use_cached_index else 'Building fresh index'}")
        print(f"Min match score: {self.min_match_score}")
        if limit:
            print(f"Limit: {limit} houses")
        print("=" * 70 + "\n")
        
        try:
            # Step 1: Build/load index
            self.build_or_load_index()
            
            # Step 2: Fetch houses from your database
            houses = self.fetch_houses_from_db(limit=limit)
            
            if not houses:
                print("❌ No houses to process")
                return
            
            # Step 3: Match houses against index
            match_results = self.match_houses(houses)
            
            # Step 4: Stage matched products
            staging_stats = self.stage_matches(match_results)
            
            # Final summary
            elapsed = time.time() - start_time
            print("\n" + "=" * 70)
            print("✅ Scraping Complete!")
            print("=" * 70)
            print(f"Execution time: {elapsed:.1f} seconds")
            print(f"Products staged: {staging_stats['staged']}")
            print("\n🔍 Next steps:")
            print("  1. Check Supabase staged_houses table")
            print("  2. Review confidence scores")
            print("  3. Build moderation UI for approval workflow")
            print("=" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Scraping interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Error during scraping: {e}")
            raise


def main():
    """Main entry point with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Department 56 Data Enhancement Scraper')
    parser.add_argument('--rebuild-index', action='store_true',
                       help='Force rebuild of product index (ignore cache)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of houses to process (for testing)')
    parser.add_argument('--min-score', type=float, default=60.0,
                       help='Minimum fuzzy match score (0-100, default: 60)')
    
    args = parser.parse_args()
    
    scraper = Dept56Scraper(
        use_cached_index=not args.rebuild_index,
        min_match_score=args.min_score
    )
    
    scraper.run(limit=args.limit)


if __name__ == "__main__":
    # Quick test mode: process 5 houses with cached index
    scraper = Dept56Scraper(use_cached_index=True, min_match_score=60.0)
    scraper.run(limit=5)
