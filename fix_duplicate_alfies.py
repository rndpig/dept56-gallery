"""
Fix duplicate entries for Alfie's Toy School For Elves Early Release
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

# IDs of the duplicate entries
id_1 = 'ed247b65-3383-438a-a918-c9234e0ca737'  # First entry
id_2 = 'fd236a91-8c9e-42eb-afbe-111488d1b276'  # Second entry

# Get any accessory links for both houses
links_1 = supabase.table('house_accessory_links').select('*').eq('house_id', id_1).execute()
links_2 = supabase.table('house_accessory_links').select('*').eq('house_id', id_2).execute()

print(f"House 1 ({id_1}) has {len(links_1.data)} accessory links")
print(f"House 2 ({id_2}) has {len(links_2.data)} accessory links")

# Keep the first entry (id_1) as it has the simpler filename
# Update its photo URL to use the one from id_2 since that matches your Word doc screenshot
house_1 = supabase.table('houses').select('*').eq('id', id_1).single().execute()
house_2 = supabase.table('houses').select('*').eq('id', id_2).single().execute()

print("\nUpdating photo URL for the house we're keeping...")
supabase.table('houses').update({
    'photo_url': house_2.data['photo_url']
}).eq('id', id_1).execute()

print("Moving any accessory links to the house we're keeping...")
for link in links_2.data:
    # Create new link with id_1
    supabase.table('house_accessory_links').insert({
        'house_id': id_1,
        'accessory_id': link['accessory_id']
    }).execute()

print("Deleting the duplicate house entry...")
supabase.table('houses').delete().eq('id', id_2).execute()

print("\n✅ Done! The duplicate has been removed and all data is preserved.")
print("💡 Refresh your browser to see the changes.")