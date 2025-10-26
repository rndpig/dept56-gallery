"""
House-Accessory Linking Engine

Automatically links accessories to appropriate houses using multiple strategies:
1. Series/Collection matching - items from same series/collection
2. Name pattern matching - accessories with house names in them
3. Description mining - "goes with", "coordinates with", etc.
4. SKU pattern analysis - similar item numbers
5. Year proximity - introduced in similar years
6. Replacements.com cross-references

This is critical for accessories since product pages don't explicitly show relationships.
"""

import os
import re
import asyncio
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime

try:
    from rapidfuzz import fuzz
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

@dataclass
class HouseData:
    """House information for linking"""
    id: str
    name: str
    year: Optional[int]
    sku: str
    notes: str
    series: str = ""
    collection: str = ""

@dataclass
class AccessoryData:
    """Accessory information for linking"""
    name: str
    item_number: str
    intro_year: Optional[int]
    description: str
    discovered_series: str = ""
    discovered_collection: str = ""
    source_site: str = ""

@dataclass
class LinkingMatch:
    """Represents a potential house-accessory link"""
    house: HouseData
    accessory: AccessoryData
    match_score: float
    match_reasons: List[str] = field(default_factory=list)
    confidence_level: str = ""

class HouseAccessoryLinker:
    """Engine for automatically linking accessories to houses"""
    
    def __init__(self):
        self.houses_cache = []
        self.linking_patterns = self._initialize_linking_patterns()
        
    def _initialize_linking_patterns(self) -> Dict:
        """Initialize patterns for description mining"""
        return {
            'compatibility_phrases': [
                r'goes with (.+?)(?:\.|$)',
                r'coordinates with (.+?)(?:\.|$)',
                r'pairs with (.+?)(?:\.|$)',
                r'complements (.+?)(?:\.|$)',
                r'designed for (.+?)(?:\.|$)',
                r'perfect for (.+?)(?:\.|$)',
                r'matches (.+?)(?:\.|$)',
                r'compatible with (.+?)(?:\.|$)'
            ],
            'inclusion_phrases': [
                r'includes (.+?)(?:\.|$)',
                r'comes with (.+?)(?:\.|$)',
                r'features (.+?)(?:\.|$)',
                r'contains (.+?)(?:\.|$)'
            ],
            'accessory_keywords': [
                'accessory', 'figure', 'figurine', 'tree', 'fence', 'sign', 
                'light', 'lamp', 'car', 'truck', 'sleigh', 'sled', 'animal',
                'person', 'people', 'snow', 'decoration', 'ornament'
            ],
            'house_keywords': [
                'house', 'building', 'church', 'shop', 'store', 'factory', 
                'mill', 'barn', 'cottage', 'manor', 'castle', 'tower',
                'station', 'depot', 'inn', 'hotel', 'school', 'hospital'
            ]
        }
    
    async def load_houses_cache(self):
        """Load all houses into memory for fast matching"""
        try:
            response = supabase.table("houses").select(
                "id, name, year, sku, notes"
            ).execute()
            
            self.houses_cache = []
            for house_data in response.data or []:
                # Extract series/collection from notes
                notes = house_data.get('notes', '') or ''
                series, collection = self._extract_series_collection_from_notes(notes)
                
                house = HouseData(
                    id=house_data['id'],
                    name=house_data['name'],
                    year=house_data.get('year'),
                    sku=house_data.get('sku', '') or '',
                    notes=notes,
                    series=series,
                    collection=collection
                )
                self.houses_cache.append(house)
            
            print(f"📚 Loaded {len(self.houses_cache)} houses for linking")
            
        except Exception as e:
            print(f"❌ Error loading houses: {e}")
            self.houses_cache = []
    
    def _extract_series_collection_from_notes(self, notes: str) -> Tuple[str, str]:
        """Extract series and collection info from house notes"""
        notes_lower = notes.lower()
        series = ""
        collection = ""
        
        # Look for series patterns
        series_patterns = [
            r'series[:\s]+([^.\n]+)',
            r'village[:\s]+([^.\n]+)',
            r'from the ([^.\n]+ (?:series|village|collection))'
        ]
        
        for pattern in series_patterns:
            match = re.search(pattern, notes_lower)
            if match:
                series = match.group(1).strip()
                break
        
        # Look for collection patterns
        collection_patterns = [
            r'collection[:\s]+([^.\n]+)',
            r'part of ([^.\n]+ collection)'
        ]
        
        for pattern in collection_patterns:
            match = re.search(pattern, notes_lower)
            if match:
                collection = match.group(1).strip()
                break
        
        return series, collection
    
    async def find_compatible_houses(self, accessory: AccessoryData) -> List[LinkingMatch]:
        """
        Find houses that are compatible with the given accessory
        
        Args:
            accessory: AccessoryData object
            
        Returns:
            List of LinkingMatch objects sorted by match score
        """
        if not self.houses_cache:
            await self.load_houses_cache()
        
        matches = []
        
        for house in self.houses_cache:
            match_score, reasons = self._calculate_compatibility_score(house, accessory)
            
            if match_score > 0.3:  # Minimum threshold for consideration
                confidence_level = self._determine_confidence_level(match_score)
                
                match = LinkingMatch(
                    house=house,
                    accessory=accessory,
                    match_score=match_score,
                    match_reasons=reasons,
                    confidence_level=confidence_level
                )
                matches.append(match)
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        return matches
    
    def _calculate_compatibility_score(self, house: HouseData, accessory: AccessoryData) -> Tuple[float, List[str]]:
        """Calculate compatibility score between house and accessory"""
        score = 0.0
        reasons = []
        
        # 1. Series/Collection Matching (strongest signal)
        series_score = self._score_series_match(house, accessory)
        if series_score > 0:
            score += series_score * 0.4  # 40% weight
            if series_score >= 0.8:
                reasons.append(f"Same series: {accessory.discovered_series}")
            elif series_score >= 0.5:
                reasons.append(f"Similar series: {house.series} ≈ {accessory.discovered_series}")
        
        collection_score = self._score_collection_match(house, accessory)
        if collection_score > 0:
            score += collection_score * 0.3  # 30% weight
            reasons.append(f"Same collection: {accessory.discovered_collection}")
        
        # 2. Name Pattern Matching
        name_score = self._score_name_patterns(house, accessory)
        if name_score > 0:
            score += name_score * 0.15  # 15% weight
            if name_score >= 0.8:
                reasons.append(f"Name contains house reference")
            else:
                reasons.append(f"Name similarity detected")
        
        # 3. Description Mining
        desc_score = self._score_description_mining(house, accessory)
        if desc_score > 0:
            score += desc_score * 0.1  # 10% weight
            reasons.append(f"Description indicates compatibility")
        
        # 4. Year Proximity
        year_score = self._score_year_proximity(house, accessory)
        if year_score > 0:
            score += year_score * 0.03  # 3% weight
            reasons.append(f"Introduced in similar years")
        
        # 5. SKU Pattern Analysis
        sku_score = self._score_sku_patterns(house, accessory)
        if sku_score > 0:
            score += sku_score * 0.02  # 2% weight
            reasons.append(f"Similar item numbers")
        
        return min(score, 1.0), reasons
    
    def _score_series_match(self, house: HouseData, accessory: AccessoryData) -> float:
        """Score series matching between house and accessory"""
        if not house.series or not accessory.discovered_series:
            return 0.0
        
        # Exact match
        if house.series.lower() == accessory.discovered_series.lower():
            return 1.0
        
        # Fuzzy match
        similarity = fuzz.token_sort_ratio(house.series.lower(), accessory.discovered_series.lower()) / 100
        
        # Require at least 70% similarity for series matching
        return similarity if similarity >= 0.7 else 0.0
    
    def _score_collection_match(self, house: HouseData, accessory: AccessoryData) -> float:
        """Score collection matching"""
        if not house.collection or not accessory.discovered_collection:
            return 0.0
        
        if house.collection.lower() == accessory.discovered_collection.lower():
            return 1.0
        
        similarity = fuzz.token_sort_ratio(house.collection.lower(), accessory.discovered_collection.lower()) / 100
        return similarity if similarity >= 0.7 else 0.0
    
    def _score_name_patterns(self, house: HouseData, accessory: AccessoryData) -> float:
        """Score name pattern matching"""
        house_name_lower = house.name.lower()
        accessory_name_lower = accessory.name.lower()
        
        score = 0.0
        
        # Check if accessory name contains house name (or vice versa)
        if house_name_lower in accessory_name_lower:
            score = max(score, 0.9)
        elif accessory_name_lower in house_name_lower:
            score = max(score, 0.8)
        
        # Check for common keywords
        house_words = set(re.findall(r'\w+', house_name_lower))
        accessory_words = set(re.findall(r'\w+', accessory_name_lower))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'of', 'for', 'with', 'by'}
        house_words -= stop_words
        accessory_words -= stop_words
        
        if house_words and accessory_words:
            common_words = house_words.intersection(accessory_words)
            if common_words:
                # Score based on proportion of common words
                overlap_score = len(common_words) / min(len(house_words), len(accessory_words))
                score = max(score, overlap_score * 0.6)
        
        # Check for specific patterns
        # Example: "Santa's Workshop" house with "Santa's Workshop Sign" accessory
        for house_word in house_words:
            if len(house_word) > 3 and house_word in accessory_name_lower:
                score = max(score, 0.7)
        
        return score
    
    def _score_description_mining(self, house: HouseData, accessory: AccessoryData) -> float:
        """Mine descriptions for compatibility hints"""
        score = 0.0
        
        # Combine all text to search
        accessory_text = f"{accessory.description}".lower()
        house_text = f"{house.name} {house.notes}".lower()
        
        # Look for explicit compatibility phrases
        for pattern in self.linking_patterns['compatibility_phrases']:
            matches = re.findall(pattern, accessory_text, re.IGNORECASE)
            for match in matches:
                # Check if the mentioned item relates to our house
                if fuzz.partial_ratio(match.lower(), house.name.lower()) > 70:
                    score = max(score, 0.9)
                elif any(word in house_text for word in match.lower().split()):
                    score = max(score, 0.6)
        
        # Look for inclusion phrases (accessories that come with houses)
        for pattern in self.linking_patterns['inclusion_phrases']:
            matches = re.findall(pattern, house_text, re.IGNORECASE)
            for match in matches:
                if fuzz.partial_ratio(match.lower(), accessory.name.lower()) > 70:
                    score = max(score, 0.8)
        
        return score
    
    def _score_year_proximity(self, house: HouseData, accessory: AccessoryData) -> float:
        """Score based on introduction year proximity"""
        if not house.year or not accessory.intro_year:
            return 0.0
        
        year_diff = abs(house.year - accessory.intro_year)
        
        # Items introduced in the same year get full score
        if year_diff == 0:
            return 1.0
        # Items within 1 year get high score
        elif year_diff == 1:
            return 0.8
        # Items within 2-3 years get medium score
        elif year_diff <= 3:
            return 0.5
        # Items within 5 years get low score
        elif year_diff <= 5:
            return 0.2
        else:
            return 0.0
    
    def _score_sku_patterns(self, house: HouseData, accessory: AccessoryData) -> float:
        """Score based on SKU/item number patterns"""
        if not house.sku or not accessory.item_number:
            return 0.0
        
        house_sku = house.sku.lower().replace('-', '').replace('.', '')
        acc_sku = accessory.item_number.lower().replace('-', '').replace('.', '')
        
        # Look for common prefixes (e.g., "56.54305" and "56.54306")
        if len(house_sku) >= 6 and len(acc_sku) >= 6:
            if house_sku[:6] == acc_sku[:6]:
                return 0.8
            elif house_sku[:4] == acc_sku[:4]:
                return 0.5
        
        # Fuzzy match on full SKUs
        similarity = fuzz.ratio(house_sku, acc_sku) / 100
        return similarity if similarity >= 0.7 else 0.0
    
    def _determine_confidence_level(self, score: float) -> str:
        """Determine confidence level from score"""
        if score >= 0.85:
            return "VERY_HIGH"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.55:
            return "MEDIUM"
        elif score >= 0.4:
            return "LOW"
        else:
            return "VERY_LOW"
    
    async def suggest_links_for_accessory(self, accessory_name: str, accessory_data: AccessoryData, top_n: int = 5) -> List[LinkingMatch]:
        """
        Get top N house suggestions for an accessory
        
        Args:
            accessory_name: Name for display
            accessory_data: AccessoryData object
            top_n: Number of top matches to return
            
        Returns:
            List of top LinkingMatch objects
        """
        print(f"\n🔗 Finding compatible houses for: {accessory_name}")
        
        matches = await self.find_compatible_houses(accessory_data)
        
        top_matches = matches[:top_n]
        
        if top_matches:
            print(f"   Found {len(matches)} potential matches, showing top {len(top_matches)}:")
            for i, match in enumerate(top_matches):
                print(f"   {i+1}. {match.house.name} (Score: {match.match_score:.2f}, {match.confidence_level})")
                if match.match_reasons:
                    print(f"      Reasons: {', '.join(match.match_reasons[:2])}")
        else:
            print(f"   ❌ No compatible houses found")
        
        return top_matches
    
    async def batch_link_accessories(self, accessories: List[Tuple[str, AccessoryData]]) -> Dict[str, List[LinkingMatch]]:
        """
        Process multiple accessories for house linking
        
        Args:
            accessories: List of (name, AccessoryData) tuples
            
        Returns:
            Dictionary mapping accessory names to their top matches
        """
        print(f"🔗 Processing {len(accessories)} accessories for house linking...")
        
        if not self.houses_cache:
            await self.load_houses_cache()
        
        results = {}
        
        for i, (acc_name, acc_data) in enumerate(accessories):
            print(f"\n[{i+1}/{len(accessories)}] Processing: {acc_name}")
            
            matches = await self.find_compatible_houses(acc_data)
            results[acc_name] = matches[:5]  # Top 5 matches
            
            if matches:
                best_match = matches[0]
                print(f"   🎯 Best match: {best_match.house.name} ({best_match.match_score:.2f})")
            else:
                print(f"   ❌ No matches found")
        
        return results


