"""
Confidence Scoring Enhancements for Multi-Source Scraper

Advanced confidence calculation that considers:
1. Name matching accuracy across sources
2. Data completeness and consistency  
3. Cross-source validation
4. Series/collection discovery
5. Image availability
6. SKU/item number matches
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from rapidfuzz import fuzz
import re
from datetime import datetime

@dataclass
class ConfidenceFactors:
    """Detailed breakdown of confidence calculation factors"""
    name_match_score: float = 0.0
    sku_match_score: float = 0.0
    data_completeness: float = 0.0
    cross_source_validation: float = 0.0
    series_discovery_bonus: float = 0.0
    image_quality_bonus: float = 0.0
    year_consistency: float = 0.0
    description_quality: float = 0.0
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'name_match': self.name_match_score,
            'sku_match': self.sku_match_score,
            'data_completeness': self.data_completeness,
            'cross_source_validation': self.cross_source_validation,
            'series_discovery': self.series_discovery_bonus,
            'image_quality': self.image_quality_bonus,
            'year_consistency': self.year_consistency,
            'description_quality': self.description_quality,
            'overall': self.overall_confidence
        }

class EnhancedConfidenceCalculator:
    """Advanced confidence scoring for multi-source scraping results"""
    
    def __init__(self):
        # Confidence weights (must sum to 1.0)
        self.weights = {
            'name_match': 0.35,      # Primary factor - how well name matches
            'sku_match': 0.15,       # SKU exact matches are very reliable
            'data_completeness': 0.20, # How much useful data we found
            'cross_source_validation': 0.15, # Multiple sources agree
            'series_discovery': 0.05,  # Found series/collection info
            'image_quality': 0.05,    # Good images available
            'year_consistency': 0.03, # Years make sense
            'description_quality': 0.02 # Good description available
        }
    
    def calculate_detailed_confidence(self, 
                                    search_name: str, 
                                    search_sku: str,
                                    multi_source_results: Dict) -> ConfidenceFactors:
        """
        Calculate detailed confidence scores
        
        Args:
            search_name: Original name being searched
            search_sku: Original SKU/item number (if any)
            multi_source_results: Dict of {site_name: {product, score, url}}
            
        Returns:
            ConfidenceFactors with detailed breakdown
        """
        factors = ConfidenceFactors()
        
        if not multi_source_results:
            return factors
        
        # 1. Name Match Scoring
        factors.name_match_score = self._calculate_name_match(search_name, multi_source_results)
        
        # 2. SKU Match Scoring  
        factors.sku_match_score = self._calculate_sku_match(search_sku, multi_source_results)
        
        # 3. Data Completeness
        factors.data_completeness = self._calculate_data_completeness(multi_source_results)
        
        # 4. Cross-Source Validation
        factors.cross_source_validation = self._calculate_cross_source_validation(multi_source_results)
        
        # 5. Series Discovery Bonus
        factors.series_discovery_bonus = self._calculate_series_bonus(multi_source_results)
        
        # 6. Image Quality Bonus
        factors.image_quality_bonus = self._calculate_image_bonus(multi_source_results)
        
        # 7. Year Consistency
        factors.year_consistency = self._calculate_year_consistency(multi_source_results)
        
        # 8. Description Quality
        factors.description_quality = self._calculate_description_quality(multi_source_results)
        
        # Calculate overall confidence
        factors.overall_confidence = (
            factors.name_match_score * self.weights['name_match'] +
            factors.sku_match_score * self.weights['sku_match'] +
            factors.data_completeness * self.weights['data_completeness'] +
            factors.cross_source_validation * self.weights['cross_source_validation'] +
            factors.series_discovery_bonus * self.weights['series_discovery'] +
            factors.image_quality_bonus * self.weights['image_quality'] +
            factors.year_consistency * self.weights['year_consistency'] +
            factors.description_quality * self.weights['description_quality']
        )
        
        # Cap at 1.0
        factors.overall_confidence = min(factors.overall_confidence, 1.0)
        
        return factors
    
    def _calculate_name_match(self, search_name: str, results: Dict) -> float:
        """Calculate name matching confidence"""
        if not results:
            return 0.0
        
        # Get best name match across all sources
        best_score = 0
        scores = []
        
        for result in results.values():
            product = result['product']
            
            # Multiple fuzzy matching strategies
            token_sort = fuzz.token_sort_ratio(search_name.lower(), product.name.lower())
            token_set = fuzz.token_set_ratio(search_name.lower(), product.name.lower())
            partial = fuzz.partial_ratio(search_name.lower(), product.name.lower())
            
            # Take the best score
            best_match = max(token_sort, token_set, partial)
            scores.append(best_match)
            best_score = max(best_score, best_match)
        
        # Average score across sources (with emphasis on best match)
        if scores:
            avg_score = sum(scores) / len(scores)
            # Weighted average: 70% best match, 30% average
            final_score = (best_score * 0.7 + avg_score * 0.3) / 100
        else:
            final_score = 0.0
        
        return min(final_score, 1.0)
    
    def _calculate_sku_match(self, search_sku: str, results: Dict) -> float:
        """Calculate SKU/item number matching confidence"""
        if not search_sku or not results:
            return 0.0
        
        exact_matches = 0
        partial_matches = 0
        total_with_sku = 0
        
        for result in results.values():
            product = result['product']
            if product.item_number:
                total_with_sku += 1
                
                # Exact match (highest confidence)
                if search_sku.lower() == product.item_number.lower():
                    exact_matches += 1
                # Partial match (medium confidence)
                elif (search_sku.lower() in product.item_number.lower() or 
                      product.item_number.lower() in search_sku.lower()):
                    partial_matches += 1
        
        if total_with_sku == 0:
            return 0.0
        
        # Score: exact matches = 1.0, partial = 0.5
        score = (exact_matches + partial_matches * 0.5) / total_with_sku
        return min(score, 1.0)
    
    def _calculate_data_completeness(self, results: Dict) -> float:
        """Calculate how complete the scraped data is"""
        if not results:
            return 0.0
        
        # Required fields for good data
        required_fields = ['item_number', 'description', 'intro_year', 'primary_image_url']
        optional_fields = ['retire_year', 'dimensions', 'discovered_series', 'discovered_collection']
        
        completeness_scores = []
        
        for result in results.values():
            product = result['product']
            
            # Count required fields
            required_count = sum(1 for field in required_fields if getattr(product, field))
            required_score = required_count / len(required_fields)
            
            # Count optional fields (bonus)
            optional_count = sum(1 for field in optional_fields if getattr(product, field))
            optional_bonus = (optional_count / len(optional_fields)) * 0.2  # 20% bonus
            
            total_score = required_score + optional_bonus
            completeness_scores.append(min(total_score, 1.0))
        
        # Return best completeness score
        return max(completeness_scores) if completeness_scores else 0.0
    
    def _calculate_cross_source_validation(self, results: Dict) -> float:
        """Calculate confidence from multiple sources agreeing"""
        if len(results) <= 1:
            return 0.0
        
        # More sources = higher confidence (diminishing returns)
        source_count_score = min(len(results) / 3, 1.0)  # Max score at 3+ sources
        
        # Check agreement between sources
        products = [result['product'] for result in results.values()]
        
        agreement_factors = []
        
        # Name agreement
        names = [p.name for p in products]
        if len(names) > 1:
            name_similarities = []
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    similarity = fuzz.token_sort_ratio(names[i].lower(), names[j].lower()) / 100
                    name_similarities.append(similarity)
            
            avg_name_agreement = sum(name_similarities) / len(name_similarities)
            agreement_factors.append(avg_name_agreement)
        
        # SKU agreement (if available)
        skus = [p.item_number for p in products if p.item_number]
        if len(skus) > 1:
            unique_skus = len(set(skus))
            sku_agreement = 1.0 if unique_skus == 1 else 0.5
            agreement_factors.append(sku_agreement)
        
        # Year agreement
        years = [p.intro_year for p in products if p.intro_year]
        if len(years) > 1:
            year_range = max(years) - min(years)
            year_agreement = 1.0 if year_range <= 1 else max(0.5, 1.0 - (year_range / 10))
            agreement_factors.append(year_agreement)
        
        # Calculate final cross-source score
        if agreement_factors:
            avg_agreement = sum(agreement_factors) / len(agreement_factors)
            cross_source_score = (source_count_score + avg_agreement) / 2
        else:
            cross_source_score = source_count_score * 0.5  # Penalize lack of comparable data
        
        return min(cross_source_score, 1.0)
    
    def _calculate_series_bonus(self, results: Dict) -> float:
        """Bonus for discovering series/collection information"""
        if not results:
            return 0.0
        
        series_found = 0
        collection_found = 0
        
        for result in results.values():
            product = result['product']
            if product.discovered_series:
                series_found += 1
            if product.discovered_collection:
                collection_found += 1
        
        # Score based on discovery rate
        total_sources = len(results)
        series_score = series_found / total_sources
        collection_score = collection_found / total_sources
        
        # Either series OR collection is good, both is better
        combined_score = max(series_score, collection_score)
        if series_score > 0 and collection_score > 0:
            combined_score = min(series_score + collection_score * 0.3, 1.0)
        
        return combined_score
    
    def _calculate_image_bonus(self, results: Dict) -> float:
        """Bonus for finding good images"""
        if not results:
            return 0.0
        
        image_scores = []
        
        for result in results.values():
            product = result['product']
            score = 0.0
            
            # Primary image available
            if product.primary_image_url:
                score += 0.7
            
            # Additional images bonus
            if len(product.additional_images) > 0:
                additional_bonus = min(len(product.additional_images) * 0.1, 0.3)
                score += additional_bonus
            
            image_scores.append(min(score, 1.0))
        
        return max(image_scores) if image_scores else 0.0
    
    def _calculate_year_consistency(self, results: Dict) -> float:
        """Check if years are reasonable and consistent"""
        if not results:
            return 0.0
        
        current_year = datetime.now().year
        dept56_founded = 1976  # Department 56 founded in 1976
        
        year_scores = []
        
        for result in results.values():
            product = result['product']
            score = 0.0
            
            # Check intro year
            if product.intro_year:
                if dept56_founded <= product.intro_year <= current_year:
                    score += 0.5
                else:
                    score -= 0.2  # Penalize impossible years
            
            # Check retire year
            if product.retire_year:
                if (product.intro_year and product.retire_year >= product.intro_year and 
                    product.retire_year <= current_year):
                    score += 0.3
                elif not product.intro_year and dept56_founded <= product.retire_year <= current_year:
                    score += 0.2
            
            # Bonus for having both years
            if product.intro_year and product.retire_year:
                score += 0.2
            
            year_scores.append(max(score, 0.0))
        
        return max(year_scores) if year_scores else 0.0
    
    def _calculate_description_quality(self, results: Dict) -> float:
        """Score quality of product descriptions"""
        if not results:
            return 0.0
        
        desc_scores = []
        
        for result in results.values():
            product = result['product']
            score = 0.0
            
            if product.description:
                desc_len = len(product.description)
                
                # Length scoring
                if desc_len > 200:
                    score += 0.5
                elif desc_len > 100:
                    score += 0.3
                elif desc_len > 50:
                    score += 0.1
                
                # Quality indicators
                desc_lower = product.description.lower()
                quality_indicators = [
                    'department 56', 'village', 'collection', 'series', 
                    'introduced', 'retired', 'dimensions', 'detail'
                ]
                
                indicator_bonus = sum(0.1 for indicator in quality_indicators 
                                    if indicator in desc_lower)
                score += min(indicator_bonus, 0.5)
            
            desc_scores.append(min(score, 1.0))
        
        return max(desc_scores) if desc_scores else 0.0
    
    def get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence level"""
        if confidence >= 0.90:
            return "EXCELLENT"
        elif confidence >= 0.80:
            return "GOOD"
        elif confidence >= 0.70:
            return "FAIR"
        elif confidence >= 0.50:
            return "POOR"
        else:
            return "VERY_POOR"
    
    def get_recommendation(self, factors: ConfidenceFactors) -> str:
        """Get recommendation based on confidence factors"""
        confidence = factors.overall_confidence
        
        if confidence >= 0.90:
            return "AUTO_APPROVE" if factors.cross_source_validation > 0.5 else "RECOMMEND_APPROVE"
        elif confidence >= 0.80:
            return "RECOMMEND_APPROVE"
        elif confidence >= 0.70:
            return "MANUAL_REVIEW"
        elif confidence >= 0.50:
            return "NEEDS_VERIFICATION"
        else:
            return "REJECT"


