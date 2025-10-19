"""
Batch Process All Word Documents and Upload to Supabase
Parses all .docx files and uploads the data to Supabase database

Author: GitHub Copilot
Date: October 18, 2025
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from docx_parser_simple import Dept56DocxParser
from supabase import create_client, Client
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class BatchProcessor:
    """Batch process Word documents and upload to Supabase"""
    
    def __init__(self, docs_directory: str, output_dir: str = "parsed_output", user_id: str = None):
        self.docs_directory = Path(docs_directory)
        self.output_dir = Path(output_dir)
        self.parser = Dept56DocxParser(output_dir=str(self.output_dir))
        
        # Initialize Supabase client with service role key (bypasses RLS)
        supabase_url = os.getenv("VITE_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Use provided user ID or get from env
        self.user_id = user_id or os.getenv("SUPABASE_USER_ID")
        
        if not self.user_id:
            print("⚠️  Warning: No user_id provided. Will need to authenticate or provide user ID.")
    
    def set_user_id(self, user_id: str):
        """Set the user ID for uploads"""
        self.user_id = user_id
        print(f"✅ User ID set to: {self.user_id}")
    
    def find_all_documents(self) -> List[Path]:
        """Find all .docx files in the directory"""
        docs = list(self.docs_directory.glob("*.docx"))
        # Filter out temp files that start with ~$
        docs = [d for d in docs if not d.name.startswith("~$")]
        return sorted(docs)
    
    def parse_all_documents(self, docs: List[Path]) -> List[Dict]:
        """Parse all documents and return results"""
        results = []
        
        print(f"\n{'='*70}")
        print(f"PARSING {len(docs)} DOCUMENTS")
        print(f"{'='*70}\n")
        
        for i, doc_path in enumerate(docs, 1):
            print(f"\n[{i}/{len(docs)}] Processing: {doc_path.name}")
            print(f"{'─'*70}")
            
            try:
                result = self.parser.parse_document(str(doc_path))
                results.append(result)
                print(f"✅ Success")
            except Exception as e:
                print(f"❌ Error parsing {doc_path.name}: {str(e)}")
                # Save error info
                results.append({
                    'source_file': doc_path.name,
                    'error': str(e),
                    'houses': [],
                    'accessories': []
                })
        
        return results
    
    def upload_to_supabase(self, results: List[Dict]):
        """Upload parsed results to Supabase"""
        if not self.user_id:
            raise ValueError("Must authenticate before uploading")
        
        print(f"\n{'='*70}")
        print(f"UPLOADING TO SUPABASE")
        print(f"{'='*70}\n")
        
        total_houses = 0
        total_accessories = 0
        errors = []
        skipped_duplicates = []
        
        # Create lookup maps for linking
        # Pre-populate with existing items from database to prevent duplicates
        house_name_to_id = {}
        accessory_name_to_id = {}
        
        print("Loading existing items from database to prevent duplicates...")
        try:
            # Load all existing houses
            existing_houses = self.supabase.table('houses').select('id, name').eq('user_id', self.user_id).execute()
            for house in existing_houses.data:
                house_name_to_id[house['name']] = house['id']
            print(f"  Found {len(existing_houses.data)} existing houses")
            
            # Load all existing accessories
            existing_accessories = self.supabase.table('accessories').select('id, name').eq('user_id', self.user_id).execute()
            for acc in existing_accessories.data:
                accessory_name_to_id[acc['name']] = acc['id']
            print(f"  Found {len(existing_accessories.data)} existing accessories")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not load existing items: {str(e)}")
            print("  Continuing without duplicate detection...")
        
        print()
        
        for result in results:
            if 'error' in result:
                errors.append(result)
                continue
            
            # Upload houses
            for house_data in result.get('houses', []):
                try:
                    house_name = house_data['name']
                    
                    # DUPLICATE CHECK #1: Skip if already exists as a house
                    if house_name in house_name_to_id:
                        print(f"  ⏭️  House already exists: {house_name}")
                        skipped_duplicates.append({'type': 'house', 'name': house_name, 'reason': 'already in houses table'})
                        continue
                    
                    # DUPLICATE CHECK #2: Check if it exists as an accessory (CROSS-TABLE CHECK)
                    if house_name in accessory_name_to_id:
                        print(f"  ⚠️  WARNING: '{house_name}' already exists as ACCESSORY - skipping house upload")
                        skipped_duplicates.append({'type': 'house', 'name': house_name, 'reason': 'already exists as accessory'})
                        errors.append({'type': 'house', 'name': house_name, 'error': 'Item already exists as accessory - possible parser misclassification'})
                        continue
                    
                    # Prepare house record
                    house_record = {
                        'user_id': self.user_id,
                        'name': house_data['name'],
                        'sku': house_data.get('sku'),
                        'description': house_data.get('description'),
                        'notes': house_data.get('notes'),
                        'price': house_data.get('price'),
                        'year': house_data.get('year'),
                        'retired_year': house_data.get('retired_year'),
                        'purchased_year': house_data.get('purchased_year'),
                        'collection': house_data.get('collection'),
                        'series': house_data.get('series'),
                        # TODO: Upload image to storage and set photo_url
                    }
                    
                    # Insert house
                    response = self.supabase.table('houses').insert(house_record).execute()
                    house_id = response.data[0]['id']
                    house_name_to_id[house_data['name']] = house_id
                    
                    total_houses += 1
                    print(f"  ✅ House: {house_data['name']}")
                    
                except Exception as e:
                    print(f"  ❌ Error uploading house {house_data['name']}: {str(e)}")
                    errors.append({'type': 'house', 'name': house_data['name'], 'error': str(e)})
            
            # Upload accessories
            for acc_data in result.get('accessories', []):
                try:
                    acc_name = acc_data['name']
                    
                    # DUPLICATE CHECK #1: Skip if already exists as an accessory
                    if acc_name in accessory_name_to_id:
                        print(f"  ⏭️  Accessory already exists: {acc_name}")
                        skipped_duplicates.append({'type': 'accessory', 'name': acc_name, 'reason': 'already in accessories table'})
                        continue
                    
                    # DUPLICATE CHECK #2: Check if it exists as a house (CROSS-TABLE CHECK)
                    if acc_name in house_name_to_id:
                        print(f"  ⚠️  WARNING: '{acc_name}' already exists as HOUSE - skipping accessory upload")
                        skipped_duplicates.append({'type': 'accessory', 'name': acc_name, 'reason': 'already exists as house'})
                        errors.append({'type': 'accessory', 'name': acc_name, 'error': 'Item already exists as house - possible parser misclassification'})
                        continue
                    
                    # Prepare accessory record
                    acc_record = {
                        'user_id': self.user_id,
                        'name': acc_data['name'],
                        'sku': acc_data.get('sku'),
                        'description': acc_data.get('description'),
                        'notes': acc_data.get('notes'),
                        'price': acc_data.get('price'),
                        'year': acc_data.get('year'),
                        'retired_year': acc_data.get('retired_year'),
                        'purchased_year': acc_data.get('purchased_year'),
                        'collection': acc_data.get('collection'),
                        'series': acc_data.get('series'),
                        # TODO: Upload image to storage and set photo_url
                    }
                    
                    # Insert accessory
                    response = self.supabase.table('accessories').insert(acc_record).execute()
                    acc_id = response.data[0]['id']
                    accessory_name_to_id[acc_data['name']] = acc_id
                    
                    total_accessories += 1
                    print(f"  ✅ Accessory: {acc_data['name']}")
                    
                except Exception as e:
                    print(f"  ❌ Error uploading accessory {acc_data['name']}: {str(e)}")
                    errors.append({'type': 'accessory', 'name': acc_data['name'], 'error': str(e)})
        
        # Create house-accessory links
        print(f"\n{'─'*70}")
        print("Creating house-accessory links...")
        print(f"{'─'*70}\n")
        
        for result in results:
            if 'error' in result:
                continue
            
            for house_data in result.get('houses', []):
                house_name = house_data['name']
                house_id = house_name_to_id.get(house_name)
                
                if not house_id:
                    continue
                
                for linked_acc_name in house_data.get('linked_items', []):
                    acc_id = accessory_name_to_id.get(linked_acc_name)
                    
                    if acc_id:
                        try:
                            link_record = {
                                'house_id': house_id,
                                'accessory_id': acc_id
                            }
                            self.supabase.table('house_accessory_links').insert(link_record).execute()
                            print(f"  🔗 Linked: {house_name} ↔ {linked_acc_name}")
                        except Exception as e:
                            # Might be duplicate, ignore
                            if "duplicate" not in str(e).lower():
                                print(f"  ⚠️  Link error: {house_name} ↔ {linked_acc_name}: {str(e)}")
        
        # Print summary
        print(f"\n{'='*70}")
        print("UPLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"  Houses uploaded:      {total_houses}")
        print(f"  Accessories uploaded: {total_accessories}")
        print(f"  Duplicates skipped:   {len(skipped_duplicates)}")
        print(f"  Errors:               {len(errors)}")
        
        if skipped_duplicates:
            print(f"\n{'─'*70}")
            print("SKIPPED DUPLICATES:")
            print(f"{'─'*70}")
            for skip in skipped_duplicates[:20]:  # Show first 20
                print(f"  - {skip['type'].upper()}: {skip['name']} ({skip['reason']})")
            if len(skipped_duplicates) > 20:
                print(f"  ... and {len(skipped_duplicates) - 20} more")
        
        if errors:
            print(f"\n{'─'*70}")
            print("ERRORS:")
            print(f"{'─'*70}")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
        
        return {
            'total_houses': total_houses,
            'total_accessories': total_accessories,
            'skipped_duplicates': skipped_duplicates,
            'errors': errors
        }
    
    def run(self, skip_upload: bool = False):
        """Run the complete batch process"""
        start_time = time.time()
        
        # Check user ID
        if not skip_upload and not self.user_id:
            print("❌ No user ID set. Use --user-id or set SUPABASE_USER_ID in .env")
            return
        
        # Find all documents
        docs = self.find_all_documents()
        print(f"\nFound {len(docs)} Word documents")
        
        if not docs:
            print("❌ No documents found!")
            return
        
        # Parse all documents
        results = self.parse_all_documents(docs)
        
        # Save consolidated results
        consolidated_path = self.output_dir / "consolidated_results.json"
        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Consolidated results saved to: {consolidated_path}")
        
        if not skip_upload:
            # Upload to Supabase
            summary = self.upload_to_supabase(results)
            
            # Save summary
            summary_path = self.output_dir / "upload_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"  Summary saved to: {summary_path}")
        
        elapsed_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"✅ BATCH PROCESS COMPLETE")
        print(f"{'='*70}")
        print(f"  Time elapsed: {elapsed_time:.2f} seconds")
        print(f"{'='*70}\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process Word documents and upload to Supabase')
    parser.add_argument('docs_dir', help='Directory containing .docx files')
    parser.add_argument('--user-id', help='Supabase user ID (or set SUPABASE_USER_ID in .env)')
    parser.add_argument('--output', default='parsed_output', help='Output directory (default: parsed_output)')
    parser.add_argument('--parse-only', action='store_true', help='Only parse documents, skip upload')
    
    args = parser.parse_args()
    
    # Run batch processor
    processor = BatchProcessor(args.docs_dir, args.output, user_id=args.user_id)
    processor.run(skip_upload=args.parse_only)


if __name__ == "__main__":
    main()