# Integration with staging system
async def stage_accessory_with_links(accessory_data: AccessoryData, 
                                   house_matches: List[LinkingMatch],
                                   original_accessory_id: str = None) -> bool:
    """
    Stage an accessory with its house link suggestions for admin review
    
    Args:
        accessory_data: The accessory to stage
        house_matches: List of compatible house matches
        original_accessory_id: ID if updating existing accessory
        
    Returns:
        True if successfully staged
    """
    try:
        # Prepare house link suggestions for staging
        suggested_links = []
        for match in house_matches[:3]:  # Top 3 suggestions
            suggested_links.append({
                'house_id': match.house.id,
                'house_name': match.house.name,
                'match_score': match.match_score,
                'confidence_level': match.confidence_level,
                'match_reasons': match.match_reasons
            })
        
        # Stage accessory data
        staging_data = {
            'original_accessory_id': original_accessory_id,
            'item_number': accessory_data.item_number,
            'name': accessory_data.name,
            'intro_year': accessory_data.intro_year,
            'description': accessory_data.description,
            'discovered_series': accessory_data.discovered_series,
            'discovered_collection': accessory_data.discovered_collection,
            'suggested_house_links': suggested_links,  # Store as JSONB
            'status': 'pending'
        }
        
        response = supabase.table('staged_accessories').insert(staging_data).execute()
        
        if response.data:
            print(f"✅ Staged accessory with {len(suggested_links)} house link suggestions")
            return True
        else:
            print(f"❌ Failed to stage accessory")
            return False
            
    except Exception as e:
        print(f"❌ Error staging accessory: {e}")
        return False


