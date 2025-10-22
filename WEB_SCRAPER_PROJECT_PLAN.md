# Web Scraper & Data Enhancement Project Plan

## 🎯 Project Goals

1. **Enhance existing data** with comprehensive details and images
2. **Automate future imports** from item title lists
3. **Maintain data integrity** through staging and moderation
4. **Link relationships** between houses, accessories, series, and collections

---

## 🏗️ System Architecture

### Data Flow
```
Input (Item Titles)
    ↓
Multi-Site Web Scraper
    ↓
Staging Tables (isolated from production)
    ↓
Confidence Scoring & Matching
    ↓
Moderation Interface (human review)
    ↓
Production Database (approved changes only)
```

---

## 📦 Component 1: Database Schema (Staging Tables)

### New Supabase Tables

#### `staged_houses`
```sql
CREATE TABLE staged_houses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_house_id UUID REFERENCES houses(id),  -- NULL for new imports
  item_number TEXT NOT NULL,
  name TEXT NOT NULL,
  
  -- Scraped data fields
  intro_year INTEGER,
  retire_year INTEGER,
  description TEXT,
  dimensions TEXT,
  primary_image_url TEXT,
  additional_images JSONB,  -- Array of image URLs
  
  -- Source tracking
  dept56_official_url TEXT,
  dept56_retired_url TEXT,
  replacements_url TEXT,
  scraped_at TIMESTAMP DEFAULT NOW(),
  
  -- Confidence scoring
  name_match_score DECIMAL(3,2),  -- 0.00 to 1.00
  details_confidence_score DECIMAL(3,2),
  overall_confidence_score DECIMAL(3,2),
  
  -- Relationship data (discovered through scraping)
  discovered_series TEXT,
  discovered_collection TEXT,
  discovered_accessories JSONB,  -- Array of accessory names/numbers
  
  -- Moderation status
  status TEXT DEFAULT 'pending',  -- pending, approved, rejected, needs_review
  reviewed_at TIMESTAMP,
  reviewed_by TEXT,
  moderator_notes TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `staged_accessories`
```sql
CREATE TABLE staged_accessories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_accessory_id UUID REFERENCES accessories(id),
  item_number TEXT NOT NULL,
  name TEXT NOT NULL,
  
  -- Same structure as staged_houses
  intro_year INTEGER,
  retire_year INTEGER,
  description TEXT,
  dimensions TEXT,
  primary_image_url TEXT,
  additional_images JSONB,
  
  dept56_official_url TEXT,
  dept56_retired_url TEXT,
  replacements_url TEXT,
  scraped_at TIMESTAMP DEFAULT NOW(),
  
  name_match_score DECIMAL(3,2),
  details_confidence_score DECIMAL(3,2),
  overall_confidence_score DECIMAL(3,2),
  
  discovered_series TEXT,
  discovered_collection TEXT,
  discovered_compatible_houses JSONB,
  
  status TEXT DEFAULT 'pending',
  reviewed_at TIMESTAMP,
  reviewed_by TEXT,
  moderator_notes TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `scraping_log`
```sql
CREATE TABLE scraping_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  search_query TEXT NOT NULL,
  source_site TEXT NOT NULL,  -- 'dept56_official', 'dept56_retired', 'replacements'
  results_found INTEGER,
  success BOOLEAN,
  error_message TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🕷️ Component 2: Python Web Scraper

### Technology Stack
- **Selenium** for JavaScript-heavy sites (Department 56)
- **BeautifulSoup** for simpler parsing (Replacements.com)
- **FuzzyWuzzy** for string matching and confidence scoring
- **Supabase Python Client** for database operations

### File Structure
```
scripts/
  scraper/
    __init__.py
    config.py                  # Site configs, selectors, rate limits
    dept56_official_scraper.py # Main site scraper
    dept56_retired_scraper.py  # Retired products scraper
    replacements_scraper.py    # Replacements.com scraper
    fuzzy_matcher.py           # Confidence scoring logic
    staging_manager.py         # Insert/update staging tables
    bulk_importer.py           # Process CSV/text lists
    image_downloader.py        # Download and upload images to Supabase Storage
```

### Key Features

#### 1. **Multi-Site Search Strategy**
```python
def search_all_sources(item_name, item_number=None):
    results = {
        'dept56_official': search_dept56_official(item_name, item_number),
        'dept56_retired': search_dept56_retired(item_name, item_number),
        'replacements': search_replacements(item_name, item_number)
    }
    
    # Merge results with confidence scoring
    best_match = aggregate_results(results)
    return best_match
