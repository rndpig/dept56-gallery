"""
Link Images to Database Records
Updates photo_url fields in houses and accessories tables with Supabase Storage URLs

Author: GitHub Copilot
Date: October 18, 2025
"""

import os
import re
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class ImageLinker:
    """Link uploaded images to database records"""
    
    def __init__(self):
        # Initialize Supabase client with service role key
        supabase_url = os.getenv("VITE_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "dept56-images"
        self.user_id = os.getenv("SUPABASE_USER_ID")
        
        if not self.user_id:
            raise ValueError("Missing SUPABASE_USER_ID in .env file")
        
        self.base_url = f"{supabase_url}/storage/v1/object/public/{self.bucket_name}/{self.user_id}"
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for comparison (remove special chars, lowercase, spaces to underscores)"""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^\w\s-]', '', name).strip()
        # Replace spaces with underscores
        normalized = normalized.replace(' ', '_')
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.lower()
    
    def get_storage_files(self):
        """Get all files from Supabase Storage"""
        print(f"\n{'='*70}")
        print(f"FETCHING STORAGE FILES")
        print(f"{'='*70}\n")
        
        # Fetch all files with pagination
        all_files = []
        offset = 0
        limit = 1000  # Supabase max limit
        
        while True:
            files = self.supabase.storage.from_(self.bucket_name).list(
                self.user_id,
                {
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if not files:
                break
            
            all_files.extend(files)
            
            if len(files) < limit:
                break
            
            offset += limit
        
        print(f"Found {len(all_files)} files in storage")
        
        # Create mapping: normalized_name -> full_filename
        storage_map = {}
        for file in all_files:
            filename = file['name']
            # Extract item name and type from filename (e.g., "Fisher_Price_Pull_Toy_Factory_house.jpg")
            if filename.endswith('_house.jpg') or filename.endswith('_house.png'):
                item_name = filename.replace('_house.jpg', '').replace('_house.png', '')
                item_type = 'house'
            elif filename.endswith('_accessory.jpg') or filename.endswith('_accessory.png'):
                item_name = filename.replace('_accessory.jpg', '').replace('_accessory.png', '')
                item_type = 'accessory'
            else:
                continue
            
            normalized_name = self.normalize_name(item_name)
            storage_map[f"{item_type}:{normalized_name}"] = filename
        
        print(f"Mapped {len(storage_map)} images")
        return storage_map
    
    def update_houses(self, storage_map):
        """Update house records with image URLs"""
        print(f"\n{'='*70}")
        print(f"UPDATING HOUSE IMAGES")
        print(f"{'='*70}\n")
        
        # Fetch all houses
        response = self.supabase.table('houses').select('id, name, photo_url').execute()
        houses = response.data
        
        print(f"Found {len(houses)} houses in database")
        
        updated = 0
        not_found = 0
        already_set = 0
        
        for house in houses:
            # Skip if photo_url already set
            if house.get('photo_url'):
                already_set += 1
                continue
            
            # Normalize house name for lookup
            normalized_name = self.normalize_name(house['name'])
            lookup_key = f"house:{normalized_name}"
            
            # Find matching file
            if lookup_key in storage_map:
                filename = storage_map[lookup_key]
                photo_url = f"{self.base_url}/{filename}"
                
                # Update database
                self.supabase.table('houses').update({
                    'photo_url': photo_url
                }).eq('id', house['id']).execute()
                
                updated += 1
                if updated <= 5 or updated % 50 == 0:
                    print(f"  ✅ [{updated}] {house['name']}")
            else:
                not_found += 1
                if not_found <= 5:
                    print(f"  ⚠️  No image found for: {house['name']} (looking for: {normalized_name})")
        
        print(f"\n{'─'*70}")
        print(f"Houses Summary:")
        print(f"  Updated:     {updated}")
        print(f"  Not Found:   {not_found}")
        print(f"  Already Set: {already_set}")
        print(f"{'─'*70}")
        
        return updated, not_found, already_set
    
    def update_accessories(self, storage_map):
        """Update accessory records with image URLs"""
        print(f"\n{'='*70}")
        print(f"UPDATING ACCESSORY IMAGES")
        print(f"{'='*70}\n")
        
        # Fetch all accessories
        response = self.supabase.table('accessories').select('id, name, photo_url').execute()
        accessories = response.data
        
        print(f"Found {len(accessories)} accessories in database")
        
        updated = 0
        not_found = 0
        already_set = 0
        
        for accessory in accessories:
            # Skip if photo_url already set
            if accessory.get('photo_url'):
                already_set += 1
                continue
            
            # Normalize accessory name for lookup
            normalized_name = self.normalize_name(accessory['name'])
            lookup_key = f"accessory:{normalized_name}"
            
            # Find matching file
            if lookup_key in storage_map:
                filename = storage_map[lookup_key]
                photo_url = f"{self.base_url}/{filename}"
                
                # Update database
                self.supabase.table('accessories').update({
                    'photo_url': photo_url
                }).eq('id', accessory['id']).execute()
                
                updated += 1
                if updated <= 5 or updated % 50 == 0:
                    print(f"  ✅ [{updated}] {accessory['name']}")
            else:
                not_found += 1
                if not_found <= 5:
                    print(f"  ⚠️  No image found for: {accessory['name']} (looking for: {normalized_name})")
        
        print(f"\n{'─'*70}")
        print(f"Accessories Summary:")
        print(f"  Updated:     {updated}")
        print(f"  Not Found:   {not_found}")
        print(f"  Already Set: {already_set}")
        print(f"{'─'*70}")
        
        return updated, not_found, already_set
    
    def run(self):
        """Run the complete linking process"""
        print(f"\n{'='*70}")
        print(f"IMAGE LINKER - Connecting Storage to Database")
        print(f"{'='*70}\n")
        print(f"Base URL: {self.base_url}")
        
        # Get storage files
        storage_map = self.get_storage_files()
        
        # Update houses
        houses_updated, houses_not_found, houses_already_set = self.update_houses(storage_map)
        
        # Update accessories
        acc_updated, acc_not_found, acc_already_set = self.update_accessories(storage_map)
        
        # Final summary
        print(f"\n{'='*70}")
        print(f"✅ IMAGE LINKING COMPLETE")
        print(f"{'='*70}")
        print(f"Houses:")
        print(f"  ✅ Linked:       {houses_updated}")
        print(f"  ⚠️  Not Found:   {houses_not_found}")
        print(f"  ℹ️  Already Set: {houses_already_set}")
        print(f"\nAccessories:")
        print(f"  ✅ Linked:       {acc_updated}")
        print(f"  ⚠️  Not Found:   {acc_not_found}")
        print(f"  ℹ️  Already Set: {acc_already_set}")
        print(f"\nTotal Images Linked: {houses_updated + acc_updated}")
        print(f"{'='*70}\n")


def main():
    """Main function"""
    linker = ImageLinker()
    linker.run()


if __name__ == "__main__":
    main()
