"""
Execute SQL migrations on Supabase
"""
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

load_dotenv()

def run_sql_file(supabase, filepath: str):
    """Execute a SQL file on Supabase"""
    print(f"\n{'='*70}")
    print(f"Executing: {filepath}")
    print(f"{'='*70}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Split by semicolon for multiple statements
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for i, statement in enumerate(statements, 1):
        # Skip comments
        if statement.startswith('--') or not statement:
            continue
        
        print(f"[{i}/{len(statements)}] Executing statement...")
        try:
            response = supabase.rpc('exec_sql', {'query': statement}).execute()
            print(f"  ✅ Success")
        except Exception as e:
            # Some statements might not be supported via RPC, show the error
            print(f"  ⚠️  {str(e)[:100]}")
    
    print(f"\n✅ Completed: {filepath}\n")

def main():
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("\n" + "="*70)
    print("SUPABASE SQL MIGRATION RUNNER")
    print("="*70)
    
    # Migration file
    migration_file = "migration_add_all_fields.sql"
    
    if not Path(migration_file).exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"\nThis will execute: {migration_file}")
    print("\nNOTE: Due to Supabase limitations, you may need to run this manually in the SQL Editor.")
    print("This script will show you the SQL to copy.")
    
    # Show the SQL
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    print(f"\n{'='*70}")
    print("COPY THIS SQL TO SUPABASE SQL EDITOR:")
    print(f"{'='*70}\n")
    print(sql)
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
