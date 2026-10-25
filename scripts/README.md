# Utility Scripts

This directory contains utility scripts for data management and maintenance.

## 📁 Directory Structure

```
scripts/
├── data-ingestion/      # Import data from external sources
├── scraping/            # Web scraping tools
└── maintenance/         # Database maintenance utilities
```

## 🔧 Data Ingestion

**Location:** `data-ingestion/`

Scripts for importing data from various sources into the Supabase database.

### ingest_docx.py

Imports Department 56 collection data from Word documents.

**Setup:**
```powershell
cd scripts/data-ingestion
pip install -r requirements.txt
```

**Usage:**
```powershell
# Set environment variables
$env:SUPABASE_URL = "your-project-url"
$env:SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

# Run the ingestion
python ingest_docx.py path/to/your/document.docx
```

**See also:** [INGESTION_GUIDE.md](../../INGESTION_GUIDE.md) for detailed instructions.

---

## 🌐 Web Scraping

**Location:** `scraping/`

Tools for scraping Department 56 product data from websites.

### scraper_prototype.py

Prototype web scraper for collecting product information.

**Setup:**
```powershell
cd scripts/scraping
pip install -r requirements.txt
```

**Usage:**
```powershell
python scraper_prototype.py
```

**See also:** [SCRAPING_PLAN.md](../../SCRAPING_PLAN.md) for methodology and results.

---

## 🛠️ Database Maintenance

**Location:** `maintenance/`

Scripts for maintaining database integrity and cleaning up duplicates.

### analyze_duplicates.py

Analyzes the database for duplicate house records based on name similarity.

**Setup:**
```powershell
cd scripts/maintenance
# Uses supabase-py (install if needed)
pip install supabase
```

**Usage:**
```powershell
$env:SUPABASE_URL = "your-project-url"
$env:SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

python analyze_duplicates.py
```

**Output:** Creates a timestamped JSON file with duplicate analysis.

### generate_cleanup_plan.py

Generates a cleanup plan from duplicate analysis results.

**Usage:**
```powershell
python generate_cleanup_plan.py duplicate_analysis_YYYYMMDD_HHMMSS.json
```

**Output:** Creates a timestamped cleanup plan JSON file with:
- Records to delete
- Records to keep (primary)
- Detailed analysis by duplicate group

### execute_cleanup.py

Safely executes a cleanup plan to remove duplicate records.

**Usage:**
```powershell
python execute_cleanup.py cleanup_plan_YYYYMMDD_HHMMSS.json
```

**Features:**
- Confirmation prompt before deletion
- Batch processing (10 records at a time)
- Progress reporting
- Summary of kept primary records

**⚠️ WARNING:** This permanently deletes records. Review the cleanup plan carefully before executing.

### link_accessories_to_houses.py

Creates house-accessory links based on the ingestion manifest. Links accessories to the houses they originated with in the same Word document.

**Usage:**
```powershell
$env:SUPABASE_URL = "your-project-url"
$env:SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

python link_accessories_to_houses.py
```

**Features:**
- Reads latest ingestion manifest automatically
- Validates all IDs exist before creating links
- Skips already-existing links
- Batch processing (100 links at a time)
- Generates detailed JSON report
- Confirmation prompt before proceeding

**Output:** Creates `linking_report_YYYYMMDD_HHMMSS.json` with statistics and invalid mappings.

---

## 🔐 Environment Variables

All scripts require Supabase credentials:

```powershell
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
```

**Note:** Use the **service role key** (not the anon key) for these administrative scripts. Keep this key secure and never commit it to version control.

---

## 📝 Workflow Examples

### Cleaning Up Duplicates

1. **Analyze for duplicates:**
   ```powershell
   cd scripts/maintenance
   python analyze_duplicates.py
   # Output: duplicate_analysis_20251018_120000.json
   ```

2. **Generate cleanup plan:**
   ```powershell
   python generate_cleanup_plan.py duplicate_analysis_20251018_120000.json
   # Output: cleanup_plan_20251018_120000.json
   ```

3. **Review the plan** (open the JSON file and check which records will be deleted)

4. **Execute the cleanup:**
   ```powershell
   python execute_cleanup.py cleanup_plan_20251018_120000.json
   # Type 'yes' to confirm
   ```

### Importing New Data

1. **Prepare your Word document** with collection data

2. **Run the ingestion:**
   ```powershell
   cd scripts/data-ingestion
   python ingest_docx.py path/to/document.docx
   ```

3. **Check results** in the Supabase dashboard

---

## 🆘 Troubleshooting

### "ModuleNotFoundError"
Install the required dependencies:
```powershell
pip install -r requirements.txt
```

### "Missing environment variables"
Make sure to set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` before running scripts.

### Permission errors
These scripts require the **service role key** with elevated permissions, not the regular anon key.

---

## 📚 Additional Documentation

- [INGESTION_GUIDE.md](../../INGESTION_GUIDE.md) - Detailed data import instructions
- [SCRAPING_PLAN.md](../../SCRAPING_PLAN.md) - Web scraping methodology
- [README.md](../../README.md) - Main project documentation
