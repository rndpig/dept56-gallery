"""
Collection/Series Bulk Update Tool - DEMO MODE
Shows the interface and functionality with sample data
"""

import asyncio
from typing import List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HouseAnalysis:
    """Results of collection/series analysis for a house"""
    house_id: str
    house_name: str
    house_name_short: str
    current_collection: str
    current_series: str
    scraped_collection: str
    scraped_series: str
    collection_confidence: float
    series_confidence: float
    overall_confidence: float
    source_sites: List[str]
    needs_update: bool

class DemoCollectionUpdater:
    """Demo version with sample data"""
    
    def __init__(self):
        self.high_confidence_threshold = 0.75
        self.medium_confidence_threshold = 0.50
    
    def generate_sample_data(self) -> tuple:
        """Generate sample analysis data"""
        
        # High confidence samples
        high_conf = [
            HouseAnalysis(
                house_id="1", house_name="Santa's Wonderland House", house_name_short="Santa's Wonderland House",
                current_collection="", current_series="", 
                scraped_collection="Christmas Village", scraped_series="Holiday Series",
                collection_confidence=0.8, series_confidence=0.9, overall_confidence=0.87,
                source_sites=["dept56_retired", "dept56_official"], needs_update=True
            ),
            HouseAnalysis(
                house_id="2", house_name="Robbie's Robot Factory", house_name_short="Robbie's Robot Factory",
                current_collection="", current_series="",
                scraped_collection="North Pole", scraped_series="Workshop Series", 
                collection_confidence=0.85, series_confidence=0.8, overall_confidence=0.82,
                source_sites=["dept56_retired", "dept56_official", "replacements"], needs_update=True
            ),
            HouseAnalysis(
                house_id="3", house_name="Gingerbread House with LED Lights", house_name_short="Gingerbread House with LED...",
                current_collection="", current_series="",
                scraped_collection="Sweet Treats", scraped_series="Bakery Series",
                collection_confidence=0.9, series_confidence=0.75, overall_confidence=0.79,
                source_sites=["dept56_retired", "replacements"], needs_update=True
            )
        ]
        
        # Medium confidence samples
        medium_conf = [
            HouseAnalysis(
                house_id="4", house_name="Christmas Carol Cottages Set", house_name_short="Christmas Carol Cottages Set",
                current_collection="", current_series="",
                scraped_collection="Dickens Village", scraped_series="Literary Series",
                collection_confidence=0.7, series_confidence=0.6, overall_confidence=0.65,
                source_sites=["dept56_retired"], needs_update=True
            ),
            HouseAnalysis(
                house_id="5", house_name="Winter Village Church", house_name_short="Winter Village Church", 
                current_collection="", current_series="",
                scraped_collection="Snow Village", scraped_series="",
                collection_confidence=0.6, series_confidence=0.0, overall_confidence=0.58,
                source_sites=["dept56_official"], needs_update=True
            )
        ]
        
        # Low confidence samples
        low_conf = [
            HouseAnalysis(
                house_id="6", house_name="Small Red Barn", house_name_short="Small Red Barn",
                current_collection="", current_series="",
                scraped_collection="", scraped_series="Farm Series",
                collection_confidence=0.0, series_confidence=0.4, overall_confidence=0.35,
                source_sites=["dept56_retired"], needs_update=False
            ),
            HouseAnalysis(
                house_id="7", house_name="Generic House #47", house_name_short="Generic House #47",
                current_collection="", current_series="",
                scraped_collection="", scraped_series="",
                collection_confidence=0.0, series_confidence=0.0, overall_confidence=0.12,
                source_sites=[], needs_update=False
            )
        ]
        
        return high_conf, medium_conf, low_conf
    
    def display_analysis_tables(self, high_conf: List[HouseAnalysis], 
                               medium_conf: List[HouseAnalysis], 
                               low_conf: List[HouseAnalysis]):
        """Display analysis results in organized tables"""
        
        print(f"\n{'='*100}")
        print("🎯 COLLECTION/SERIES ANALYSIS RESULTS (DEMO DATA)")
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
            
            for analysis in low_conf:
                collection = analysis.scraped_collection or "—"
                series = analysis.scraped_series or "—"
                confidence = f"{analysis.overall_confidence:.2f}"
                sources = f"{len(analysis.source_sites)}x"
                
                print(f"{analysis.house_name_short:<32} {collection:<20} {series:<20} {confidence:<6} {sources:<12}")
    
    def display_summary(self, high_conf: List[HouseAnalysis], 
                       medium_conf: List[HouseAnalysis], 
                       low_conf: List[HouseAnalysis]):
        """Display summary statistics"""
        
        total = len(high_conf) + len(medium_conf) + len(low_conf)
        high_needs_update = sum(1 for a in high_conf if a.needs_update)
        medium_needs_update = sum(1 for a in medium_conf if a.needs_update)
        
        print(f"\n{'='*60}")
        print("📊 SUMMARY STATISTICS (DEMO)")
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
    
    def preview_updates(self, analyses: List[HouseAnalysis]) -> int:
        """Preview what updates would be applied"""
        
        updates_to_apply = [a for a in analyses if a.needs_update]
        
        print(f"\n🧪 PREVIEW: Would update {len(updates_to_apply)} houses")
        print("-" * 80)
        
        for analysis in updates_to_apply:
            new_notes = self._build_updated_notes(analysis)
            print(f"House: {analysis.house_name_short}")
            print(f"   New notes: {new_notes}")
            print(f"   Confidence: {analysis.overall_confidence:.2f}")
            print()
            
        return len(updates_to_apply)
    
    def _build_updated_notes(self, analysis: HouseAnalysis) -> str:
        """Build updated notes string with collection/series data"""
        
        additions = []
        if analysis.scraped_collection:
            additions.append(f"Collection: {analysis.scraped_collection}")
        if analysis.scraped_series:
            additions.append(f"Series: {analysis.scraped_series}")
        
        if additions:
            return " | ".join(additions)
        
        return "No collection/series data found"


