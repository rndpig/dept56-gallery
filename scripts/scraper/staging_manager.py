"""
Staging Manager for Department 56 Web Scraper
Handles database operations for staging scraped data
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class StagingManager:
    """Manages staging of scraped product data"""
    
    def __init__(self):
        self.supabase = supabase
    
    def calculate_overall_confidence(self, matched_product: Dict, match_confidence: float) -> float:
        """
        Calculate overall confidence score based on match quality and data completeness
        
        Args:
            matched_product: Scraped product data
            match_confidence: Confidence from fuzzy matching (0-1)
            
        Returns:
            Overall confidence score (0-1)
        """
        # Start with match confidence (weighted 50%)
        score = match_confidence * 0.5
        
        # Data completeness (weighted 30%)
        required_fields = ['name', 'sku', 'description', 'images']
        present_fields = sum(1 for field in required_fields if matched_product.get(field))
        completeness = (present_fields / len(required_fields)) * 0.3
        score += completeness
        
        # Bonus points (weighted 20% total)
        bonuses = 0
        
        # Has multiple images (5%)
        if len(matched_product.get('images', [])) > 1:
            bonuses += 0.05
        
        # Has year information (5%)
        if matched_product.get('intro_year'):
            bonuses += 0.05
        
        # Has series information (5%)
        if matched_product.get('series'):
            bonuses += 0.05
        
        # Has SRP (5%)
        if matched_product.get('srp'):
            bonuses += 0.05
        
        score += bonuses
        
        # Cap at 1.0
        return round(min(score, 1.0), 2)
    
    def stage_house(self, original_house: Dict, matched_product: Dict, 
                   match_confidence: float) -> Optional[str]:
        """
        Insert scraped house data into staged_houses table
        
        Args:
            original_house: Original house data from your database
            matched_product: Matched product data from scraping
            match_confidence: Confidence score from matching (0-1)
            
        Returns:
            Staged house ID if successful, None otherwise
        """
        try:
            overall_confidence = self.calculate_overall_confidence(
                matched_product, match_confidence
            )
            
            # Prepare staged house data
            staged_house = {
                'original_house_id': original_house.get('id'),
                'item_number': matched_product.get('sku'),
                'name': matched_product.get('name'),
                'intro_year': matched_product.get('intro_year'),
                'retire_year': matched_product.get('retired_year'),  # Note: retire_year not retired_year
                'description': matched_product.get('description'),
                'primary_image_url': matched_product['images'][0] if matched_product.get('images') else None,
                'additional_images': json.dumps(matched_product.get('images', [])),
                'discovered_series': matched_product.get('series'),
                # Note: srp field removed as it doesn't exist in staged_houses table
                'dept56_official_url': matched_product.get('url') if matched_product.get('source') == 'dept56_official' else None,
                'dept56_retired_url': matched_product.get('url') if matched_product.get('source') == 'dept56_retired' else None,
                'replacements_url': matched_product.get('url') if matched_product.get('source') == 'replacements' else None,
                'name_match_score': match_confidence,
                'details_confidence_score': overall_confidence,
                'overall_confidence_score': overall_confidence,
                'status': 'pending'
            }
            
            # Remove None values
            staged_house = {k: v for k, v in staged_house.items() if v is not None}
            
            # Insert into database
            result = self.supabase.table('staged_houses').insert(staged_house).execute()
            
            if result.data:
                staged_id = result.data[0]['id']
                print(f"  💾 Staged to database (ID: {staged_id}, confidence: {overall_confidence:.2f})")
                return staged_id
            else:
                print(f"  ⚠️  No data returned from insert")
                return None
            
        except Exception as e:
            print(f"  ❌ Failed to stage house: {e}")
            return None
    
    def log_scrape(self, search_query: str, item_type: str, source: str,
                  results_found: int, success: bool, best_match_name: Optional[str] = None,
                  best_match_url: Optional[str] = None, best_match_score: Optional[float] = None,
                  error_type: Optional[str] = None, error_message: Optional[str] = None,
                  execution_time_ms: int = 0):
        """Log scraping operation to database"""
        try:
            self.supabase.table('scraping_log').insert({
                'search_query': search_query,
                'item_type': item_type,
                'source_site': source,
                'results_found': results_found,
                'best_match_name': best_match_name,
                'best_match_url': best_match_url,
                'best_match_score': best_match_score,
                'success': success,
                'error_type': error_type,
                'error_message': error_message,
                'execution_time_ms': execution_time_ms
            }).execute()
        except Exception as e:
            print(f"  ⚠️  Failed to log scrape: {e}")
    
    def stage_batch(self, match_results: List[Dict]) -> Dict:
        """
        Stage a batch of matched products
        
        Args:
            match_results: List of match results from FuzzyMatcher
            
        Returns:
            Statistics about staging operation
        """
        stats = {
            'total': len(match_results),
            'staged': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for result in match_results:
            if not result['matched']:
                stats['skipped'] += 1
                continue
            
            original = result['original_item']
            matched = result['matched_product']
            confidence = result['confidence']
            
            staged_id = self.stage_house(original, matched, confidence)
            
            if staged_id:
                stats['staged'] += 1
                
                # Log successful match
                self.log_scrape(
                    search_query=original.get('name', ''),
                    item_type='house',
                    source=matched.get('source', 'dept56_retired'),  # Use valid source
                    results_found=1,
                    success=True,
                    best_match_name=matched.get('name'),
                    best_match_url=matched.get('url'),
                    best_match_score=confidence
                )
            else:
                stats['failed'] += 1
                
                # Log failure
                self.log_scrape(
                    search_query=original.get('name', ''),
                    item_type='house',
                    source='dept56_retired',  # Use valid source
                    results_found=0,
                    success=False,
                    error_type='staging_failed'
                )
        
        return stats
    
    def get_pending_summary(self) -> Dict:
        """Get summary of pending staged items"""
        try:
            result = self.supabase.rpc('get_pending_items_summary').execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return {}
        except Exception as e:
            print(f"⚠️  Failed to get pending summary: {e}")
            return {}
    
    def get_staged_houses(self, status: str = 'pending', limit: int = 10) -> List[Dict]:
        """Retrieve staged houses by status"""
        try:
            result = self.supabase.table('staged_houses')\
                .select('*')\
                .eq('status', status)\
                .order('overall_confidence_score', desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            print(f"⚠️  Failed to retrieve staged houses: {e}")
            return []


# Test function
if __name__ == "__main__":
    print("🧪 Testing Staging Manager\n")
    
    manager = StagingManager()
    
    # Test getting pending summary
    print("📊 Pending items summary:")
    summary = manager.get_pending_summary()
    if summary:
        print(f"  Total pending: {summary.get('total_pending', 0)}")
        print(f"  Houses: {summary.get('houses_pending', 0)}")
        print(f"  Avg confidence: {summary.get('avg_confidence', 0):.2f}")
    else:
        print("  No pending items or function not available")
    
    # Test retrieving staged houses
    print("\n🏠 Recent staged houses:")
    houses = manager.get_staged_houses(limit=5)
    for house in houses:
        print(f"  - {house.get('name', 'Unknown')}")
        print(f"    Confidence: {house.get('overall_confidence_score', 0):.2f}")
        print(f"    Status: {house.get('status', 'unknown')}")
