from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase 
supabase = create_client(
    os.getenv("VITE_SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Get all accessories
result = supabase.table('accessories').select('name').execute()

# Search for reindeer-related names
reindeer_terms = ['reindeer', 'dasher', 'dancer', 'prancer', 'vixen', 
                  'comet', 'cupid', 'donner', 'donder', 'blitzen']

print("Reindeer-related accessories:")
print("-" * 30)

found = []
for record in result.data:
    name = record['name'].lower()
    if any(term in name for term in reindeer_terms):
        found.append(record['name'])

for name in sorted(found):
    print(f"- {name}")