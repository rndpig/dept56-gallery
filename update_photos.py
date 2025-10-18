# Department 56 Photo Re-upload Script
# Focus on just re-uploading missing photos by matching names
# Uses same state tracking as ingest_docx.py

import os
import sys
import zipfile
import pathlib
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase 
supabase = create_client(
    os.getenv("VITE_SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Configuration 
SOURCE_DIR = r"\\DilgerNAS\Public\Media\Day NP Files"
OUTPUT_DIR = r"C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app\ingestion_output"
STATE_FILE = os.path.join(OUTPUT_DIR, "ingestion_state.json")

# Cache for database records
DB_CACHE = {
    "houses": None,
    "accessories": None
}

# Special handling for reindeer pairs
REINDEER_PAIRS = {
    frozenset(["donner", "donder", "blitzen"]): [
        "Donner & Blitzen",
        "Blitzen & Donner",
        "Donner and Blitzen",
        "Blitzen and Donner",
        "Reindeer Stables Donner & Blitzen",
        "Reindeer Stables, Donner & Blitzen",
        "Reindeer Stables Blitzen & Donner",
        "Reindeer Stables, Blitzen & Donner",
        "Donner Blitzen Reindeer Stables",
        "Blitzen Donner Reindeer Stables"
    ],
    frozenset(["dasher", "dancer"]): [
        "Dasher & Dancer",
        "Dancer & Dasher",
        "Dasher and Dancer",
        "Dancer and Dasher",
        "Reindeer Stables Dasher & Dancer",
        "Reindeer Stables, Dasher & Dancer",
        "Reindeer Stables Dancer & Dasher",
        "Reindeer Stables, Dancer & Dasher",
        "Dasher Dancer Reindeer Stables",
        "Dancer Dasher Reindeer Stables"
    ],
    frozenset(["prancer", "vixen"]): [
        "Prancer & Vixen",
        "Vixen & Prancer",
        "Prancer and Vixen",
        "Vixen and Prancer",
        "Reindeer Stables Prancer & Vixen",
        "Reindeer Stables, Prancer & Vixen",
        "Reindeer Stables Vixen & Prancer",
        "Reindeer Stables, Vixen & Prancer",
        "Prancer Vixen Reindeer Stables",
        "Vixen Prancer Reindeer Stables"
    ],
    frozenset(["comet", "cupid"]): [
        "Comet & Cupid",
        "Cupid & Comet",
        "Comet and Cupid",
        "Cupid and Comet",
        "Reindeer Stables Comet & Cupid",
        "Reindeer Stables, Comet & Cupid",
        "Reindeer Stables Cupid & Comet",
        "Reindeer Stables, Cupid & Comet",
        "Comet Cupid Reindeer Stables",
        "Cupid Comet Reindeer Stables"
    ]
}

def load_db_cache(supabase: Client) -> None:
    """Load all records into memory for faster lookups."""
    try:
        print("Loading database records into cache...")
        
        # Get all records
        houses = supabase.table("houses").select("*").execute().data
        accessories = supabase.table("accessories").select("*").execute().data
        
        # Create name variations for each record
        DB_CACHE["houses"] = {}
        DB_CACHE["accessories"] = {}
        
        # Process houses
        for record in houses:
            name = record["name"]
            variations = get_name_variations(name)
            for var in variations:
                var_lower = var.lower()
                if var_lower not in DB_CACHE["houses"]:
                    DB_CACHE["houses"][var_lower] = record
        
        # Process accessories with special handling
        for record in accessories:
            name = record["name"]
            
            # Special case: Reindeer Stables
            if "Reindeer" in name and "&" in name:
                parts = name.split("&")
                for part in parts:
                    clean_part = part.strip()
                    if "Reindeer" not in clean_part:
                        variations = get_name_variations(f"Reindeer Stables {clean_part}")
                        for var in variations:
                            var_lower = var.lower()
                            if var_lower not in DB_CACHE["accessories"]:
                                DB_CACHE["accessories"][var_lower] = record
            
            # Generate standard variations
            variations = get_name_variations(name)
            for var in variations:
                var_lower = var.lower()
                if var_lower not in DB_CACHE["accessories"]:
                    DB_CACHE["accessories"][var_lower] = record
        
        print(f"Cached {len(houses)} houses and {len(accessories)} accessories")
        print(f"Generated {len(DB_CACHE['houses'])} house variations and {len(DB_CACHE['accessories'])} accessory variations")
    except Exception as e:
        print(f"⚠️  Error loading database cache: {e}")
        DB_CACHE["houses"] = {}
        DB_CACHE["accessories"] = {}

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

def get_docx_files(directory: str) -> List[str]:
    """Find all .docx files in directory."""
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

def normalize_name(name: str) -> str:
    """Normalize a name for comparison by removing special characters and extra spaces."""
    # Preserve ACC prefix if present
    acc_prefix = ""
    if name.upper().startswith("ACC "):
        acc_prefix = "ACC "
        name = name[4:]
    
    # Replace common variations
    name = name.replace("'s", "s").replace("&", "and")
    
    # Handle special characters while preserving meaningful ones
    preserved = {
        "'": "'",  # Smart quotes
        "'": "'",  # Smart quotes
        """: '"',  # Smart quotes
        """: '"',  # Smart quotes
        "–": "-",  # En dash
        "—": "-",  # Em dash
        "…": "...", # Ellipsis
    }
    
    for old, new in preserved.items():
        name = name.replace(old, new)
    
    # Remove special characters but keep spaces and hyphens in meaningful positions
    cleaned = ""
    for i, char in enumerate(name):
        if char.isalnum() or char.isspace():
            cleaned += char
        elif char == '-':
            # Keep hyphen if it's between letters (like "Ring-a-Ling")
            if (i > 0 and i < len(name)-1 and 
                (name[i-1].isalnum() or name[i-1].isspace()) and 
                (name[i+1].isalnum() or name[i+1].isspace())):
                cleaned += char
        elif char == '&':
            # Keep & if it's between words
            if (i > 0 and i < len(name)-1 and 
                (name[i-1].isspace() or name[i+1].isspace())):
                cleaned += "and"
    
    # Normalize whitespace
    name = ' '.join(cleaned.split())
    
    # Reapply ACC prefix if it was present
    if acc_prefix:
        name = acc_prefix + name
        
    return name.lower()

def normalize_filename(filename: str) -> str:
    """Normalize filename to sentence case and fix common spelling issues."""
    # Fix common spelling mistakes and standardize names
    spelling_fixes = {
            # Spelling corrections
            "Perect": "Perfect",
            "THink": "Think",
            "TOys": "Toys",
            "Facotry": "Factory", 
            "Cabooxe": "Caboose",
            "Shating": "Skating",
            "MIttens": "Mittens",
            "Christams": "Christmas",
            "Snovys": "Snowy's",
            "Snowys": "Snowy's",
            "Snowy Diner": "Snowy's Diner",
            "Fir Farm": "Needle's Tree Farm", 
            "Tree Farm": "Needle's Tree Farm",
            "Up up and Away": "Animated Flight",
            "Up Up and Away": "Animated Flight",
            "Up, up, and Away": "Animated Flight",
            
            # Standardize reindeer names
            "Donder": "Donner",
            "Dancer & Dasher": "Dasher & Dancer",
            "Vixen & Prancer": "Prancer & Vixen",
            "Blitzen & Donner": "Donner & Blitzen",
            "Cupid & Comet": "Comet & Cupid",
            
            # Common name variations
            "Ring-A-Ling": "Ring-a-Ling",
            "Ring A Ling": "Ring-a-Ling",
            "Ring-a-ling": "Ring-a-Ling",
            "Ring a ling": "Ring-a-Ling",
            "Jingle and Jangle": "Jingle & Jangle",
            "Jingles Bells": "Jingle's Bells",
            "Ring a Ling Bells": "Ring-a-Ling Bells",
            "Ring A Ling Bells": "Ring-a-Ling Bells",
            "Ring-a-Ling Bells": "Ring-a-Ling Bells",
            "Ring-A-Ling Bells": "Ring-a-Ling Bells",
            "Jingle Bells": "Ring-a-Ling Bells",
            "Jingle & Jangle's Bells": "Ring-a-Ling Bells",
            "Jangle's Bells": "Ring-a-Ling Bells",
            "Ring a Ling's": "Ring-a-Ling",
            "Jingles and Jangles": "Ring-a-Ling",
            "Model Train Mfg": "Model Train Manufacturing",
            "Toots Model Train Mfg": "Toot's Model Train Manufacturing",
            "Toot's Train": "Toot's Model Train",
            "All Aboard Toots": "All Aboard at Toot's",
            "Mfg": "Manufacturing",
            "St Nick": "Saint Nick",
            "Saint Nicholas": "Saint Nick",
            
            # Bottom of Form cleanup
            "CadetsBottom": "Cadets",
            "TreesBottom": "Trees",
            "FactoryBottom": "Factory",
            "StationBottom": "Station",
            "Bottom of Form": "",        # Common suffixes to remove
        " Set of 2": "",
        " Set of 3": "",
        " Set of 4": "",
        " set of 2": "",
        " set of 3": "",
        " set of 4": "",
        " No ACC Box": "",
        " No ACC box": "",
        " No Acc Box": "",
        " SANTA": "",
        " CLAUS": "",
        " DESCRIPTION": "",
    }
    
    # Pre-process to handle special characters
    for wrong, right in spelling_fixes.items():
        filename = filename.replace(wrong, right)
        
    # Handle special characters while preserving intended separators
    filename = (filename.replace("  ", " ")  # Remove double spaces
                      .replace("_", " ")     # Convert underscores to spaces
                      .replace(" ,", ",")    # Fix space before comma
                      .replace(" .", ".")     # Fix space before period
                      .replace("( ", "(")     # Fix space after opening paren
                      .replace(" )", ")"))    # Fix space before closing paren
    
    # Split on spaces but preserve quotes and parentheses
    tokens = []
    current_token = []
    in_quotes = False
    in_parens = 0
    
    for char in filename:
        if char == '"' or char == "'":
            in_quotes = not in_quotes
            continue
        elif char == '(':
            in_parens += 1
        elif char == ')':
            in_parens -= 1
        elif char.isspace() and not in_quotes and in_parens == 0:
            if current_token:
                tokens.append(''.join(current_token))
                current_token = []
            continue
        
        current_token.append(char)
    
    if current_token:
        tokens.append(''.join(current_token))
    
    # Process each token
    normalized = []
    for word in tokens:
        # Handle all-caps words (except ACC and common abbreviations)
        if word.isupper() and len(word) > 2 and word not in ["ACC", "DQ", "QC", "DIY", "LED"]:
            word = word.capitalize()
            
        # Preserve hyphenation in multi-word tokens
        if "-" in word and not any(x in word.lower() for x in ["ring-a-ling", "coca-cola", "easy-bake"]):
            parts = [p.capitalize() if p.isupper() and len(p) > 2 else p 
                    for p in word.split("-")]
            word = "-".join(parts)
        
        normalized.append(word)
    
    return " ".join(normalized)

def clean_name(filename: str) -> Tuple[str, Optional[int], bool, str]:
    """Extract clean name, year, if accessory and alternative name from filename."""
    # Normalize filename first
    filename = normalize_filename(filename)
    
    # Check for ACC prefix in any case variation
    acc_patterns = ["acc ", "Acc ", "ACC "]
    is_accessory = any(filename.startswith(prefix) for prefix in acc_patterns)
    name = filename[4:] if is_accessory else filename
    
    # Fix common repeating patterns
    repeating_patterns = [
        (r'Ring-?[Aa]-?[Ll]ing(?:\s+Ring-?[Aa]-?[Ll]ing)+', 'Ring-a-Ling'),  # Fix repeated Ring-a-Ling
        (r'Bell(?:\s+Bell)+', 'Bell'),  # Fix repeated Bell
        (r'Bells(?:\s+Bells)+', 'Bells')  # Fix repeated Bells
    ]
    for pattern, replacement in repeating_patterns:
        name = re.sub(pattern, replacement, name)
    
    # Tag with ACC if this is an accessory and doesn't already have it
    if is_accessory and not any(filename[4:].strip().startswith(prefix) for prefix in acc_patterns):
        name = "ACC " + name
    
    # Try various year patterns
    year_patterns = [
        r'\s*(20\d{2})\s*',  # 2023, 2015 etc
        r'\s*\(?(19\d{2})\)?',  # 1990, (1995) etc
        r'\s*NORTH POLE\s+(19\d{2})',  # NORTH POLE 1991
        r'\s+\'?(\d{2})\s*$',  # '96, 99 etc - convert to 19xx
        r'\s+(?:19|20)(\d{2})\s*$'  # Space followed by year at end
    ]
    
    year = None
    for pattern in year_patterns:
        match = re.search(pattern, name)
        if match:
            year_str = match.group(1)
            if len(year_str) == 2:
                prefix = "19" if int(year_str) > 50 else "20"
                year = int(prefix + year_str)
            else:
                year = int(year_str)
            name = re.sub(pattern, '', name)
            break
    
    # Enhanced handling for reindeer names with more sophisticated matching
    reindeer_names = [
        "Dasher", "Dancer", "Prancer", "Vixen",
        "Comet", "Cupid", "Donner", "Donder", "Blitzen", "Rudolph"
    ]
    
    # Check for reindeer combinations
    found_reindeer = []
    for reindeer in reindeer_names:
        if reindeer.lower() in name.lower():
            found_reindeer.append(reindeer)
            
    if len(found_reindeer) >= 2:
        # Look for known pairs first
        for pair_set, variations in REINDEER_PAIRS.items():
            pair_reindeer = list(pair_set)  # Convert frozenset to list
            if all(r.lower() in [x.lower() for x in found_reindeer] for r in pair_reindeer):
                # Use the first standard variation for this pair
                name = variations[0]
                break
                
        # If no known pair found but we have multiple reindeer, use the first two in standard order
        if name != variations[0]:
            reindeer_order = {r: i for i, r in enumerate(reindeer_names)}  # Define standard order
            found_reindeer.sort(key=lambda x: reindeer_order.get(x, 999))  # Sort by standard order
            name = f"{found_reindeer[0]} & {found_reindeer[1]}"
            
    elif len(found_reindeer) == 1:
        # If only one reindeer found, use it with standardized format
        name = f"Reindeer Stables {found_reindeer[0]}"
    
    # Split into primary and secondary names
    parts = name.split(' 20')[0]  # Remove everything after year if present
    
    # List of important phrases to preserve
    preserved_phrases = [
        "North Pole",
        "Santa's Workshop",
        "Mrs. Claus",
        "Fisher Price",
        "Reindeer Stables",
        "M&M's",
        "M&M",
        "Set of",
        "Ready for",
        "Santa's Little",
        "Home for",
        "Jack in the Box",
        "Santa & Mrs",
        "Coca Cola",
        "Coca-Cola",
        "Perfect Snow",
        "Christmas Eve",
        "I Think You're Cute",
        "She Thinks I'm Cute",
        "She Said I'm Cute",
        "Happy Gnome",
        "Make A Wish",
        "Can I Keep",
        "Ring-A-Ling",
        "Loading the Sleigh",
        "For a Merry Christmas",
        "Make A Bow",
        "Saint Nick's",
        "Gift Sorting Center",
        "Jingle & Jangle",
        "Katie's Candied Apples",
        "Christmas Critters Pet Store",
        "Pet Store",
        "Brite Lites Bulb Factory",
        "Bulb Factory",
        "Toot's Model Train",
        "Train Mfg",
        "Model Train",
        "All in a Tangle",
        "All Aboard",
        "Little Dipper",
        "Dipper",
        "Make A Bow Machine",
        "Bow Machine",
        "Christmas Critters",
        "Gift Center",
        "Sleigh",
        "Loading",
        "Loading the"
    ]
    
    # Replace spaces in preserved phrases with temporary markers
    temp_phrases = {}
    for phrase in preserved_phrases:
        if phrase.lower() in parts.lower():
            marker = f"_PHRASE{len(temp_phrases)}_"
            temp_phrases[marker] = phrase
            parts = re.sub(re.escape(phrase), marker, parts, flags=re.IGNORECASE)
    
    # Split on separators but preserve certain punctuation
    name_parts = []
    current_part = ""
    
    for char in parts:
        if char in [',', '&', '|', '-']:
            if current_part.strip():
                name_parts.append(current_part.strip())
            current_part = ""
        else:
            current_part += char
    
    if current_part.strip():
        name_parts.append(current_part.strip())
    
    # Clean up names
    clean_parts = []
    for part in name_parts:
        # Restore preserved phrases
        for marker, phrase in temp_phrases.items():
            part = part.replace(marker, phrase)
        
        # Standard cleanup with more specific patterns
        cleanup_patterns = [
            (r'\s*\([^)]+\)', ''),  # Remove parentheticals
            (r'\s+set of \d+.*$', ''),  # Remove "set of X" suffixes
            (r'(?i)No ACC [Bb]ox.*$', ''),  # Case-insensitive "No ACC box"
            (r'\s+included in set.*$', ''),
            (r'\s+SANTA.*$', ''),
            (r'\s+CLAUS.*$', ''),
            (r'Bottom of Form.*$', ''),
            (r'\s+[Tt]he$', ''),  # Remove "the" from end
            (r'^[Tt]he\s+', '')  # Remove "the" from start
        ]
        
        for pattern, replacement in cleanup_patterns:
            part = re.sub(pattern, replacement, part)
        
        part = part.strip()
        if part and not part.lower() in ['a', 'an', 'the']:
            clean_parts.append(part)
    
    # Get primary and alternative names
    primary_name = clean_parts[0] if clean_parts else ""
    alt_name = clean_parts[1] if len(clean_parts) > 1 else ""
    
    # Special handling for accessories
    if is_accessory and alt_name:
        # More sophisticated decision for primary name
        primary_score = sum(phrase.lower() in primary_name.lower() for phrase in preserved_phrases)
        alt_score = sum(phrase.lower() in alt_name.lower() for phrase in preserved_phrases)
        
        # If alt_name seems more significant, swap
        if alt_score > primary_score:
            primary_name, alt_name = alt_name, primary_name
    
    return primary_name, year, is_accessory, alt_name

def get_name_variations(name: str) -> Set[str]:
    """Generate likely variations of a name for matching."""
    variations = {name}
    
    # Add normalized version
    variations.add(normalize_name(name))
    
    # Handle ACC prefix variations
    if name.lower().startswith("acc "):
        base_name = name[4:]
        variations.add(base_name)
        variations.add("ACC " + base_name)
        variations.add("Acc " + base_name)
        variations.add("acc " + base_name)
    else:
        # Only add ACC variants if it might be an accessory
        if "accessory" in name.lower() or any(word in name.lower() for word in ["set", "piece", "figure", "ornament"]):
            variations.add("ACC " + name)
    
    # Handle common accessory descriptors
    descriptors = ["set", "set of", "set of 2", "set of 3", "three accessories",
                  "accessory", "accessories", "accessory set", "3 piece set"]
    base_name = name.lower()
    for desc in descriptors:
        base_name = base_name.replace(desc.lower(), "").strip()
    if base_name != name.lower():
        variations.add(base_name.title())
        variations.add("ACC " + base_name.title())
        variations.add(normalize_name(base_name))
    
    # Handle possessives and apostrophes
    variations.add(name.replace("'s", "s"))
    variations.add(name.replace("s", "'s"))
    variations.add(name.replace("'", ""))
    
    # Handle common abbreviations and titles
    variations.add(name.replace("Saint", "St"))
    variations.add(name.replace("St", "Saint"))
    variations.add(name.replace("Mrs.", "Mrs"))
    variations.add(name.replace("Mrs", "Mrs."))
    variations.add(name.replace("Mr.", "Mr"))
    variations.add(name.replace("Mr", "Mr."))
    
    # Handle special characters and conjunctions
    variations.add(name.replace("&", "and"))
    variations.add(name.replace("and", "&"))
    variations.add(name.replace("-", " "))
    variations.add(name.replace(" - ", " "))
    variations.add(name.replace("!", ""))
    
    # Handle numbers and special formatting
    variations.add(name.replace("#", "No."))
    variations.add(name.replace("No.", "#"))
    variations.add(re.sub(r'\d+', '', name).strip())  # Remove all numbers
    
    # Remove common articles and prefixes from start
    for prefix in ["the ", "a ", "an ", "acc ", "set of "]:
        if name.lower().startswith(prefix):
            variations.add(name[len(prefix):])
    
    # Special handling for common suffixes
    suffixes = [
        r'\s+Set of \d+.*$',
        r'\s+No ACC [Bb]ox.*$',
        r'\s+included in set.*$',
        r'\s+Bottom of Form.*$',
        r'\s+\([^)]+\).*$',  # Remove parentheticals
        r'\s+SANTA.*$',
        r'\s+CLAUS.*$',
        r'\s+The$'  # Remove "The" from end
    ]
    
    for suffix in suffixes:
        match = re.search(f'(.*?){suffix}', name)
        if match:
            variations.add(match.group(1))
    
    # Special handling for North Pole variations
    if "North Pole" in name:
        variations.add(name.replace("North Pole", "NP"))
        variations.add(name.replace("NP", "North Pole"))
        
        # Handle common North Pole compound names
        np_patterns = [
            "North Pole's",
            "North Pole Village",
            "North Pole Gate",
            "North Pole Palace"
        ]
        for pattern in np_patterns:
            if pattern in name:
                variations.add(name.replace(pattern, "North Pole"))
                variations.add(name.replace(pattern, "NP"))
    
    # Special handling for Reindeer Stables
    if any(x in name for x in ["Reindeer", "Stables", "Dancer", "Prancer", "Vixen", "Comet", "Cupid", "Donner", "Donder", "Blitzen", "Rudolph"]):
        # Try to extract reindeer names with improved pattern
        reindeer_match = re.search(r'(?:.*?Reindeer\s*Stables[,\s]+)?([A-Za-z\s&]+)(?:\s+(?:19|20)\d{2})?$', name)
        if reindeer_match:
            reindeer_part = reindeer_match.group(1).strip()
            
            # Add variations with different Stables formats
            variations.add(f"Reindeer Stables {reindeer_part}")
            variations.add(f"{reindeer_part} Reindeer Stables")
            variations.add(reindeer_part)
            
            # Handle individual reindeer names and pairs
            reindeer_parts = re.split(r'\s*(?:&|and)\s*', reindeer_part)
            for i, reindeer in enumerate(reindeer_parts):
                clean_reindeer = reindeer.strip()
                if clean_reindeer:
                    # Add individual reindeer variations
                    variations.add(clean_reindeer)
                    variations.add(f"{clean_reindeer} Reindeer Stables")
                    variations.add(f"Reindeer Stables {clean_reindeer}")
                    
                    # Handle pairs (both orders)
                    for j, other in enumerate(reindeer_parts):
                        if i != j:
                            clean_other = other.strip()
                            pair = f"{clean_reindeer} & {clean_other}"
                            variations.add(pair)
                            variations.add(f"Reindeer Stables {pair}")
                            variations.add(f"{pair} Reindeer Stables")
                            # Also add reverse order
                            pair_rev = f"{clean_other} & {clean_reindeer}"
                            variations.add(pair_rev)
                            variations.add(f"Reindeer Stables {pair_rev}")
                            variations.add(f"{pair_rev} Reindeer Stables")
    
    # Handle hyphenated or space-separated multi-word phrases
    if "-" in name or "  " in name:
        parts = re.split(r'[-\s]+', name)
        variations.add(" ".join(parts))
        variations.add("-".join(parts))
    
    return variations

def extract_images(docx_path: str) -> List[Tuple[bytes, str]]:
    """Extract images from .docx file."""
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

def upload_image_to_supabase(
    supabase: Client,
    image_data: bytes,
    filename: str,
    max_retries: int = 3
) -> Optional[str]:
    """Upload image to Supabase Storage with retries."""
    for attempt in range(max_retries):
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
            if "already exists" in str(e).lower():
                try:
                    # Try to update existing file
                    response = supabase.storage.from_("dept56-images").update(
                        filename,
                        image_data,
                        file_options={"content-type": "image/jpeg"}
                    )
                    public_url = supabase.storage.from_("dept56-images").get_public_url(filename)
                    return public_url
                except Exception as update_error:
                    print(f"   ⚠️ Error updating existing image {filename}: {update_error}")
            
            if attempt < max_retries - 1:
                print(f"   ⚠️ Upload failed, retrying ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            print(f"   ❌ Error uploading image {filename}: {e}")
            return None
    
    return None

def find_db_record_by_name(
    supabase: Client,
    name: str,
    table: str = "houses"
) -> Optional[Dict]:
    """Find a database record using flexible name matching strategies."""
    try:
        # Get name variations
        variations = get_name_variations(name)
        
        # Try exact matches first using cache
        cache = DB_CACHE[table]
        
        # Try direct matches first
        for var in variations:
            var_lower = var.lower()
            if var_lower in cache:
                print(f"   ✓ Found exact match: {cache[var_lower]['name']}")
                return cache[var_lower]
                
        # Try to handle special formatting cases
        cleaned_name = name.lower()
        cleaned_name = cleaned_name.replace("'s", "s").replace("-", " ").replace("&", "and")
        
        # Special case handlers
        if "can i keep them" in cleaned_name:
            # Check for variations of "Can I Keep Them"
            for record_name, record in cache.items():
                if "can i keep them" in record_name:
                    print(f"   ✓ Found special case match: {record['name']}")
                    return record
                    
        if "ring a ling" in cleaned_name or "ring-a-ling" in cleaned_name or "bell" in cleaned_name:
            # Look for bell-related accessories with improved matching
            for record_name, record in cache.items():
                record_lower = record_name.lower()
                # Check for various bell-related patterns
                if (("bell" in record_lower or "ring" in record_lower) and 
                    any(x in record_lower for x in ["jingle", "ring", "chime", "ding", "carol"])):
                    score = 0
                    # Score based on matching terms
                    if "ring" in cleaned_name and "ring" in record_lower: score += 2
                    if "bell" in cleaned_name and "bell" in record_lower: score += 2
                    if "jingle" in cleaned_name and "jingle" in record_lower: score += 2
                    if any(x in cleaned_name for x in ["ding", "dong"]) and any(x in record_lower for x in ["ding", "dong"]): score += 1
                    if score >= 2:  # Require at least 2 matching terms
                        print(f"   ✓ Found bell match: {record['name']} (score: {score})")
                        return record
                    
        if any(x in cleaned_name for x in ["loading", "sleigh", "gift", "toy", "present", "delivery", "prep", "flight", "flying", "up", "away"]):
            # Enhanced matching for sleigh/flight/loading related accessories with more flexible scoring
            best_match = None
            best_score = 0
            
            for record_name, record in cache.items():
                record_lower = record_name.lower()
                score = 0
                
                # Core concepts with more variations
                sleigh_terms = ["sleigh", "sled", "delivery", "loading", "packed", "flight", "flying", "animated"]
                if any(term in record_lower for term in sleigh_terms):
                    if any(term in cleaned_name for term in sleigh_terms):
                        score += 4  # Higher score for sleigh/flight-related matches
                        # Extra points for flight/animated matches
                        if any(x in cleaned_name and x in record_lower for x in ["flight", "flying", "up", "away", "animated"]):
                            score += 3
                
                # Action verbs
                action_terms = ["loading", "preparing", "packing", "getting", "ready", "helping"]
                if any(term in record_lower for term in action_terms):
                    if any(term in cleaned_name for term in action_terms):
                        score += 3
                
                # Related concepts with expanded terms
                gift_terms = ["gift", "toy", "present", "package", "delivery", "supplies"]
                for term in gift_terms:
                    if term in record_lower and term in cleaned_name:
                        score += 2
                    elif term in record_lower or term in cleaned_name:
                        score += 1
                
                # Context terms with more holiday specifics
                context_terms = ["santa", "christmas", "workshop", "elf", "pack", "holiday", "merry", "north pole"]
                for term in context_terms:
                    if term in record_lower and term in cleaned_name:
                        score += 2
                    elif term in record_lower or term in cleaned_name:
                        score += 1
                
                # Additional score for year match if available
                if record.get("year"):
                    try:
                        record_year = int(record.get("year", 0))
                        name_parts = cleaned_name.split()
                        # Look for year in the name
                        for part in name_parts:
                            if part.isdigit() and len(part) == 4:
                                doc_year = int(part)
                                if abs(record_year - doc_year) <= 2:
                                    score += 2
                                break
                    except (ValueError, TypeError):
                        pass  # Skip year comparison if there are any conversion issues
                
                # Boost score if it looks like a clear match
                if (("loading" in cleaned_name and "loading" in record_lower) or
                    ("sleigh" in cleaned_name and "sleigh" in record_lower)):
                    score *= 1.5
                    
                if score > best_score:
                    best_score = score
                    best_match = record
            
            if best_score >= 6:  # Adjusted threshold for more flexible matching
                print(f"   ✓ Found loading/sleigh match: {best_match['name']} (score: {best_score})")
                return best_match
                    
            # Use global REINDEER_PAIRS        # Look for reindeer names
        found_reindeer = set()
        for reindeer in ["dasher", "dancer", "prancer", "vixen", "comet", "cupid", "donner", "donder", "blitzen"]:
            if reindeer in cleaned_name:
                found_reindeer.add(reindeer)
        
            # Check for matching pairs using fuzzy logic
            for pair_set, pair_variations in REINDEER_PAIRS.items():
                if found_reindeer & pair_set:  # If any intersection
                    matched_records = []
                    
                    # Look for any of the variations in the cache
                    for record_name, record in cache.items():
                        record_name_lower = record_name.lower()
                        score = 0
                        
                        # Check for exact pair matches first
                        for pair_name in pair_variations:
                            if pair_name.lower() in record_name_lower:
                                score += 10  # High score for exact matches
                                
                        # Check for individual reindeer names
                        found_count = 0
                        for reindeer in pair_set:
                            if reindeer.lower() in record_name_lower:
                                found_count += 1
                                
                        if found_count == 2:
                            score += 5  # Good score for finding both reindeer
                        elif found_count == 1:
                            score += 2  # Low score for finding one reindeer
                            
                        # Check for contextual words
                        for word in ["stable", "stables", "reindeer"]:
                            if word in record_name_lower:
                                score += 1  # Bonus for contextual words
                                
                        if score > 0:
                            matched_records.append((record, score))
                    
                    if matched_records:
                        # Sort by score descending
                        matched_records.sort(key=lambda x: x[1], reverse=True)
                        print(f"   ✓ Found reindeer match: {matched_records[0][0]['name']} (score: {matched_records[0][1]})")
                        return matched_records[0][0]        # Special handling for tree-related items
        if any(x in cleaned_name for x in ["tree", "fir", "forest", "wood", "pine"]):
            for record_name, record in cache.items():
                record_lower = record_name.lower()
                if any(x in record_lower for x in ["tree farm", "needle", "pine", "fir", "forest"]):
                    print(f"   ✓ Found tree match: {record['name']}")
                    return record

        # Try normalized partial matches
        normalized = normalize_name(name)
        words = normalized.split()
        meaningful_words = [w for w in words if len(w) > 2]  # Allow shorter meaningful words
        
        if meaningful_words:
            # Search through cached records
            matches = []
            for record_name, record in cache.items():
                # Try to find matches by groups of meaningful words
                word_groups = []
                for i in range(len(meaningful_words)):
                    for j in range(i + 2, min(i + 5, len(meaningful_words) + 1)):
                        word_group = " ".join(meaningful_words[i:j])
                        if len(word_group) > 3:  # Only use groups with enough characters
                            word_groups.append(word_group)
                
                # Score matches based on both individual words and word groups
                word_score = sum(1 for word in meaningful_words if word in record_name)
                group_score = sum(1 for group in word_groups if group in record_name)
                total_score = word_score + (group_score * 2)  # Weight groups more heavily
                
                if total_score > len(meaningful_words) / 2:
                    matches.append((record, total_score))
            
            if matches:
                # Sort by score descending
                matches.sort(key=lambda x: x[1], reverse=True)
                
                if len(matches) == 1 or matches[0][1] > matches[1][1] * 1.5:
                    # Take best match if it's significantly better
                    print(f"   ✓ Found best match: {matches[0][0]['name']} (score: {matches[0][1]})")
                    return matches[0][0]
                
                # Handle special cases for ambiguous matches
                best_matches = [m for m in matches if m[1] >= matches[0][1] * 0.8]
                if len(best_matches) > 1:
                    # Look for matches that better preserve phrase order
                    normalized_input = " ".join(meaningful_words)
                    best_order_score = 0
                    best_order_match = None
                    
                    for match, _ in best_matches:
                        record_words = normalize_name(match["name"]).split()
                        # Calculate longest common subsequence to check phrase order
                        lcs_length = 0
                        last_pos = -1
                        for word in meaningful_words:
                            for i, rec_word in enumerate(record_words[last_pos + 1:], last_pos + 1):
                                if word == rec_word:
                                    lcs_length += 1
                                    last_pos = i
                                    break
                        if lcs_length > best_order_score:
                            best_order_score = lcs_length
                            best_order_match = match
                    
                    if best_order_match:
                        print(f"   ✓ Found order-preserving match: {best_order_match['name']}")
                        return best_order_match
        
        print(f"   ⚠️ No match found for '{name}'")
        return None
        
    except Exception as e:
        print(f"   ⚠️ Error finding record '{name}' in {table}: {e}")
        return None

def update_photo_url(
    supabase: Client,
    id: str,
    photo_url: str,
    table: str = "houses"
) -> bool:
    """Update photo URL for a record."""
    try:
        result = supabase.table(table).update({"photo_url": photo_url}).eq("id", id).execute()
        return bool(result.data)
    except Exception as e:
        print(f"⚠️  Error updating photo URL for {id} in {table}: {e}")
        return False

def process_document_photos(
    docx_path: str,
    supabase: Client,
    state: Dict
) -> Dict:
    """
    Process a single Word document, focusing on photo extraction and upload.
    Returns processing results.
    """
    filename = os.path.basename(docx_path)
    stem = pathlib.Path(docx_path).stem
    
    print(f"\n📄 Processing photos: {filename}")
    
    result = {
        "file": filename,
        "path": docx_path,
        "success": False,
        "error": None,
        "images_uploaded": 0,
        "house_id": None,
        "house_name": None,
        "accessory_ids": [],
        "accessory_names": []
    }
    
    try:
        # Extract images
        images = extract_images(docx_path)
        if not images:
            print("   ⚠️ No images found")
            result["error"] = "No images found in document"
            return result
        
        print(f"   🖼️  Found {len(images)} image(s)")
        
        # Clean filename and get record
        name_clean, year, is_accessory, alt_name = clean_name(stem)
        if year:
            print(f"   📅 Detected year: {year}")
        
        # Find database record
        table = "accessories" if is_accessory else "houses"
        record = find_db_record_by_name(supabase, name_clean, table)
        
        if not record and alt_name:
            # Try alternative name if primary match failed
            alt_record = find_db_record_by_name(supabase, alt_name, table)
            if alt_record:
                record = alt_record
                
        if not record:
            # Try combining names if both parts failed
            if alt_name:
                combined_name = f"{name_clean} {alt_name}"
                combined_record = find_db_record_by_name(supabase, combined_name, table)
                if combined_record:
                    record = combined_record
            
            if not record:
                print(f"   ⚠️ Could not find matching {table} record for '{name_clean}'")
                result["error"] = f"No matching {table} record found"
                return result
        
        # Upload all images
        uploaded_urls = []
        for i, (image_data, ext) in enumerate(images):
            suffix = f"_{i+1}" if i > 0 else ""
            image_filename = f"{record['id']}/primary{suffix}{ext}"
            
            image_url = upload_image_to_supabase(supabase, image_data, image_filename)
            if image_url:
                uploaded_urls.append(image_url)
                result["images_uploaded"] += 1
        
        if uploaded_urls:
            # Update database with image URLs
            updates = {"photo_url": uploaded_urls[0]}  # Primary photo
            try:
                # Check for additional_photos support first
                if len(uploaded_urls) > 1 and table == "houses":
                    updates["additional_photos"] = uploaded_urls[1:]
                
                # Do the update
                if supabase.table(table).update(updates).eq("id", record["id"]).execute():
                    print(f"   ✅ Updated {len(uploaded_urls)} photo(s) for {record['name']}")
                    
                    if is_accessory:
                        result["accessory_ids"].append(record["id"])
                        result["accessory_names"].append(record["name"])
                    else:
                        result["house_id"] = record["id"]
                        result["house_name"] = record["name"]
                        
                    result["success"] = True
            except Exception as e:
                if "additional_photos" in str(e):
                    # Try without additional photos if the column doesn't exist
                    try:
                        updates.pop("additional_photos", None)
                        if supabase.table(table).update(updates).eq("id", record["id"]).execute():
                            print(f"   ✅ Updated primary photo for {record['name']}")
                            
                            if is_accessory:
                                result["accessory_ids"].append(record["id"])
                                result["accessory_names"].append(record["name"])
                            else:
                                result["house_id"] = record["id"]
                                result["house_name"] = record["name"]
                                
                            result["success"] = True
                    except Exception as e2:
                        print(f"   ❌ Error updating photos: {e2}")
                else:
                    print(f"   ❌ Error updating photos: {e}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"   ❌ Error: {e}")
    
    return result

def process_batch(
    docx_files: List[str],
    start_idx: int,
    batch_size: int,
    total_files: int,
    state: Dict,
    max_retries: int = 3
) -> List[Dict]:
    """Process a batch of documents with retries."""
    results = []
    end_idx = min(start_idx + batch_size, total_files)
    
    for i in range(start_idx, end_idx):
        docx_path = docx_files[i]
        file_key = os.path.basename(docx_path)
        
        # Skip if already successfully processed
        if file_key in state["processed_files"] and state["processed_files"][file_key].get("images_uploaded", 0) > 0:
            print(f"\n[{i+1}/{total_files}] Skipping already processed: {file_key}")
            cached_result = state["processed_files"][file_key].copy()
            cached_result["success"] = True
            cached_result["file"] = file_key
            results.append(cached_result)
            continue
            
        print(f"\n[{i+1}/{total_files}]", end=" ")
        
        # Try processing with retries
        for attempt in range(max_retries):
            try:
                result = process_document_photos(docx_path, supabase, state)
                
                if result["success"] or "No images found" in str(result.get("error", "")):
                    results.append(result)
                    break
                    
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Retry {attempt + 1}/{max_retries}...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"   ❌ Failed after {max_retries} attempts")
                    results.append(result)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Error, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2 ** attempt)
                else:
                    print(f"   ❌ Fatal error: {e}")
                    results.append({
                        "file": file_key,
                        "path": docx_path,
                        "success": False,
                        "error": str(e)
                    })
        
        # Update state after each successful document
        if results[-1]["success"]:
            state["processed_files"][file_key] = {
                "path": docx_path,
                "images_uploaded": results[-1].get("images_uploaded", 0),
                "house_id": results[-1].get("house_id"),
                "house_name": results[-1].get("house_name"),
                "accessory_ids": results[-1].get("accessory_ids", []),
                "accessory_names": results[-1].get("accessory_names", []),
                "last_processed": datetime.now().isoformat()
            }
            save_state(state)  # Save state after each successful file
            
    return results

def main():
    """Main entry point for photo re-upload script."""
    print("=" * 60)
    print("Department 56 Photo Re-upload Script")
    print("=" * 60)
    print(f"\nSource: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Ensure output directory exists
    ensure_dir(OUTPUT_DIR)
    
    # Load processing state
    state = load_state()
    
    # Load database cache
    load_db_cache(supabase)
    
    # Find all .docx files
    print("\nScanning for .docx files...")
    docx_files = get_docx_files(SOURCE_DIR)
    total_files = len(docx_files)
    print(f"Found {total_files} document(s)")
    
    if not docx_files:
        print("❌ No .docx files found. Check the source directory.")
        return
        
    # Sort files to process accessories after their main pieces
    docx_files.sort(key=lambda x: os.path.basename(x).lower().startswith("acc "))
    
    # Process in batches
    BATCH_SIZE = 10
    results = []
    
    try:
        for start_idx in range(0, total_files, BATCH_SIZE):
            print(f"\nProcessing batch {(start_idx // BATCH_SIZE) + 1}...")
            batch_results = process_batch(docx_files, start_idx, BATCH_SIZE, total_files, state)
            results.extend(batch_results)
            
            # Show interim summary for batch
            batch_successful = sum(1 for r in batch_results if r["success"])
            batch_images = sum(r.get("images_uploaded", 0) for r in batch_results)
            print(f"\nBatch summary:")
            print(f"Processed: {len(batch_results)}")
            print(f"Successful: {batch_successful}")
            print(f"Images uploaded: {batch_images}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
    finally:
        # Save final state
        save_state(state)
        print(f"\nState saved: {STATE_FILE}")
        
        # Generate final summary report
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        total_images = sum(r.get("images_uploaded", 0) for r in results)
        updated_houses = sum(1 for r in results if r.get("house_id"))
        updated_accessories = sum(len(r.get("accessory_ids", [])) for r in results)
        
        print(f"Total processed: {len(results)}/{total_files}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Images uploaded: {total_images}")
        print(f"Houses updated: {updated_houses}")
        print(f"Accessories updated: {updated_accessories}")
        
        # Save summary CSV
        summary_path = os.path.join(OUTPUT_DIR, f"photo_update_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("File,Type,Success,Images,House ID,House Name,Accessory IDs,Accessory Names,Error\n")
            for r in results:
                row = [
                    r["file"],
                    "Accessory" if r["file"].startswith("ACC ") else "House",
                    "YES" if r["success"] else "NO",
                    str(r.get("images_uploaded", 0)),
                    r.get("house_id", ""),
                    r.get("house_name", ""),
                    "|".join(r.get("accessory_ids", [])),
                    "|".join(r.get("accessory_names", [])),
                    r.get("error", "")[:50] if r.get("error") else ""
                ]
                f.write(",".join(f'"{str(x)}"' for x in row) + "\n")
        
        print(f"\nSummary saved: {summary_path}")
        print("\nPhoto update complete!")

if __name__ == "__main__":
    main()