# Department 56 Web Scraper - Prototype

## Overview
Prototype scraper for enhancing Department 56 gallery data by scraping retiredproducts.department56.com. Uses fuzzy matching to identify items and calculates confidence scores for scraped data quality.

## Features
- 🔍 **Intelligent Search**: Uses fuzzy matching (FuzzyWuzzy) to find best matches
- 📊 **Confidence Scoring**: Calculates reliability scores (0.00-1.00) based on name match and data completeness
- 📝 **Detailed Logging**: Tracks all scraping operations in `scraping_log` table
- 🎯 **Staging System**: Inserts scraped data into `staged_houses` for moderation
- 🤖 **Selenium-based**: Handles JavaScript-rendered content
- ⏱️ **Respectful Scraping**: Built-in delays to avoid overwhelming source sites

## Prerequisites

### 1. Python Environment
Python 3.8 or higher required.

### 2. Chrome Browser
Selenium requires Chrome browser to be installed.

### 3. Supabase Service Role Key
Get your service role key from Supabase:
1. Go to https://supabase.com/dashboard/project/xctottgirqkkmjmutoon/settings/api
2. Copy the **service_role** key (NOT anon key)
3. Add to `.env` file (see setup below)

## Installation

### Step 1: Navigate to scraper directory
```powershell
cd "c:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app\scripts\scraper"
```

### Step 2: Create virtual environment (recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure environment
```powershell
# Copy example config
cp .env.example .env

# Edit .env and add your Supabase service role key
notepad .env
```

Your `.env` should look like:
```
VITE_SUPABASE_URL=https://xctottgirqkkmjmutoon.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... (your actual key)
```

## Usage

### Run Prototype Test
The scraper includes a test mode that scrapes 3 sample items:
```powershell
python dept56_retired_scraper.py
```

This will:
1. Open Chrome browser (visible, not headless)
2. Search for "Robbie's Robot Factory", "Santa's Wonderland House", "Fezziwig's Warehouse"
3. Use fuzzy matching to find best matches
4. Extract details (name, SKU, description, images, year)
5. Calculate confidence scores
6. Insert into `staged_houses` table
7. Log all operations to `scraping_log` table

### Check Results
After running, verify results in Supabase:

**View staged items:**
```sql
SELECT 
  name,
  item_number,
  intro_year,
  overall_confidence_score,
  status,
  created_at
FROM staged_houses
ORDER BY created_at DESC
LIMIT 5;
```

**View scraping logs:**
```sql
SELECT 
  search_query,
  source_site,
  best_match_name,
  best_match_score,
  success,
  execution_time_ms,
  created_at
FROM scraping_log
ORDER BY created_at DESC
LIMIT 10;
```

**Check pending items summary:**
```sql
SELECT * FROM get_pending_items_summary();
```

## How It Works

### 1. Search Phase
- Builds search URL with item name or item number
- Loads search results page with Selenium
- Waits for JavaScript-rendered content to load
- Extracts all product results (up to first 5)

### 2. Fuzzy Matching
- Compares search query against each result title
- Uses `fuzzywuzzy.fuzz.token_sort_ratio()` for scoring
- Selects best match if score >= 0.6 (60%)
- Handles variations in naming (punctuation, word order, etc.)

### 3. Detail Extraction
- Navigates to product detail page
- Extracts: name, SKU, description, images, year
- Handles missing fields gracefully
- Captures all available images

### 4. Confidence Calculation
Weighted scoring system:
- **Name Match** (50%): Fuzzy match score from search
- **Data Completeness** (30%): Percentage of required fields present
- **Multiple Images** (10%): Bonus if >1 image available
- **Has Year** (10%): Bonus if intro_year extracted

Overall score = sum of components (0.00-1.00)

### 5. Staging Insert
- Inserts scraped data into `staged_houses` table
- Sets status to "pending" for moderation
- Stores all confidence scores
- Preserves source URL for verification

### 6. Logging
Every scraping operation is logged with:
- Search query and source site
- Results found count
- Best match details and score
- Success/failure status
- Execution time in milliseconds
- Any errors encountered

## Configuration Options

### Rate Limiting
Edit `REQUEST_DELAY` in `dept56_retired_scraper.py`:
```python
REQUEST_DELAY = 2  # seconds between requests
```

### Headless Mode
For faster scraping without visible browser:
```python
with Dept56RetiredScraper(headless=True) as scraper:
    # ...
```

### Confidence Thresholds
Adjust minimum scores in `_extract_product_details()`:
```python
if best_score >= 0.6:  # Minimum 60% match
```

## Troubleshooting

### Chrome Driver Issues
If you get "chromedriver not found" errors:
```powershell
# Install webdriver-manager (should already be in requirements.txt)
pip install webdriver-manager

# Or manually download chromedriver and set path in .env
```

### Supabase Connection Errors
- Verify your service role key in `.env`
- Check that `staged_houses` and `scraping_log` tables exist
- Ensure RLS policies allow service role access

### No Results Found
- Item might not exist on retiredproducts.department56.com
- Try different search terms
- Check scraping_log for error details

### Low Confidence Scores
This is normal! Confidence indicates data quality:
- **0.80-1.00**: Excellent match, high confidence
- **0.60-0.79**: Good match, worth reviewing
- **0.40-0.59**: Moderate match, needs verification
- **< 0.40**: Poor match, likely incorrect

## Next Steps

### After Successful Prototype Test:
1. **Review Results**: Check staged_houses table for data quality
2. **Adjust Thresholds**: Fine-tune confidence scoring if needed
3. **Build Moderation UI**: Create admin interface in DeptApp.tsx
4. **Expand Sources**: Add dept56.com and replacements.com scrapers
5. **Batch Processing**: Create scripts to scrape all existing items
6. **Relationship Linking**: Implement house-accessory matching

## File Structure
```
scripts/scraper/
├── dept56_retired_scraper.py   # Main scraper with Selenium
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── .env                         # Your actual config (DO NOT COMMIT)
└── README.md                    # This file
```

## Important Notes

### DO NOT COMMIT .env
The `.env` file contains your service role key (full database access). Add to `.gitignore`:
```
scripts/scraper/.env
```

### Respectful Scraping
- Default 2-second delay between requests
- User-agent header identifies as browser
- Handles timeouts gracefully
- Logs all operations for transparency

### Service Role Security
The service role key bypasses RLS policies. Only use in trusted server-side scripts, never in browser/client code.

## Support

For issues or questions:
1. Check `scraping_log` table for error details
2. Review this README for configuration
3. Verify all prerequisites are installed
4. Check Supabase dashboard for table structure

---

**Version**: 0.1.0 (Prototype)  
**Last Updated**: 2024  
**Status**: ✅ Ready for testing
