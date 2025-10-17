# Department 56 DOCX Ingest Script (Improved for Windows + Supabase)
# =================================================================
# This script scans a network location for .docx files containing
# Department 56 house/accessory information and imports them into Supabase.
#
# Features:
# - Scans \\DilgerNAS\Public\Media\Day NP Files for .docx files
# - Extracts text and images from each Word document
# - Parses metadata (SKU, years, prices, box numbers)
# - Identifies primary item (house) and accessories
# - Uploads images to Supabase Storage
# - Creates database records in Supabase
# - Handles errors gracefully with detailed logging
# - Shows progress and statistics

import os
import sys
import re
import json
import zipfile
import pathlib
from xml.etree import ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Fix Windows console encoding to support UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Ignore if reconfigure not available

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Using system environment variables only.")

# For Supabase integration (install: pip install supabase)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase not installed. Run: pip install supabase")

# =================================================================
# CONFIGURATION
# =================================================================

# Network path to scan
SOURCE_DIR = r"\\DilgerNAS\Public\Media\Day NP Files"

# Local output directory for manifest and logs
OUTPUT_DIR = r"C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app\ingestion_output"

# State tracking file (records which files have been processed)
STATE_FILE = os.path.join(OUTPUT_DIR, "ingestion_state.json")

# Supabase configuration (load from environment or .env file)
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
# Try service role key first (bypasses RLS), fall back to anon key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

# User credentials for authentication (only needed if using anon key)
SUPABASE_USER_EMAIL = os.getenv("SUPABASE_USER_EMAIL")
SUPABASE_USER_PASSWORD = os.getenv("SUPABASE_USER_PASSWORD")

# Default user ID for bulk imports (when using service role key)
DEFAULT_USER_ID = "9f5851e2-9756-4b5e-8b8f-f6caa50b7d8b"

# Processing modes
SKIP_IMAGES_FOR_PROCESSED = True  # Skip image extraction for already-processed files
FORCE_REPROCESS_ALL = False  # Set to True to ignore state and reprocess everything

# =================================================================
# UTILITY FUNCTIONS
# =================================================================

