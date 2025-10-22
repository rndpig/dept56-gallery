# Replacements.com Integration Plan
## Secondary Data Source for Cross-Referencing

### Overview
Replacements.com (https://www.replacements.com) is a major secondary market for Department 56 collectibles. It can serve as a valuable cross-reference source to improve confidence scores and discover additional product information.

### Site Structure Analysis

**URL Pattern:**
```
https://www.replacements.com/china-department-56-[series]/c/[category-id]
https://www.replacements.com/p/department-56-[product-name]/[product-id]
```

**Example URLs:**
- Category: `https://www.replacements.com/china-department-56-north-pole-series/c/110033`
- Product: `https://www.replacements.com/p/department-56-north-pole-series-robbies-robot-factory/dprt54305`

### Data Available
- Product names (often with series prefix)
- Item numbers / SKU
- Current market prices (secondary market value)
- Product images (usually high quality)
- Related items / accessories
- Production years (sometimes)
- Descriptions (limited)

### robots.txt Compliance
```
# Check: curl https://www.replacements.com/robots.txt

User-agent: *
# Note: Check actual robots.txt for current restrictions
# Typical allowances: product pages, category pages
# Typical blocks: /cart, /checkout, /account
```

### Scraping Strategy

#### 1. **Discovery Phase**
```python
# Search via category pages
categories = [
    ('north-pole-series', '110033'),
    ('dickens-village', '110001'),
    ('snow-village', '110002'),
    # etc.
]

for series_name, category_id in categories:
    url = f"https://www.replacements.com/china-department-56-{series_name}/c/{category_id}"
    # Paginate through ?page=N
    # Extract product links
```

#### 2. **Product Parsing**
```python
# Extract from product page:
{
    'name': 'North Pole Series Robbie\'s Robot Factory',
    'sku': 'dprt54305',  # Their internal ID
    'dept56_sku': '54305',  # Actual Department 56 SKU
    'price': 45.00,  # Secondary market value
    'images': ['https://...'],
    'description': '...',
    'year': 2003,  # If available
    'status': 'Retired'
}
```

#### 3. **SKU Matching**
```python
# Extract Department 56 SKU from Replacements SKU
# Pattern: dprt54305 → 54305
# Pattern: dprt56.54305 → 56.54305

def extract_dept56_sku(replacements_sku):
    # Remove dprt prefix
    clean = replacements_sku.replace('dprt', '')
    # Handle dot notation
    if len(clean) > 5 and clean[2] != '.':
        clean = clean[:2] + '.' + clean[2:]
    return clean
```

### Integration with Existing Scraper

#### Database Schema
Already supported in `staged_houses`:
```sql
replacements_url TEXT,  -- URL to replacements.com product page
```

#### Confidence Scoring with Multi-Source
```python
def calculate_multi_source_confidence(sources):
    """
    sources = {
        'dept56_retired': {data},
        'replacements': {data},
        # Future: 'dept56_official': {data}
    }
    """
    base_score = 0
    
    # Single source: max 0.85
    if len(sources) == 1:
        base_score = 0.85
    
    # Two sources with matching SKU: 0.95
    elif len(sources) == 2:
        skus = [s.get('sku') for s in sources.values()]
        if len(set(skus)) == 1:  # All match
            base_score = 0.95
    
    # Three sources with matching SKU: 0.99
    elif len(sources) >= 3:
        skus = [s.get('sku') for s in sources.values()]
        if len(set(skus)) == 1:
            base_score = 0.99
    
    # Adjust for data completeness
    # ...
    
    return base_score
```

### Implementation Phases

#### Phase 1: Parser Development (1-2 hours)
```
scripts/scraper/
├── replacements_parser.py     # NEW: Replacements.com HTML parser
├── replacements_scraper.py    # NEW: Scraper for replacements.com
└── multi_source_matcher.py    # NEW: Cross-reference multiple sources
```

#### Phase 2: Index Integration (30 min)
- Update `index_builder.py` to optionally crawl replacements.com
- Merge data from multiple sources in index
- Store source URLs separately

#### Phase 3: Confidence Algorithm (1 hour)
- Implement cross-reference scoring
- SKU verification across sources
- Data conflict resolution (e.g., different years)

#### Phase 4: Testing (1 hour)
- Test on 10 items available on both sites
- Verify confidence scores improve
- Check for false positives

### Benefits of Multi-Source Approach

**Higher Confidence:**
- dept56_retired only: 0.80-0.90
- dept56_retired + replacements (matching SKU): 0.95
- All 3 sources matching: 0.99

**Better Data Quality:**
- Cross-verify years, names, descriptions
- More images to choose from
- Secondary market pricing data (bonus feature)

**Conflict Resolution:**
- If sources disagree, flag for manual review
- Use majority vote for simple conflicts
- Prefer official dept56.com for authoritative data

### Robots.txt Compliance Notes
- ✅ Respect rate limits (1 req/sec)
- ✅ Check robots.txt before implementing
- ✅ User-agent header identifying our purpose
- ✅ Cache aggressively to minimize requests
- ❌ Do NOT scrape during peak hours (9am-5pm ET)

### Future Enhancements
1. **eBay Completed Listings** - Market value tracking
2. **CollectorsQuest** - Community-driven data
3. **Department56.com Official** - Current products and archives
4. **Image Recognition** - Match products by visual similarity

---

## Next Steps to Implement

1. **Check robots.txt:**
   ```bash
   curl https://www.replacements.com/robots.txt
   ```

2. **Create parser:**
   ```python
   # scripts/scraper/replacements_parser.py
   class ReplacementsParser(ProductParser):
       def extract_dept56_sku(self):
           # Extract from their SKU format
       
       def extract_price(self):
           # Get secondary market value
   ```

3. **Test on sample:**
   - Search for "Robbie's Robot Factory" on replacements.com
   - Parse product page
   - Verify SKU extraction
   - Check image quality

4. **Integrate into workflow:**
   - Add to `index_builder.py` as optional source
   - Update `staging_manager.py` to handle multiple URLs
   - Enhance confidence calculation

---

**Estimated Total Time:** 4-5 hours for full implementation
**Priority:** Medium (current scraper works well, this is enhancement)
**Risk:** Low (additive feature, doesn't break existing functionality)
