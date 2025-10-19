"""
Upload Images to Supabase Storage
Clears the dept56-images bucket and uploads all extracted images

Author: GitHub Copilot
Date: October 18, 2025
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

class ImageUploader:
    """Upload images to Supabase Storage"""
    
    def __init__(self, images_dir: str = "parsed_output/images"):
        self.images_dir = Path(images_dir)
        
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
    
    def clear_bucket(self):
        """Clear all files from the bucket"""
        print(f"\n{'='*70}")
        print(f"CLEARING BUCKET: {self.bucket_name}")
        print(f"{'='*70}\n")
        
        try:
            # List all files in the bucket
            response = self.supabase.storage.from_(self.bucket_name).list()
            
            if not response:
                print("✅ Bucket is already empty")
                return
            
            print(f"Found {len(response)} items in bucket")
            
            # Delete all files
            for item in response:
                file_path = item['name']
                try:
                    self.supabase.storage.from_(self.bucket_name).remove([file_path])
                    print(f"  🗑️  Deleted: {file_path}")
                except Exception as e:
                    print(f"  ⚠️  Could not delete {file_path}: {str(e)}")
            
            # Also try to delete the user folder if it exists
            try:
                user_files = self.supabase.storage.from_(self.bucket_name).list(self.user_id)
                if user_files:
                    file_paths = [f"{self.user_id}/{f['name']}" for f in user_files]
                    self.supabase.storage.from_(self.bucket_name).remove(file_paths)
                    print(f"  🗑️  Deleted {len(file_paths)} files from user folder")
            except Exception as e:
                print(f"  ℹ️  No user folder to clear: {str(e)}")
            
            print(f"\n✅ Bucket cleared successfully\n")
            
        except Exception as e:
            print(f"❌ Error clearing bucket: {str(e)}")
            raise
    
    def upload_images(self):
        """Upload all images to Supabase Storage"""
        if not self.images_dir.exists():
            print(f"❌ Images directory not found: {self.images_dir}")
            return
        
        # Get all image files
        image_files = list(self.images_dir.glob("*.*"))
        image_files = [f for f in image_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']]
        
        if not image_files:
            print(f"❌ No image files found in {self.images_dir}")
            return
        
        print(f"\n{'='*70}")
        print(f"UPLOADING IMAGES TO SUPABASE STORAGE")
        print(f"{'='*70}\n")
        print(f"Bucket: {self.bucket_name}")
        print(f"User folder: {self.user_id}")
        print(f"Total images: {len(image_files)}\n")
        
        uploaded = 0
        failed = 0
        
        for i, image_path in enumerate(image_files, 1):
            # Create storage path: user_id/filename
            storage_path = f"{self.user_id}/{image_path.name}"
            
            try:
                # Read image file
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Determine content type
                content_type = "image/jpeg"
                if image_path.suffix.lower() == '.png':
                    content_type = "image/png"
                elif image_path.suffix.lower() == '.gif':
                    content_type = "image/gif"
                
                # Upload to Supabase Storage
                self.supabase.storage.from_(self.bucket_name).upload(
                    storage_path,
                    image_data,
                    {
                        "content-type": content_type,
                        "upsert": "true"  # Overwrite if exists
                    }
                )
                
                uploaded += 1
                
                # Progress indicator
                if i % 50 == 0 or i == len(image_files):
                    print(f"  [{i}/{len(image_files)}] Uploaded: {image_path.name}")
                
            except Exception as e:
                failed += 1
                print(f"  ❌ Failed to upload {image_path.name}: {str(e)}")
        
        print(f"\n{'='*70}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"  ✅ Uploaded:  {uploaded}")
        print(f"  ❌ Failed:    {failed}")
        print(f"  📁 Total:     {len(image_files)}")
        print(f"{'='*70}\n")
        
        return {
            'uploaded': uploaded,
            'failed': failed,
            'total': len(image_files)
        }
    
    def get_public_urls(self):
        """Get public URLs for all uploaded images"""
        print(f"\n{'='*70}")
        print(f"GENERATING PUBLIC URLS")
        print(f"{'='*70}\n")
        
        # List files in user folder
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(self.user_id)
            
            if not files:
                print("No files found in storage")
                return []
            
            urls = []
            for file in files:
                storage_path = f"{self.user_id}/{file['name']}"
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
                urls.append({
                    'filename': file['name'],
                    'url': public_url
                })
            
            print(f"Generated {len(urls)} public URLs")
            
            # Show a few examples
            print(f"\nExample URLs:")
            for url_info in urls[:3]:
                print(f"  {url_info['filename']}: {url_info['url']}")
            
            return urls
            
        except Exception as e:
            print(f"❌ Error getting public URLs: {str(e)}")
            return []
    
    def run(self):
        """Run the complete upload process"""
        start_time = time.time()
        
        # Clear existing images
        self.clear_bucket()
        
        # Upload new images
        summary = self.upload_images()
        
        # Get public URLs
        urls = self.get_public_urls()
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ IMAGE UPLOAD COMPLETE")
        print(f"{'='*70}")
        print(f"  Time elapsed: {elapsed_time:.2f} seconds")
        print(f"  Bucket: {self.bucket_name}")
        print(f"  User folder: {self.user_id}")
        print(f"{'='*70}\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload images to Supabase Storage')
    parser.add_argument('--images-dir', default='parsed_output/images', help='Directory containing images')
    parser.add_argument('--skip-clear', action='store_true', help='Skip clearing bucket (just add images)')
    
    args = parser.parse_args()
    
    # Create uploader
    uploader = ImageUploader(args.images_dir)
    
    if not args.skip_clear:
        # Clear bucket first
        uploader.clear_bucket()
    
    # Upload images
    uploader.upload_images()
    
    # Get public URLs
    uploader.get_public_urls()


if __name__ == "__main__":
    main()
