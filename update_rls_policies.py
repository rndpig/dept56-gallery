"""
Update RLS policies to allow public access
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use service role key for admin operations
supabase = create_client(
    os.getenv('VITE_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def main():
    print("\n🔧 Updating RLS policies for public access...")
    
    try:
        # Drop existing policies
        print("\nDropping existing RLS policies...")
        supabase.query("""
            DROP POLICY IF EXISTS "Users can view own houses" ON houses;
            DROP POLICY IF EXISTS "Users can view own accessories" ON accessories;
            DROP POLICY IF EXISTS "Users can view own collections" ON collections;
            DROP POLICY IF EXISTS "Users can view own tags" ON tags;
            DROP POLICY IF EXISTS "Users can view own house_accessory_links" ON house_accessory_links;
            DROP POLICY IF EXISTS "Users can view own house_collections" ON house_collections;
            DROP POLICY IF EXISTS "Users can view own accessory_collections" ON accessory_collections;
            DROP POLICY IF EXISTS "Users can view own house_tags" ON house_tags;
            DROP POLICY IF EXISTS "Users can view own accessory_tags" ON accessory_tags;
        """).execute()
        
        # Create new public SELECT policies
        print("Creating new public SELECT policies...")
        supabase.query("""
            CREATE POLICY "Public can view houses"
                ON houses FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view accessories"
                ON accessories FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view collections"
                ON collections FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view tags"
                ON tags FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view house_accessory_links"
                ON house_accessory_links FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view house_collections"
                ON house_collections FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view accessory_collections"
                ON accessory_collections FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view house_tags"
                ON house_tags FOR SELECT
                USING (true);
            
            CREATE POLICY "Public can view accessory_tags"
                ON accessory_tags FOR SELECT
                USING (true);
        """).execute()
        
        print("\n✅ Successfully updated RLS policies!")
        print("Now let's test the access...")
        
        # Test access
        houses = supabase.table('houses').select('*').execute()
        accessories = supabase.table('accessories').select('*').execute()
        
        print(f"\nFound {len(houses.data)} houses")
        print(f"Found {len(accessories.data)} accessories")
        
        if houses.data:
            print("\nSample house:", houses.data[0]['name'])
        if accessories.data:
            print("Sample accessory:", accessories.data[0]['name'])
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        
    print("\n💡 Now refresh your browser to see if the data loads properly.")

if __name__ == '__main__':
    main()