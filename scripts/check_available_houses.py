#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.append(str(Path(__file__).parent))

# Import the database connection
from get_user_id import supabase

def check_house_exists(house_name):
    """Check if a house exists in the current database"""
    try:
        result = supabase.table('houses').select('name').ilike('name', f'%{house_name}%').execute()
        return len(result.data) > 0, result.data
    except Exception as e:
        print(f"Error checking database: {e}")
        return False, []

# Test a few house names
test_houses = [
    "48 Doughty St Home",
    "Basel Cheese Shop", 
    "Reit Train Station",
    "5607 Park Avenue Townhouse",
    "Adobe House",
    "Aldeburgh Music Box Shop"
]

print("Checking which houses are NOT in your database:")
print("=" * 50)

available_houses = []
for house in test_houses:
    exists, matches = check_house_exists(house)
    if not exists:
        available_houses.append(house)
        print(f"✅ AVAILABLE: {house}")
    else:
        print(f"❌ Already exists: {house}")
        if matches:
            print(f"   Found as: {matches[0]['name']}")
    print()

print(f"\nHouses available for import: {len(available_houses)}")
if available_houses:
    print(f"Recommended to test: {available_houses[0]}")