def main():
    """Demo main function"""
    
    print("🏠 Department 56 Collection/Series Bulk Update Tool - DEMO MODE")
    print("=" * 70)
    print("This demo shows the interface with sample data.")
    print("To run with real data, set up .env file and run the full version.")
    print("=" * 70)
    
    updater = DemoCollectionUpdater()
    
    # Generate sample data
    print("🔍 Generating sample analysis results...")
    high_conf, medium_conf, low_conf = updater.generate_sample_data()
    
    # Display results
    updater.display_analysis_tables(high_conf, medium_conf, low_conf)
    updater.display_summary(high_conf, medium_conf, low_conf)
    
    # Interactive demo
    print(f"\n{'='*60}")
    print("🎛️ DEMO - BULK UPDATE OPTIONS")
    print(f"{'='*60}")
    
    while True:
        print("\nChoose an action:")
        print("1. 🟢 Preview high confidence updates")
        print("2. 🟡 Preview medium confidence updates")
        print("3. 📊 Show detailed analysis")
        print("4. ❌ Exit demo")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            updater.preview_updates(high_conf)
        elif choice == "2":
            updater.preview_updates(medium_conf)
        elif choice == "3":
            print("\n🔍 DETAILED ANALYSIS EXAMPLE:")
            print("-" * 40)
            example = high_conf[0]
            print(f"House: {example.house_name}")
            print(f"Current Collection: {example.current_collection or 'None'}")
            print(f"Current Series: {example.current_series or 'None'}")
            print(f"Scraped Collection: {example.scraped_collection}")
            print(f"Scraped Series: {example.scraped_series}")
            print(f"Collection Confidence: {example.collection_confidence:.2f}")
            print(f"Series Confidence: {example.series_confidence:.2f}")
            print(f"Overall Confidence: {example.overall_confidence:.2f}")
            print(f"Sources: {', '.join(example.source_sites)}")
            print(f"Needs Update: {example.needs_update}")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please enter 1-4.")
    
    print("\n✅ Demo complete!")
    print("\nTo run with your real data:")
    print("1. Set up .env file with Supabase credentials")
    print("2. Run: python scripts\\scraper\\collection_series_bulk_update.py")

if __name__ == "__main__":
    main()