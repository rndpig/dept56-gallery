# Collection/Series Bulk Update - Environment Setup

This tool requires Supabase credentials to access your production database.

## Quick Setup:

1. **Create .env file** in the root directory:
```bash
# In: c:\Users\rndpi\Documents\Coding Projects\dept56-gallery\.env

VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-public-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

2. **Get credentials from Supabase dashboard**:
   - Go to your Supabase project dashboard
   - Navigate to Settings → API
   - Copy the Project URL and service_role key

3. **Run the bulk update tool**:
```bash
python scripts\scraper\collection_series_bulk_update.py
```

## What the tool will do:

1. **Analyze ALL houses** in your database using the enhanced scraper
2. **Extract collection/series data** for each house
3. **Calculate confidence scores** (0.0 - 1.0) for the findings
4. **Present results in organized tables**:
   - 🟢 **High Confidence** (75%+) - Safe for bulk approval
   - 🟡 **Medium Confidence** (50-75%) - Review individually  
   - 🔴 **Low Confidence** (<50%) - Manual research needed

5. **Interactive options**:
   - Preview updates (dry run)
   - Apply bulk updates to database
   - Search specific items
   - Detailed analysis view

## Safety Features:

- **Dry run mode** shows what would be updated without making changes
- **Confidence thresholds** separate high-quality vs uncertain results
- **Interactive confirmation** before applying database updates
- **Rollback friendly** - only updates the notes field

## Expected Output:

```
🟢 HIGH CONFIDENCE RESULTS (45 items)
House Name                       Collection           Series               Conf   Sources
-------------------------------- -------------------- -------------------- ------ ----------
Santa's Wonderland House        Christmas Village    Holiday Series       0.87   2x
Robbie's Robot Factory           North Pole           Workshop Series      0.82   3x
...

🟡 MEDIUM CONFIDENCE RESULTS (23 items)  
House Name                       Collection           Series               Conf   Sources
-------------------------------- -------------------- -------------------- ------ ----------
Christmas Carol Cottages         Dickens Village     Literary Series      0.65   1x
...
```

Once you have the .env file set up, the tool will analyze your entire house collection and present the results for review!