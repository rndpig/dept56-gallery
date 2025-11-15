/**
 * Test script for the enrichment scanner
 */

import { scanForEnrichments } from './src/enrichmentScanner';

// Sample database items for testing
const sampleDbItems = [
  {
    id: '1',
    name: 'Alpine Village Church',
    year: undefined,
    retired_year: undefined,
    sku: undefined,
    description: undefined,
    photo_url: undefined,
    collection: undefined,
    price: undefined
  },
  {
    id: '2', 
    name: 'Christmas Market',
    year: 2010,
    retired_year: undefined,
    sku: '56789',
    description: 'A festive market scene',
    photo_url: 'old-image.jpg',
    collection: 'Heritage Village',
    price: 45.00
  }
];

async function testEnrichmentScanner() {
  console.log('Testing enrichment scanner...');
  
  try {
    const result = await scanForEnrichments(sampleDbItems);
    console.log('Scan result:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Only run if this file is executed directly
if (typeof window === 'undefined') {
  testEnrichmentScanner();
}