```

#### 2. **Fuzzy Matching with Confidence Scores**
```python
from fuzzywuzzy import fuzz

def calculate_confidence(search_name, found_name, found_details):
    # Name matching (weighted 50%)
    name_score = fuzz.token_sort_ratio(search_name, found_name) / 100
    
    # Details completeness (weighted 30%)
    required_fields = ['intro_year', 'description', 'images']
    details_score = sum([1 for f in required_fields if found_details.get(f)]) / len(required_fields)
    
    # Cross-site validation (weighted 20%)
    cross_site_score = 0.5 if len(found_details.get('sources', [])) > 1 else 0
    
    overall = (name_score * 0.5) + (details_score * 0.3) + (cross_site_score * 0.2)
    
    return {
        'name_match': name_score,
        'details_confidence': details_score,
        'overall': overall
    }
```

#### 3. **Series/Collection Discovery**
```python
def discover_relationships(item_data, all_results):
    """
    Extract series/collection from:
    1. Breadcrumb navigation
    2. Product categories/tags
    3. Related items sections
    4. Pattern matching in descriptions
    """
    series = extract_series(item_data)
    collection = extract_collection(item_data)
    related_items = find_related_accessories(item_data, all_results)
    
    return {
        'series': series,
        'collection': collection,
        'accessories': related_items
    }
```

---

## 🖥️ Component 3: Moderation Interface (React UI)

### New Tab in DeptApp.tsx: "Data Review"

Only visible to admins, shows:

#### View 1: Pending Items Grid
- Card layout showing staged items
- Display original vs. scraped values side-by-side
- Confidence score badges (green >0.8, yellow 0.5-0.8, red <0.5)
- Diff highlighting for changed fields

#### View 2: Comparison Details
```tsx
<ComparisonView>
  <Column title="Current Data">
    <Field label="Name">{currentData.name}</Field>
    <Field label="Year">{currentData.intro_year}</Field>
    {/* ... */}
  </Column>
  
  <Column title="Scraped Data" highlight="changes">
    <Field label="Name" changed={nameChanged}>{scrapedData.name}</Field>
    <Field label="Year" changed={yearChanged}>{scrapedData.intro_year}</Field>
    {/* ... */}
  </Column>
  
  <Column title="Actions">
    <Button onClick={approveAll}>✅ Approve All</Button>
    <Button onClick={approveSelected}>✅ Approve Selected Fields</Button>
    <Button onClick={reject}>❌ Reject</Button>
    <Button onClick={flagForReview}>⚠️ Needs Manual Review</Button>
  </Column>
</ComparisonView>
```

#### View 3: Image Gallery Comparison
- Side-by-side current images vs. scraped images
- Select which images to keep/add
- Preview before approval

---

## 📥 Component 4: Bulk Import Tool

### CSV/Text Input Format
```csv
item_number,name,type
56.54305,"Robbie's Robot Factory",house
56.53320,"Animated Neon Sign",accessory
```

### Import Process
1. Parse CSV/text file
2. Queue items for scraping (with rate limiting)
3. Scrape each item from all 3 sources
4. Insert into staging tables
5. Generate import report with confidence scores

### CLI Usage
```bash
python scripts/scraper/bulk_importer.py --file new_items.csv --type house
```

---

## 🔗 Component 5: Relationship Linking

### House-Accessory Linking Strategy

Since product pages don't explicitly link accessories, use:

#### Method 1: Collection/Series Matching
```python
def link_by_collection(house, all_accessories):
    # If house is "North Pole Series", find accessories in same series
    matching = [acc for acc in all_accessories 
                if acc.series == house.series 
                or acc.collection == house.collection]
    return matching
```

#### Method 2: Replacements.com Cross-Reference
```python
def scrape_replacements_recommendations(item_number):
    """
    Replacements.com often shows:
    - "Goes with" sections
    - "Complete your collection" suggestions
    - Related items
    """
    page = fetch_page(f"https://www.replacements.com/search?q={item_number}")
    related = parse_related_items(page)
    return related
```

#### Method 3: Description Text Mining
```python
def extract_accessory_hints(house_description):
    """
    Look for phrases like:
    - "Coordinates with..."
    - "Pairs well with..."
    - "Includes accessories: X, Y, Z"
    """
    patterns = [
        r"coordinates with (.+?)(?:\.|$)",
        r"pairs with (.+?)(?:\.|$)",
        r"includes (.+?)(?:\.|$)"
    ]
    hints = extract_with_patterns(house_description, patterns)
    return hints
