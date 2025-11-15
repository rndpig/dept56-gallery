/**
 * Client-side enrichment scanner using the search index
 */

export interface EnrichmentOpportunity {
  db_item: {
    id: string;
    name: string;
    year?: number;
    retired_year?: number;
    sku?: string;
    description?: string;
    photo_url?: string;
    collection?: string;
    price?: number;
  };
  matched_item: {
    name: string;
    intro_year?: number;
    retired_year?: number;
    sku: string;
    description: string;
    photo_url: string;
    collection: string;
    images: string[];
    srp?: number;
    url: string;
  };
  match_score: number;
  match_type: 'name' | 'sku';
  enrichments: Array<{
    field: string;
    current: any;
    suggested: any;
    type: 'missing' | 'enhancement';
    images?: string[];
  }>;
  priority: 'high' | 'medium' | 'low';
}

export interface EnrichmentScanResult {
  success: boolean;
  total_items_scanned: number;
  opportunities_found: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  opportunities: EnrichmentOpportunity[];
  generated_at: string;
  search_index_houses: number;
}

// Simple fuzzy matching function
function calculateMatchScore(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().trim();
  const s2 = str2.toLowerCase().trim();
  
  // Exact match
  if (s1 === s2) return 100;
  
  // One contains the other
  if (s1.includes(s2) || s2.includes(s1)) return 85;
  
  // Split into words and check for word matches
  const words1 = s1.split(/\s+/);
  const words2 = s2.split(/\s+/);
  
  let matchingWords = 0;
  const totalWords = Math.max(words1.length, words2.length);
  
  for (const word1 of words1) {
    for (const word2 of words2) {
      if (word1 === word2 || word1.includes(word2) || word2.includes(word1)) {
        matchingWords++;
        break;
      }
    }
  }
  
  return Math.round((matchingWords / totalWords) * 100);
}

function findBestMatch(dbItem: any, searchIndex: any[]): { item: any; score: number; matchType: 'name' | 'sku' } | null {
  let bestMatch = null;
  let bestScore = 0;
  let bestMatchType: 'name' | 'sku' = 'name';
  
  for (const searchItem of searchIndex) {
    // Name-based matching
    const nameScore = calculateMatchScore(dbItem.name || '', searchItem.name || '');
    
    // SKU-based matching (if both have SKUs)
    let skuScore = 0;
    if (dbItem.sku && searchItem.sku) {
      skuScore = calculateMatchScore(dbItem.sku, searchItem.sku);
    }
    
    // Use the better score
    if (skuScore >= 90 && skuScore > nameScore) {
      if (skuScore > bestScore) {
        bestScore = skuScore;
        bestMatch = searchItem;
        bestMatchType = 'sku';
      }
    } else if (nameScore > bestScore) {
      bestScore = nameScore;
      bestMatch = searchItem;
      bestMatchType = 'name';
    }
  }
  
  return bestMatch && bestScore >= 70 ? { item: bestMatch, score: bestScore, matchType: bestMatchType } : null;
}