def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def load_state() -> Dict:
    """Load processing state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading state file: {e}")
    return {"processed_files": {}, "last_run": None}

def save_state(state: Dict) -> None:
    """Save processing state to file."""
    try:
        state["last_run"] = datetime.now().isoformat()
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving state file: {e}")

def is_file_processed(file_path: str, state: Dict) -> bool:
    """Check if a file has been processed (has images uploaded)."""
    if FORCE_REPROCESS_ALL:
        return False
    
    file_key = os.path.basename(file_path)
    file_info = state.get("processed_files", {}).get(file_key)
    
    if file_info:
        # Check if images were uploaded in a previous run
        return file_info.get("images_uploaded", 0) > 0
    
    return False

def get_docx_files(directory: str) -> List[str]:
    """
    Recursively find all .docx files in directory.
    Handles network paths and ignores temp files (~$).
    """
    docx_files = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".docx") and not file.startswith("~$"):
                    full_path = os.path.join(root, file)
                    docx_files.append(full_path)
    except Exception as e:
        print(f"❌ Error scanning directory {directory}: {e}")
    return docx_files

def read_docx_text(docx_path: str) -> List[str]:
    """
    Extract plain text from .docx by parsing word/document.xml.
    Returns list of non-empty text lines (paragraphs).
    """
    text_lines = []
    try:
        with zipfile.ZipFile(docx_path) as z:
            with z.open("word/document.xml") as f:
                xml = f.read()
        
        root = ET.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        
        for paragraph in root.findall(".//w:p", ns):
            parts = []
            for text_elem in paragraph.findall(".//w:t", ns):
                if text_elem.text:
                    parts.append(text_elem.text)
            line = "".join(parts).strip()
            if line:
                text_lines.append(line)
    except Exception as e:
        print(f"⚠️  Error reading text from {docx_path}: {e}")
    
    return text_lines

def extract_images(docx_path: str) -> List[Tuple[bytes, str]]:
    """
    Extract images from .docx file.
    Returns list of tuples: (image_bytes, extension)
    """
    images = []
    try:
        with zipfile.ZipFile(docx_path) as z:
            for info in z.infolist():
                if info.filename.startswith("word/media/"):
                    data = z.read(info.filename)
                    ext = pathlib.Path(info.filename).suffix.lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        images.append((data, ext))
    except Exception as e:
        print(f"⚠️  Error extracting images from {docx_path}: {e}")
    
    return images

# =================================================================
# METADATA PARSING
# =================================================================

# Boilerplate phrases to ignore when identifying titles
BOILERPLATE = {
    "top of form", "bottom of form", "box", "box set",
    "department 56", "dept 56", "dept. 56"
}

def is_heading(line: str) -> bool:
    """
    Heuristic to determine if a line is a title/heading.
    - Must be title case or sentence case
    - Not too long (< 100 chars)
    - Not boilerplate
    - Not a metadata line (SKU, price, etc.)
    """
    if not line:
        return False
    
    line_clean = line.strip()
    line_lower = line_clean.lower()
    
    # Ignore boilerplate
    if line_lower in BOILERPLATE:
        return False
    
    # Ignore metadata patterns
    if re.search(r"\b(SKU|Item\s?#|Part\s?Number|Introduced|Retired)\b", line_clean, re.I):
        return False
    
    # Ignore prices
    if re.search(r"\$\s?\d", line_clean):
        return False
    
    # Too long for a title
    if len(line_clean) > 100:
        return False
    
    # Check for title case pattern (multiple capitalized words)
    words = line_clean.split()
    if not words:
        return False
    
    capitalized = sum(1 for w in words if w and w[0].isupper())
    
    # At least 50% of words should be capitalized, or all caps
    return capitalized >= max(2, len(words) // 2) or line_clean.isupper()

# Regex patterns for metadata extraction
SKU_PATTERNS = [
    r"\bSKU[:#]?\s*([A-Za-z0-9.\-]+)",
    r"\bItem\s?#[:#]?\s*([A-Za-z0-9.\-]+)",
    r"\bItem\s?No\.?[:#]?\s*([A-Za-z0-9.\-]+)",
    r"\bPart\s?Number[:#]?\s*([A-Za-z0-9.\-]+)",
]

YEAR_PATTERNS = {
    "introduced": r"\bIntroduced\b(?:\s+(?:January|Feb(?:ruary)?|March?|April?|May|June?|July?|Aug(?:ust)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?))?\s+(\d{4})",
    "retired": r"\bRetired\b(?:\s+(?:January|Feb(?:ruary)?|March?|April?|May|June?|July?|Aug(?:ust)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?))?\s+(\d{4})",
}

PRICE_PATTERN = r"\$\s?(\d+(?:\.\d{2})?)"
BOX_PATTERN = r"\bBox(?:\s+Set)?\s*(?:#)?(\d+)?\b"

def parse_metadata(lines: List[str]) -> Dict:
    """
    Parse metadata from document text lines.
    Returns dict with extracted fields.
    """
    full_text = "\n".join(lines)
    
    # Extract potential titles (in order of appearance)
    headings = [ln.strip() for ln in lines if is_heading(ln)]
    titles = []
    for h in headings:
        # Deduplicate case-insensitively
        if not any(h.lower() == existing.lower() for existing in titles):
            titles.append(h)
    
    # Extract SKUs
    skus = []
    for pattern in SKU_PATTERNS:
        matches = re.findall(pattern, full_text, flags=re.I)
        skus.extend(matches)
    skus = list(dict.fromkeys(skus))  # Deduplicate preserving order
    
    # Extract years
    introduced_years = []
    for match in re.finditer(YEAR_PATTERNS["introduced"], full_text, flags=re.I):
        introduced_years.append(int(match.group(1)))
    
    retired_years = []
    for match in re.finditer(YEAR_PATTERNS["retired"], full_text, flags=re.I):
        retired_years.append(int(match.group(1)))
    
    # Extract prices
    prices = []
    for match in re.finditer(PRICE_PATTERN, full_text):
        prices.append(f"${match.group(1)}")
    
    # Extract box number
    box_match = re.search(BOX_PATTERN, full_text, flags=re.I)
    box_number = box_match.group(1) if box_match and box_match.group(1) else None
    
    # Heuristic: First title is primary item (house), subsequent titles are accessories
    primary_title = titles[0] if titles else None
    accessory_titles = titles[1:] if len(titles) > 1 else []
    
    return {
        "primary_title": primary_title,
        "accessory_titles": accessory_titles,
        "all_titles": titles,
        "skus": skus,
        "prices": prices,
        "introduced_years": sorted(set(introduced_years)),
        "retired_years": sorted(set(retired_years)),
        "box_number": box_number,
        "full_text": full_text,
        "line_count": len(lines),
    }

# =================================================================
# SUPABASE INTEGRATION
# =================================================================

def init_supabase() -> Optional[Client]:
    """Initialize Supabase client and authenticate."""
    if not SUPABASE_AVAILABLE:
        print("❌ Supabase library not available")
        return None
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not found in environment")
        print("   Set VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or VITE_SUPABASE_ANON_KEY)")
        return None
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if using service role key (bypasses RLS, no auth needed)
        using_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") is not None
        
        if using_service_key:
            print("✅ Using Service Role Key (bypasses Row Level Security)")
        else:
            # Authenticate if credentials provided (needed for anon key)
            if SUPABASE_USER_EMAIL and SUPABASE_USER_PASSWORD:
                response = supabase.auth.sign_in_with_password({
                    "email": SUPABASE_USER_EMAIL,
                    "password": SUPABASE_USER_PASSWORD
                })
                print(f"✅ Authenticated as {SUPABASE_USER_EMAIL}")
            else:
                print("⚠️  No user credentials provided (SUPABASE_USER_EMAIL/PASSWORD)")
                print("   You'll need to authenticate manually or use SUPABASE_SERVICE_ROLE_KEY")
        
        return supabase
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        return None

def upload_image_to_supabase(
    supabase: Client,
    image_data: bytes,
    filename: str
) -> Optional[str]:
    """
    Upload image to Supabase Storage.
    Returns public URL on success, None on failure.
    """
    try:
        # Upload to dept56-images bucket
        response = supabase.storage.from_("dept56-images").upload(
            filename,
            image_data,
            file_options={"content-type": "image/jpeg"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("dept56-images").get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"⚠️  Error uploading image {filename}: {e}")
        return None

def create_house_in_supabase(
    supabase: Client,
    name: str,
    metadata: Dict,
    image_url: Optional[str] = None
) -> Optional[str]:
    """
    Create a house record in Supabase.
    Returns house ID on success, None on failure.
    """
    try:
        year = metadata["introduced_years"][0] if metadata["introduced_years"] else None
        
        data = {
            "name": name,
            "year": year,
            "notes": f"Imported from DOCX. SKUs: {', '.join(metadata['skus'])}",
            "photo_url": image_url,
            "purchased_year": year,
        }
        
        response = supabase.table("houses").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"⚠️  Error creating house '{name}': {e}")
        return None

def create_accessory_in_supabase(
    supabase: Client,
    name: str,
    metadata: Dict,
    house_id: Optional[str] = None,
    image_url: Optional[str] = None
) -> Optional[str]:
    """
    Create an accessory record in Supabase.
    Links accessory to its parent house via house_id.
    Returns accessory ID on success, None on failure.
    """
    try:
        year = metadata["introduced_years"][0] if metadata["introduced_years"] else None
        
        data = {
            "name": name,
            "notes": f"Imported from DOCX",
            "photo_url": image_url,
            "purchased_year": year,
            "house_id": house_id,  # Link to parent house
        }
        
        response = supabase.table("accessories").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"⚠️  Error creating accessory '{name}': {e}")
        return None

# =================================================================
# MAIN PROCESSING
# =================================================================

def process_document(
    docx_path: str,
    supabase: Optional[Client] = None,
    dry_run: bool = True,
    skip_images: bool = False
) -> Dict:
    """
    Process a single Word document.
    Returns dict with processing results.
    
    Args:
        docx_path: Path to the Word document
        supabase: Supabase client (None for dry run)
        dry_run: If True, don't upload to database
        skip_images: If True, skip image extraction (faster for re-processing)
    """
    filename = os.path.basename(docx_path)
    stem = pathlib.Path(docx_path).stem
    
    skip_msg = " [SKIP IMAGES]" if skip_images else ""
    print(f"\n📄 Processing: {filename}{skip_msg}")
    
    result = {
        "file": filename,
        "path": docx_path,
        "success": False,
        "error": None,
        "house_id": None,
        "accessory_ids": [],
        "images_uploaded": 0,
        "metadata": {},
    }
    
    try:
        # Extract text
        lines = read_docx_text(docx_path)
        if not lines:
            result["error"] = "No text content found"
            return result
        
        # Parse metadata
        metadata = parse_metadata(lines)
        result["metadata"] = metadata
        print(f"   📝 Primary: {metadata['primary_title']}")
        if metadata['accessory_titles']:
            print(f"   🔧 Accessories: {', '.join(metadata['accessory_titles'])}")
        print(f"   📅 Years: Introduced {metadata['introduced_years']}, Retired {metadata['retired_years']}")
        
        # Extract images (unless skipped for performance)
        images = []
        if not skip_images:
            images = extract_images(docx_path)
            print(f"   🖼️  Found {len(images)} image(s)")
        else:
            print(f"   ⏭️  Skipping image extraction (already processed)")
        
        if dry_run:
            print("   ⏭️  Dry run - skipping upload")
            result["success"] = True
            result["image_count"] = len(images)
            return result
        
        # Upload to Supabase if available
        if supabase and metadata["primary_title"]:
            # Generate folder name (use 'ingestion' folder if no user context)
            try:
                user = supabase.auth.get_user()
                folder = user.user.id if user and user.user else "ingestion"
            except:
                folder = "ingestion"
            
            # Upload first image for primary item (if we have images and haven't skipped)
            image_url = None
            if images and len(images) > 0:
                image_filename = f"{folder}/{stem}_primary{images[0][1]}"
                image_url = upload_image_to_supabase(supabase, images[0][0], image_filename)
                if image_url:
                    result["images_uploaded"] += 1
            
            # Create house record
            house_id = create_house_in_supabase(
                supabase,
                metadata["primary_title"],
                metadata,
                image_url
            )
            result["house_id"] = house_id
            
            # Create accessory records and link them to the house
            for i, acc_title in enumerate(metadata["accessory_titles"]):
                acc_image_url = None
                if i + 1 < len(images):
                    acc_filename = f"{folder}/{stem}_acc{i}{images[i+1][1]}"
                    acc_image_url = upload_image_to_supabase(supabase, images[i+1][0], acc_filename)
                    if acc_image_url:
                        result["images_uploaded"] += 1
                
                acc_id = create_accessory_in_supabase(
                    supabase,
                    acc_title,
                    metadata,
                    house_id,  # Link accessory to its parent house
                    acc_image_url
                )
                if acc_id:
                    result["accessory_ids"].append(acc_id)
            
            result["success"] = True
            print(f"   ✅ Uploaded to Supabase")
        else:
            result["error"] = "Supabase not available or no primary title"
    
    except Exception as e:
        result["error"] = str(e)
        print(f"   ❌ Error: {e}")
    
    return result

def main():
    """Main entry point for ingestion script."""
    print("=" * 60)
    print("Department 56 DOCX Ingestion Script")
    print("=" * 60)
    print(f"\nSource: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Ensure output directory exists
    ensure_dir(OUTPUT_DIR)
    
    # Load processing state
    state = load_state()
    previously_processed = len([f for f in state.get("processed_files", {}).values() if f.get("images_uploaded", 0) > 0])
    
    # Find all .docx files
    print("\nScanning for .docx files...")
    docx_files = get_docx_files(SOURCE_DIR)
    print(f"Found {len(docx_files)} document(s)")
    
    if previously_processed > 0 and SKIP_IMAGES_FOR_PROCESSED:
        print(f"Previously processed: {previously_processed} files (will skip image extraction)")
    
    if not docx_files:
        print("❌ No .docx files found. Check the source directory.")
        return
    
    # Initialize Supabase
    supabase = init_supabase()
    dry_run = supabase is None
    
    if dry_run:
        print("\nRunning in DRY RUN mode (Supabase not available)")
        print("   Files will be analyzed but not uploaded")
    
    # Process each document
    results = []
    skipped_image_count = 0
    
    for i, docx_path in enumerate(docx_files, 1):
        print(f"\n[{i}/{len(docx_files)}]", end=" ")
        
        # Check if we should skip image extraction for this file
        skip_images = SKIP_IMAGES_FOR_PROCESSED and is_file_processed(docx_path, state)
        if skip_images:
            skipped_image_count += 1
        
        result = process_document(docx_path, supabase, dry_run, skip_images)
        results.append(result)
        
        # Update state for successfully processed files
        if result["success"] and not dry_run:
            file_key = os.path.basename(docx_path)
            state["processed_files"][file_key] = {
                "path": docx_path,
                "images_uploaded": result.get("images_uploaded", 0),
                "house_id": result.get("house_id"),
                "accessory_count": len(result.get("accessory_ids", [])),
                "last_processed": datetime.now().isoformat()
            }
    
    # Save updated state
    if not dry_run:
        save_state(state)
        print(f"\nState saved: {STATE_FILE}")
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    total_images = sum(r.get("images_uploaded", 0) for r in results)
    total_houses = sum(1 for r in results if r.get("house_id"))
    total_accessories = sum(len(r.get("accessory_ids", [])) for r in results)
    
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Images uploaded: {total_images}")
    print(f"Houses created: {total_houses}")
    print(f"Accessories created: {total_accessories}")
    if skipped_image_count > 0:
        print(f"Files with skipped image extraction: {skipped_image_count}")
    
    # Create verification report
    houses_list = []
    accessories_list = []
    for r in results:
        if r.get("house_id"):
            houses_list.append({
                "file": r["file"],
                "title": r.get("metadata", {}).get("primary_title", "N/A"),
                "id": r.get("house_id"),
                "images": r.get("images_uploaded", 0)
            })
        if r.get("accessory_ids"):
            for acc_title in r.get("metadata", {}).get("accessory_titles", []):
                accessories_list.append({
                    "file": r["file"],
                    "title": acc_title
                })
    
    # Save manifest
    manifest_path = os.path.join(OUTPUT_DIR, f"manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nManifest saved: {manifest_path}")
    
    # Create summary DataFrame
    df_data = []
    for r in results:
        # Determine type (House or Accessory based on filename)
        filename = r["file"]
        item_type = "Accessory" if filename.startswith("ACC ") else "House"
        
        df_data.append({
            "File": r["file"],
            "Type": item_type,
            "Success": "YES" if r["success"] else "NO",
            "Primary Title": r.get("metadata", {}).get("primary_title", "N/A") if "metadata" in r else "N/A",
            "Has House ID": "YES" if r.get("house_id") else "NO",
            "Accessories": len(r.get("accessory_ids", [])),
            "Images": r.get("images_uploaded", r.get("image_count", 0)),
            "Error": r.get("error", "")[:50] if r.get("error") else ""
        })
    
    df = pd.DataFrame(df_data)
    csv_path = os.path.join(OUTPUT_DIR, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Summary CSV saved: {csv_path}")
    
    # Save verification report
    verification_path = os.path.join(OUTPUT_DIR, f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    verification_data = {
        "summary": {
            "total_files": len(results),
            "houses_created": total_houses,
            "accessories_created": total_accessories,
            "images_uploaded": total_images,
            "files_with_skipped_images": skipped_image_count
        },
        "houses": houses_list,
        "accessories": accessories_list
    }
    with open(verification_path, "w", encoding="utf-8") as f:
        json.dump(verification_data, f, indent=2)
    print(f"Verification report saved: {verification_path}")
    
    print("\n" + df.to_string())
    print("\nIngestion complete!")

if __name__ == "__main__":
    main()
