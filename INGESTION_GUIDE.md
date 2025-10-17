# Department 56 DOCX Ingestion Guide

## Overview

This script scans your network location for Word documents containing Department 56 house/accessory information and imports them into your Supabase database.

## Key Improvements from Original

✅ **Windows Network Path Support** - Works with `\\DilgerNAS\Public\Media\Day NP Files`
✅ **Direct Supabase Integration** - Uploads directly to your cloud database
✅ **Better Error Handling** - Graceful failures with detailed error messages
✅ **Progress Tracking** - Shows progress for each file
✅ **Dry Run Mode** - Test without uploading (automatic if Supabase not configured)
✅ **Improved Parsing** - Better title detection and metadata extraction
✅ **Image Upload** - Automatically uploads images to Supabase Storage
✅ **Detailed Reports** - JSON manifest and CSV summary

## Prerequisites

1. **Python 3.8+** installed
2. **Network access** to `\\DilgerNAS\Public\Media\Day NP Files`
3. **Supabase project** configured (from previous steps)
4. **Your Supabase credentials**

## Setup

### Step 1: Install Python Dependencies

```powershell
# Navigate to your project directory
cd "C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app"

# Install required packages
pip install -r requirements-ingest.txt
```

This installs:
- `pandas` - For data processing and CSV output
- `supabase` - Python client for Supabase
- `python-dotenv` - For environment variable management

### Step 2: Configure Environment Variables

Add these lines to your `.env` file:

```env
# Existing Supabase config
VITE_SUPABASE_URL=https://xctottgirqkkmjmutoon.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Add your user credentials for ingestion
SUPABASE_USER_EMAIL=your-email@example.com
SUPABASE_USER_PASSWORD=your-password
```

**Important:** Replace with your actual email and password from when you created your Supabase account.

### Step 3: Verify Network Access

```powershell
# Test access to network location
Test-Path "\\DilgerNAS\Public\Media\Day NP Files"
```

Should return `True` if accessible.

### Step 4: Run the Script

```powershell
# Dry run first (analyzes without uploading)
python ingest_docx.py

# After reviewing results, run with Supabase credentials to upload
# (Make sure you've added SUPABASE_USER_EMAIL and SUPABASE_USER_PASSWORD to .env)
```

## Configuration Options

You can edit these constants at the top of `ingest_docx.py`:

```python
# Network path to scan
SOURCE_DIR = r"\\DilgerNAS\Public\Media\Day NP Files"

# Local output directory
OUTPUT_DIR = r"C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app\ingestion_output"
```

## What the Script Does

1. **Scans** the network location for `.docx` files
2. **Extracts** text content from each document
3. **Identifies**:
   - Primary title (house name)
   - Secondary titles (accessories)
   - SKU numbers
   - Introduced/Retired years
   - Prices
   - Box numbers
4. **Extracts** embedded images from the Word documents
5. **Uploads** images to Supabase Storage (under your user folder)
6. **Creates** database records:
   - House record with first image
   - Accessory records with subsequent images
7. **Generates** reports:
   - JSON manifest with all details
   - CSV summary for easy viewing

## Output Files

After running, you'll find in `ingestion_output/`:

- `manifest_YYYYMMDD_HHMMSS.json` - Complete processing results
- `summary_YYYYMMDD_HHMMSS.csv` - Summary table
- Logs showing success/failure for each document

## Understanding the Output

### Console Output

```
📄 Processing: Mickey's Stuffed Animals.docx
   📝 Primary: Mickey's Stuffed Animals
   🔧 Accessories: Stuffing Station, Display Rack
   📅 Years: Introduced [2018], Retired []
   🖼️  Found 3 image(s)
   ✅ Uploaded to Supabase
```

### Summary Statistics

```
✅ Successful: 45
❌ Failed: 2
🖼️  Images uploaded: 98
```

## Document Structure Expected

The script works best when your Word documents follow this structure:

```
[Primary House Name]  (Title case, first heading)
SKU: 12345
Introduced: 2018
Retired: 2020
Price: $45.00
Box 5

[Accessory Name 1]  (Optional, subsequent headings)
[Accessory Name 2]  (Optional)
```

## Troubleshooting

### "No .docx files found"
- Check the SOURCE_DIR path
- Verify network access: `Test-Path "\\DilgerNAS\Public\Media\Day NP Files"`
- Ensure you have read permissions

### "Supabase not available"
- Install: `pip install supabase`
- Check `.env` file has correct credentials

### "Authentication failed"
- Verify SUPABASE_USER_EMAIL and SUPABASE_USER_PASSWORD in `.env`
- Make sure you've confirmed your email
- Try logging into the web app first to verify credentials

### "Error uploading image"
- Check that the `dept56-images` bucket exists in Supabase Storage
- Verify RLS policies allow uploads (should be set from SQL migration)
- Check image file sizes (Supabase free tier has limits)

### Images not parsing correctly
- Some Word documents embed images differently
- Check the document manually to verify images are truly embedded
- Try re-saving the document in a newer Word format

### Titles not detected
- The script looks for Title Case headings
- Edit the `is_heading()` function to adjust sensitivity
- Check for unusual formatting in the document

## Advanced Usage

### Process Only Specific Files

Edit the script to filter files:

```python
# In get_docx_files function, add filter:
for file in files:
    if file.lower().endswith(".docx") and "2018" in file:  # Only 2018 files
        full_path = os.path.join(root, file)
        docx_files.append(full_path)
```

### Skip Already Imported Files

Keep track of processed files:

```python
# Add to the script:
processed_file = os.path.join(OUTPUT_DIR, "processed_files.txt")
if os.path.exists(processed_file):
    with open(processed_file) as f:
        processed = set(f.read().splitlines())
    docx_files = [f for f in docx_files if f not in processed]
```

### Custom Metadata Extraction

Add patterns to extract additional fields:

```python
# Add to YEAR_PATTERNS:
"manufactured": r"\bManufactured\b\s+(\d{4})",
"collection": r"\bCollection[:#]?\s+([A-Za-z0-9\s]+)",
```

## Integration with Web App

After running the ingestion:

1. **Open your web app**: http://localhost:3000
2. **Sign in** with your credentials
3. **Browse tab** will show all imported houses and accessories
4. **Use search** to find specific items
5. **Add collections/tags** to organize imported items
6. **Link accessories to houses** if not automatically linked

## Performance Tips

- **Large batches**: Process in smaller batches (e.g., by year or box number)
- **Network speed**: Copy files locally first for faster processing
- **Image sizes**: Consider resizing large images before upload
- **Rate limiting**: Add delays between uploads if hitting Supabase limits

## Data Validation

After import, verify:

1. **House count** matches expected number of documents
2. **Images** are displaying correctly
3. **Metadata** (years, SKUs) is accurate
4. **Accessories** are properly identified
5. **No duplicates** were created

Run this query in Supabase SQL Editor:

```sql
-- Check imported data
SELECT 
  COUNT(*) as total_houses,
  COUNT(photo_url) as houses_with_photos,
  COUNT(DISTINCT year) as unique_years
FROM houses;
```

## Next Steps

After successful ingestion:

1. ✅ Review imported data in web app
2. ✅ Add missing metadata manually
3. ✅ Create collections (e.g., "Heritage Village", "North Pole")
4. ✅ Add tags for easier searching
5. ✅ Link related accessories to houses
6. ✅ Add notes or additional photos

## Support

For issues or questions:
- Check the error messages in console output
- Review the manifest JSON for detailed error information
- Ensure all prerequisites are met
- Verify Supabase connection in the web app first

---

**Happy Importing! 🏠✨**