function detectEnrichments(dbItem: any, matchedItem: any): Array<{
  field: string;
  current: any;
  suggested: any;
  type: 'missing' | 'enhancement';
  images?: string[];
}> {
  const enrichments: Array<{
    field: string;
    current: any;
    suggested: any;
    type: 'missing' | 'enhancement';
    images?: string[];
  }> = [];
  
  // Check introduction year
  if (!dbItem.year && matchedItem.intro_year) {
    enrichments.push({
      field: 'introduction_year',
      current: dbItem.year,
      suggested: matchedItem.intro_year,
      type: 'missing'
    });
  } else if (dbItem.year && matchedItem.intro_year && dbItem.year !== matchedItem.intro_year) {
    enrichments.push({
      field: 'introduction_year',
      current: dbItem.year,
      suggested: matchedItem.intro_year,
      type: 'enhancement'
    });
  }
  
  // Check retired year
  if (!dbItem.retired_year && matchedItem.retired_year) {
    enrichments.push({
      field: 'retired_year',
      current: dbItem.retired_year,
      suggested: matchedItem.retired_year,
      type: 'missing'
    });
  } else if (dbItem.retired_year && matchedItem.retired_year && dbItem.retired_year !== matchedItem.retired_year) {
    enrichments.push({
      field: 'retired_year',
      current: dbItem.retired_year,
      suggested: matchedItem.retired_year,
      type: 'enhancement'
    });
  }
  
  // Check SKU
  if (!dbItem.sku && matchedItem.sku) {
    enrichments.push({
      field: 'sku',
      current: dbItem.sku,
      suggested: matchedItem.sku,
      type: 'missing'
    });
  } else if (dbItem.sku && matchedItem.sku && dbItem.sku !== matchedItem.sku) {
    enrichments.push({
      field: 'sku',
      current: dbItem.sku,
      suggested: matchedItem.sku,
      type: 'enhancement'
    });
  }
  
  // Check description
  if (!dbItem.description && matchedItem.description) {
    enrichments.push({
      field: 'description',
      current: dbItem.description,
      suggested: matchedItem.description,
      type: 'missing'
    });
  }
  
  // Check primary image
  if (!dbItem.photo_url && matchedItem.photo_url) {
    enrichments.push({
      field: 'primary_image',
      current: dbItem.photo_url,
      suggested: matchedItem.photo_url,
      type: 'missing'
    });
  }
  
  // Check collection
  if (!dbItem.collection && matchedItem.collection) {
    enrichments.push({
      field: 'collection',
      current: dbItem.collection,
      suggested: matchedItem.collection,
      type: 'missing'
    });
  }
  
  // Check additional images
  if (matchedItem.images && matchedItem.images.length > 1) {
    enrichments.push({
      field: 'additional_images',
      current: dbItem.photo_url ? 'Single image' : 'No images',
      suggested: `${matchedItem.images.length} images available`,
      type: 'enhancement',
      images: matchedItem.images
    });
  }
  
  // Check retail price
  if (!dbItem.price && matchedItem.srp) {
    enrichments.push({
      field: 'retail_price',
      current: dbItem.price,
      suggested: matchedItem.srp,
      type: 'missing'
    });
  } else if (dbItem.price && matchedItem.srp) {
    try {
      const dbPrice = parseFloat(String(dbItem.price).replace('$', '').replace(',', ''));
      const searchPrice = parseFloat(String(matchedItem.srp).replace('$', '').replace(',', ''));
      if (Math.abs(dbPrice - searchPrice) > 0.01) {
        enrichments.push({
          field: 'retail_price',
          current: `$${dbPrice.toFixed(2)}`,
          suggested: matchedItem.srp,
          type: 'enhancement'
        });
      }
    } catch (error) {
      // Skip if price conversion fails
    }
  }
  
  return enrichments;
}

export async function scanForEnrichments(dbItems: any[]): Promise<EnrichmentScanResult> {
  try {
    // Load the search index
    const response = await fetch('/house_search_index.json');
    if (!response.ok) {
      throw new Error('Failed to load search index');
    }
    const searchIndex = await response.json();
    
    const opportunities: EnrichmentOpportunity[] = [];
    
    for (const dbItem of dbItems) {
      const match = findBestMatch(dbItem, searchIndex);
      
      if (match) {
        const enrichments = detectEnrichments(dbItem, match.item);
        
        if (enrichments.length > 0) {
          // Determine priority based on match score
          let priority: 'high' | 'medium' | 'low' = 'low';
          if (match.score >= 90) {
            priority = 'high';
          } else if (match.score >= 80) {
            priority = 'medium';
          }
          
          opportunities.push({
            db_item: dbItem,
            matched_item: match.item,
            match_score: match.score,
            match_type: match.matchType,
            enrichments,
            priority
          });
        }
      }
    }
    
    // Calculate statistics
    const highPriority = opportunities.filter(opp => opp.priority === 'high').length;
    const mediumPriority = opportunities.filter(opp => opp.priority === 'medium').length;
    const lowPriority = opportunities.filter(opp => opp.priority === 'low').length;
    
    return {
      success: true,
      total_items_scanned: dbItems.length,
      opportunities_found: opportunities.length,
      high_priority: highPriority,
      medium_priority: mediumPriority,
      low_priority: lowPriority,
      opportunities,
      generated_at: new Date().toISOString(),
      search_index_houses: searchIndex.length
    };
    
  } catch (error) {
    console.error('Error in enrichment scan:', error);
    return {
      success: false,
      total_items_scanned: dbItems.length,
      opportunities_found: 0,
      high_priority: 0,
      medium_priority: 0,
      low_priority: 0,
      opportunities: [],
      generated_at: new Date().toISOString(),
      search_index_houses: 0
    };
  }
}