```

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create staging tables in Supabase
- [ ] Set up Python scraper project structure
- [ ] Implement basic Selenium scraper for dept56_retired.com
- [ ] Test on 10 sample items

### Phase 2: Multi-Source Scraping (Week 2-3)
- [ ] Add dept56.com scraper
- [ ] Add replacements.com scraper
- [ ] Implement fuzzy matching and confidence scoring
- [ ] Test cross-site data aggregation

### Phase 3: Moderation Interface (Week 3-4)
- [ ] Add "Data Review" tab to React app
- [ ] Build comparison UI
- [ ] Implement approve/reject workflow
- [ ] Add RLS policies for staging tables

### Phase 4: Bulk Import (Week 4-5)
- [ ] CSV parser
- [ ] Queue management
- [ ] Rate limiting (respect robots.txt)
- [ ] Progress tracking UI

### Phase 5: Relationship Discovery (Week 5-6)
- [ ] Series/collection extraction
- [ ] House-accessory linking algorithms
- [ ] Confidence scoring for relationships
- [ ] Manual override options

### Phase 6: Testing & Refinement (Week 6-7)
- [ ] Run on full dataset in staging
- [ ] Review confidence scores accuracy
- [ ] Adjust matching thresholds
- [ ] User acceptance testing

### Phase 7: Production Migration (Week 7-8)
- [ ] Approve high-confidence items
- [ ] Manually review medium-confidence items
- [ ] Document rejected items
- [ ] Merge feature branch to main

---

## 🔒 Safety Mechanisms

### 1. **Read-Only on Production**
Scraper NEVER writes directly to `houses` or `accessories` tables.

### 2. **Rate Limiting**
```python
RATE_LIMITS = {
    'dept56_official': 1,  # 1 request per second
    'dept56_retired': 2,   # 2 requests per second  
    'replacements': 1
}
```

### 3. **Dry Run Mode**
```bash
python bulk_importer.py --file items.csv --dry-run
# Shows what WOULD be scraped without actually doing it
```

### 4. **Rollback Capability**
Track all approvals in an audit log:
```sql
CREATE TABLE moderation_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  staged_item_id UUID,
  item_type TEXT,  -- 'house' or 'accessory'
  action TEXT,     -- 'approved', 'rejected'
  changes_applied JSONB,
  moderator TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📊 Confidence Score Thresholds

- **≥ 0.90**: Auto-approve (with admin notification)
- **0.70 - 0.89**: Recommend approval (highlight for review)
- **0.50 - 0.69**: Needs review (show warnings)
- **< 0.50**: Flag as uncertain (require manual research)

---

## 🎨 UI Mockup: Moderation Interface

```
┌─────────────────────────────────────────────────────────┐
│  Data Review (23 pending items)                         │
├─────────────────────────────────────────────────────────┤
│  Filters: [All] [High Confidence] [Needs Review]        │
│           [Houses] [Accessories]                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────┐          │
│  │ 🏠 Robbie's Robot Factory (56.54305)      │          │
│  │ Confidence: 92% ⭐⭐⭐⭐⭐                    │          │
│  ├──────────────────────────────────────────┤          │
│  │ Current          →  Scraped              │          │
│  │ Year: 2006       →  2006 ✓               │          │
│  │ Desc: [none]     →  "A whimsical..."  ⚠️  │          │
│  │ Images: 1        →  5 images found  ⚠️     │          │
│  │ Series: [none]   →  North Pole Series ⚠️  │          │
│  ├──────────────────────────────────────────┤          │
│  │ [✅ Approve] [📝 Edit] [❌ Reject]        │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
│  ┌──────────────────────────────────────────┐          │
│  │ 🎄 Animated Neon Sign (56.53320)          │          │
│  │ Confidence: 67% ⚠️⚠️⚠️                      │          │
│  │ [Review Details...]                       │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Next Steps

1. **Review this plan** - Does it address all your requirements?
2. **Prioritize features** - Which components are most critical?
3. **Set up staging tables** - I can generate the SQL migration
4. **Start with a prototype** - Scrape 10 items to test the workflow

**Ready to proceed?** Let me know if you want to:
- A) Start with the database schema (staging tables)
- B) Build a prototype scraper first
- C) Adjust any part of this plan

This is a comprehensive system that will transform your data quality! 🎉