# Test function
def test_confidence_calculator():
    """Test the enhanced confidence calculator"""
    calculator = EnhancedConfidenceCalculator()
    
    # Mock test data
    from enhanced_sitemap_scraper import ProductData
    
    # Simulate search results
    mock_results = {
        'dept56_retired': {
            'product': ProductData(
                name="Robbie's Robot Factory",
                item_number="56.54305",
                intro_year=2006,
                retire_year=2008,
                description="A whimsical robot factory from the North Pole Series",
                primary_image_url="https://example.com/image1.jpg",
                discovered_series="North Pole Series",
                source_site='dept56_retired'
            ),
            'score': 95,
            'url': 'https://retiredproducts.department56.com/...'
        },
        'dept56_official': {
            'product': ProductData(
                name="Robbie's Robot Factory",
                item_number="56.54305",
                intro_year=2006,
                description="Robot factory building",
                primary_image_url="https://example.com/image2.jpg",
                source_site='dept56_official'
            ),
            'score': 100,
            'url': 'https://department56.com/...'
        }
    }
    
    # Calculate confidence
    factors = calculator.calculate_detailed_confidence(
        "Robbie's Robot Factory",
        "56.54305", 
        mock_results
    )
    
    print("🎯 Enhanced Confidence Analysis:")
    print(f"  Overall Confidence: {factors.overall_confidence:.3f} ({calculator.get_confidence_category(factors.overall_confidence)})")
    print(f"  Recommendation: {calculator.get_recommendation(factors)}")
    print("\n📊 Detailed Breakdown:")
    
    breakdown = factors.to_dict()
    for factor, score in breakdown.items():
        if factor != 'overall':
            print(f"  {factor.replace('_', ' ').title()}: {score:.3f}")

if __name__ == "__main__":
    test_confidence_calculator()