# Test function
async def test_house_accessory_linking():
    """Test the house-accessory linking system"""
    linker = HouseAccessoryLinker()
    
    # Test accessories (simulated)
    test_accessories = [
        ("Village Animated Neon Sign", AccessoryData(
            name="Village Animated Neon Sign",
            item_number="56.53320",
            intro_year=2006,
            description="Animated neon sign for your village display",
            discovered_series="North Pole Series",
            source_site="dept56_retired"
        )),
        ("Santa's Workshop Sign", AccessoryData(
            name="Santa's Workshop Sign",
            item_number="56.54100",
            intro_year=2007,
            description="Sign for Santa's Workshop building",
            discovered_series="North Pole Series",
            source_site="dept56_retired"
        )),
        ("Christmas Tree Lot", AccessoryData(
            name="Christmas Tree Lot",
            item_number="56.55000",
            intro_year=2005,
            description="Collection of Christmas trees for village decoration",
            discovered_collection="Village Accessories",
            source_site="dept56_retired"
        ))
    ]
    
    # Test each accessory
    for acc_name, acc_data in test_accessories:
        matches = await linker.suggest_links_for_accessory(acc_name, acc_data, top_n=3)
        
        if matches:
            print(f"\n📋 Top suggestions for {acc_name}:")
            for i, match in enumerate(matches):
                print(f"   {i+1}. {match.house.name}")
                print(f"      Score: {match.match_score:.3f} ({match.confidence_level})")
                print(f"      Reasons: {', '.join(match.match_reasons)}")

if __name__ == "__main__":
    asyncio.run(test_house_accessory_linking())