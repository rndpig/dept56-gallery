"""
Fix RLS Policies for Single-User Mode

This script updates the Row Level Security (RLS) policies in the Supabase database
to allow access when running in single-user mode (no authentication).

The issue: All data has user_id = NULL, and auth.uid() = NULL, but NULL = NULL
evaluates to FALSE in SQL, so RLS policies block all access.

The solution: Update policies to allow access when user_id IS NULL (single-user mode).

Usage:
    python scripts/maintenance/fix_rls_policies.py

Requirements:
    - SUPABASE_SERVICE_ROLE_KEY environment variable must be set
    - fix_rls_policies.sql file must exist in the project root
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests

def main():
    # Load environment variables
    load_dotenv()
    
    url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("ERROR: Missing required environment variables")
        print("  VITE_SUPABASE_URL:", "✓" if url else "✗")
        print("  SUPABASE_SERVICE_ROLE_KEY:", "✓" if service_key else "✗")
        return 1
    
    # Read the SQL migration file
    sql_file = Path(__file__).parent.parent.parent / 'fix_rls_policies.sql'
    if not sql_file.exists():
        print(f"ERROR: SQL file not found: {sql_file}")
        return 1
    
    print(f"Reading SQL migration from: {sql_file}")
    sql_content = sql_file.read_text()
    
    print("\nApplying RLS policy fixes...")
    print("="*70)
    
    # Try to execute SQL using Supabase REST API
    # Extract project reference from URL
    project_ref = url.replace('https://', '').split('.')[0]
    
    # Use the Supabase SQL endpoint
    sql_url = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec_sql"
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Try executing via RPC (this may not work for DDL statements)
        response = requests.post(
            sql_url,
            headers=headers,
            json={'query': sql_content}
        )
        
        if response.status_code == 200:
            print("✓ Successfully applied RLS policy fixes")
            return 0
        else:
            # This approach doesn't work, provide manual instructions
            raise Exception(f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"\nNote: Could not execute SQL automatically: {e}")
        print("\n" + "="*70)
        print("PLEASE APPLY SQL MANUALLY")
        print("="*70)
        print("\nGo to Supabase Dashboard and run the SQL:\n")
        print("  1. Go to: https://xctottgirqkkmjmutoon.supabase.co")
        print("  2. Navigate to: SQL Editor (in left sidebar)")
        print("  3. Click: 'New query'")
        print(f"  4. Open and copy contents from: {sql_file.absolute()}")
        print("  5. Paste into SQL Editor and click 'Run'")
        print("\n" + "="*70)
        return 1

if __name__ == '__main__':
    exit(main())
