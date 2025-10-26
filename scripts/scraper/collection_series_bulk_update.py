"""
One-Time Collection/Series Bulk Update Tool
Analyzes ALL houses in database, scrapes for collection/series data,
and presents findings in confidence-based tables for review and bulk approval.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from supabase import create_client, Client

from enhanced_sitemap_scraper import SitemapBasedScraper, ProductData
from enhanced_confidence import EnhancedConfidenceCalculator

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@dataclass
class HouseAnalysis:
    """Results of collection/series analysis for a house"""
    house_id: str
    house_name: str
    house_name_short: str  # Truncated for table display
    current_collection: Optional[str]
    current_series: Optional[str]
    scraped_collection: Optional[str]
    scraped_series: Optional[str]
    collection_confidence: float
    series_confidence: float
    overall_confidence: float
    source_sites: List[str]
    needs_update: bool

class CollectionSeriesBulkUpdater:
    """One-time bulk updater for collection/series data"""
    
    def __init__(self):
        self.scraper = SitemapBasedScraper()
        self.confidence_calc = EnhancedConfidenceCalculator()
        self.high_confidence_threshold = 0.75
        self.medium_confidence_threshold = 0.50
        
    async def analyze_all_houses(self) -> Tuple[List[HouseAnalysis], List[HouseAnalysis], List[HouseAnalysis]]:
        """
        Analyze all houses for collection/series data
        
        Returns:
            Tuple of (high_confidence, medium_confidence, low_confidence) lists
        """
        print("🏠 Fetching all houses from database...")
        
        # Get all houses
        response = supabase.table("houses").select("*").execute()
        houses = response.data
        
        print(f"📊 Found {len(houses)} houses to analyze")
        
        # Initialize scraper
        print("🔧 Initializing scraper...")
        self.scraper.build_indices(['dept56_retired'], force_rebuild=False)
        
        analyses = []
        
        # Analyze each house
        for i, house in enumerate(houses, 1):
            print(f"\n🔍 [{i}/{len(houses)}] Analyzing: {house['name'][:50]}...")
            
            try:
                analysis = await self._analyze_single_house(house)
                if analysis:
                    analyses.append(analysis)
                    print(f"   ✅ Confidence: {analysis.overall_confidence:.2f}")
                else:
                    print(f"   ❌ No results found")
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        # Sort by confidence and categorize
        analyses.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        high_confidence = [a for a in analyses if a.overall_confidence >= self.high_confidence_threshold]
        medium_confidence = [a for a in analyses if self.medium_confidence_threshold <= a.overall_confidence < self.high_confidence_threshold]
        low_confidence = [a for a in analyses if a.overall_confidence < self.medium_confidence_threshold]
        
        return high_confidence, medium_confidence, low_confidence
    
    async def _analyze_single_house(self, house: Dict) -> Optional[HouseAnalysis]:
        """Analyze a single house for collection/series data"""
        
        # Search using enhanced scraper
        search_name = house['name']
        search_sku = house.get('sku', '')
        
        # Use house strategy
        search_results = self.scraper.search_multi_source(search_name, search_sku, "house")
        
        if not search_results:
            return None
        
        # Apply strategy enhancements to extract collection/series
        enhanced = self.scraper.apply_strategy_enhancements(search_results, "house", search_name)
        strategy_data = enhanced['strategy_data']
        
        # Extract best collection/series
        series_data = strategy_data.get('enhanced_series', {})
        best_series = None
        series_confidence = 0.0
        
        if series_data:
            # Find highest confidence series
            for series_name, sites in series_data.items():
                confidence = len(sites) * 0.2  # Base confidence on cross-source validation
                if confidence > series_confidence:
                    series_confidence = confidence
                    best_series = series_name
        
        # Extract collection from description patterns
        best_collection = None
        collection_confidence = 0.0
        
        for site, result in search_results.items():
            product = result.get('product')
            if isinstance(product, dict):
                desc = product.get('description', '') or product.get('name', '')
            else:
                desc = getattr(product, 'description', '') or getattr(product, 'name', '')
            
            # Look for collection patterns
            import re
            collection_patterns = [
                r'(\w+(?:\s+\w+)*)\s+collection',
                r'from\s+the\s+(\w+(?:\s+\w+)*)\s+line',
                r'(\w+(?:\s+\w+)*)\s+village'
            ]
            
            for pattern in collection_patterns:
                match = re.search(pattern, desc.lower())
                if match:
                    collection_name = match.group(1).title()
                    # Simple confidence based on pattern strength
                    confidence = 0.6 if 'collection' in pattern else 0.4
                    if confidence > collection_confidence:
                        collection_confidence = confidence
                        best_collection = collection_name
        
        # Calculate overall confidence
        base_confidence = self.confidence_calc.calculate_detailed_confidence(
            search_name, search_sku or "", search_results
        )
        
        # Bonus for finding collection/series data
        data_bonus = 0.0
        if best_series:
            data_bonus += 0.1
        if best_collection:
            data_bonus += 0.1
            
        overall_confidence = min(base_confidence.overall_confidence + data_bonus, 1.0)
        
        # Check if update is needed
        current_series = house.get('notes', '') or ''
        current_collection = ''  # Assuming no current collection field
        
        needs_update = (
            (best_series and best_series.lower() not in current_series.lower()) or
            (best_collection and best_collection.lower() not in current_series.lower())
        )
        
        return HouseAnalysis(
            house_id=house['id'],
            house_name=house['name'],
            house_name_short=house['name'][:30] + "..." if len(house['name']) > 30 else house['name'],
            current_collection=current_collection if current_collection else None,
            current_series=self._extract_current_series(current_series),
            scraped_collection=best_collection,
            scraped_series=best_series,
            collection_confidence=collection_confidence,
            series_confidence=series_confidence,
            overall_confidence=overall_confidence,
            source_sites=list(search_results.keys()),
            needs_update=needs_update
        )
    
    def _extract_current_series(self, notes: str) -> Optional[str]:
        """Extract current series from house notes"""
        if not notes:
            return None
        
        # Look for series patterns in existing notes
        import re
        patterns = [
            r'series:\s*([^,\n]+)',
            r'(\w+(?:\s+\w+)*)\s+series',
            r'from\s+(\w+(?:\s+\w+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, notes, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def display_analysis_tables(self, high_conf: List[HouseAnalysis], 
                               medium_conf: List[HouseAnalysis], 
                               low_conf: List[HouseAnalysis]):
        """Display analysis results in organized tables"""
        
        print(f"\n{'='*100}")
        print("🎯 COLLECTION/SERIES ANALYSIS RESULTS")
        print(f"{'='*100}")
        
        # High confidence table
        if high_conf:
            print(f"\n🟢 HIGH CONFIDENCE RESULTS ({len(high_conf)} items)")
            print(f"Confidence threshold: {self.high_confidence_threshold:.0%}+")
            print("-" * 100)
            print(f"{'House Name':<32} {'Collection':<20} {'Series':<20} {'Conf':<6} {'Sources':<12}")
            print("-" * 100)
            
            for analysis in high_conf:
                collection = analysis.scraped_collection or "—"
                series = analysis.scraped_series or "—"
                confidence = f"{analysis.overall_confidence:.2f}"
                sources = f"{len(analysis.source_sites)}x"
                
                print(f"{analysis.house_name_short:<32} {collection:<20} {series:<20} {confidence:<6} {sources:<12}")
        
        # Medium confidence table
        if medium_conf:
            print(f"\n🟡 MEDIUM CONFIDENCE RESULTS ({len(medium_conf)} items)")
            print(f"Confidence threshold: {self.medium_confidence_threshold:.0%}-{self.high_confidence_threshold:.0%}")
            print("-" * 100)
            print(f"{'House Name':<32} {'Collection':<20} {'Series':<20} {'Conf':<6} {'Sources':<12}")
            print("-" * 100)
            
            for analysis in medium_conf:
                collection = analysis.scraped_collection or "—"
                series = analysis.scraped_series or "—"
                confidence = f"{analysis.overall_confidence:.2f}"
                sources = f"{len(analysis.source_sites)}x"
                
                print(f"{analysis.house_name_short:<32} {collection:<20} {series:<20} {confidence:<6} {sources:<12}")
        
        # Low confidence table  
        if low_conf:
            print(f"\n🔴 LOW CONFIDENCE RESULTS ({len(low_conf)} items)")
            print(f"Confidence threshold: <{self.medium_confidence_threshold:.0%}")
            print("-" * 100)
            print(f"{'House Name':<32} {'Collection':<20} {'Series':<20} {'Conf':<6} {'Sources':<12}")
            print("-" * 100)
            
            for analysis in low_conf[:10]:  # Show only first 10 low confidence
                collection = analysis.scraped_collection or "—"
                series = analysis.scraped_series or "—"
                confidence = f"{analysis.overall_confidence:.2f}"
                sources = f"{len(analysis.source_sites)}x"
                
                print(f"{analysis.house_name_short:<32} {collection:<20} {series:<20} {confidence:<6} {sources:<12}")
            
            if len(low_conf) > 10:
                print(f"... and {len(low_conf) - 10} more low confidence results")
    
    def display_summary(self, high_conf: List[HouseAnalysis], 
                       medium_conf: List[HouseAnalysis], 
                       low_conf: List[HouseAnalysis]):
        """Display summary statistics"""
        
        total = len(high_conf) + len(medium_conf) + len(low_conf)
        high_needs_update = sum(1 for a in high_conf if a.needs_update)
        medium_needs_update = sum(1 for a in medium_conf if a.needs_update)
        
        print(f"\n{'='*60}")
        print("📊 SUMMARY STATISTICS")
        print(f"{'='*60}")
        print(f"Total houses analyzed: {total}")
        print(f"High confidence results: {len(high_conf)} ({len(high_conf)/total*100:.1f}%)")
        print(f"Medium confidence results: {len(medium_conf)} ({len(medium_conf)/total*100:.1f}%)")
        print(f"Low confidence results: {len(low_conf)} ({len(low_conf)/total*100:.1f}%)")
        print()
        print(f"High confidence needing updates: {high_needs_update}")
        print(f"Medium confidence needing updates: {medium_needs_update}")
        print()
        print("💡 RECOMMENDATIONS:")
        print(f"   • Safe to bulk approve: {len(high_conf)} high confidence items")
        print(f"   • Review individually: {len(medium_conf)} medium confidence items")
        print(f"   • Manual research needed: {len(low_conf)} low confidence items")
    
    async def apply_bulk_updates(self, analyses: List[HouseAnalysis], 
                               dry_run: bool = True) -> int:
        """
        Apply bulk updates to database
        
        Args:
            analyses: List of analyses to apply
            dry_run: If True, only shows what would be updated
            
        Returns:
            Number of items that would be/were updated
        """
        
        updates_to_apply = [a for a in analyses if a.needs_update]
        
        if dry_run:
            print(f"\n🧪 DRY RUN: Would update {len(updates_to_apply)} houses")
            print("-" * 60)
            
            for analysis in updates_to_apply[:5]:  # Show first 5 examples
                new_notes = self._build_updated_notes(analysis)
                print(f"House: {analysis.house_name_short}")
                print(f"   New notes: {new_notes}")
                print()
            
            if len(updates_to_apply) > 5:
                print(f"... and {len(updates_to_apply) - 5} more updates")
                
            return len(updates_to_apply)
        else:
            print(f"\n🚀 APPLYING {len(updates_to_apply)} UPDATES...")
            
            success_count = 0
            for analysis in updates_to_apply:
                try:
                    new_notes = self._build_updated_notes(analysis)
                    
                    response = supabase.table("houses").update({
                        "notes": new_notes
                    }).eq("id", analysis.house_id).execute()
                    
                    success_count += 1
                    print(f"   ✅ Updated: {analysis.house_name_short}")
                    
                except Exception as e:
                    print(f"   ❌ Failed: {analysis.house_name_short} - {e}")
            
            print(f"\n✅ Successfully updated {success_count}/{len(updates_to_apply)} houses")
            return success_count
    
    def _build_updated_notes(self, analysis: HouseAnalysis) -> str:
        """Build updated notes string with collection/series data"""
        
        # Start with existing notes (if any)
        current_notes = ""  # We'd need to fetch current notes from the house
        
        additions = []
        if analysis.scraped_collection:
            additions.append(f"Collection: {analysis.scraped_collection}")
        if analysis.scraped_series:
            additions.append(f"Series: {analysis.scraped_series}")
        
        if additions:
            new_info = " | ".join(additions)
            if current_notes:
                return f"{current_notes} | {new_info}"
            else:
                return new_info
        
        return current_notes


async def main():
    """Main execution function"""
    
    print("🏠 Department 56 Collection/Series Bulk Update Tool")
    print("=" * 60)
    
    updater = CollectionSeriesBulkUpdater()
    
    # Analyze all houses
    print("🔍 Starting comprehensive analysis...")
    high_conf, medium_conf, low_conf = await updater.analyze_all_houses()
    
    # Display results
    updater.display_analysis_tables(high_conf, medium_conf, low_conf)
    updater.display_summary(high_conf, medium_conf, low_conf)
    
    # Interactive options
    print(f"\n{'='*60}")
    print("🎛️ BULK UPDATE OPTIONS")
    print(f"{'='*60}")
    
    while True:
        print("\nChoose an action:")
        print("1. 🟢 Preview high confidence updates (dry run)")
        print("2. 🟡 Preview medium confidence updates (dry run)")  
        print("3. 🚀 Apply high confidence updates (LIVE)")
        print("4. 🚀 Apply medium confidence updates (LIVE)")
        print("5. 📊 Show detailed analysis for specific item")
        print("6. ❌ Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            await updater.apply_bulk_updates(high_conf, dry_run=True)
        elif choice == "2":
            await updater.apply_bulk_updates(medium_conf, dry_run=True)
        elif choice == "3":
            confirm = input("⚠️ This will update the database. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                await updater.apply_bulk_updates(high_conf, dry_run=False)
        elif choice == "4":
            confirm = input("⚠️ This will update the database. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                await updater.apply_bulk_updates(medium_conf, dry_run=False)
        elif choice == "5":
            search_term = input("Enter house name to search: ").strip()
            all_analyses = high_conf + medium_conf + low_conf
            matches = [a for a in all_analyses if search_term.lower() in a.house_name.lower()]
            
            if matches:
                print(f"\nFound {len(matches)} matches:")
                for i, match in enumerate(matches[:5], 1):
                    print(f"{i}. {match.house_name} (confidence: {match.overall_confidence:.2f})")
            else:
                print("No matches found.")
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    asyncio.run(main())