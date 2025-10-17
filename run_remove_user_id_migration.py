"""
Run SQL Migration to Remove user_id Columns
"""
import os

print("=" * 60)
print("SQL Migration: Remove user_id Columns")
print("=" * 60)

# Read SQL file
with open("remove_user_id_columns.sql", "r") as f:
    sql = f.read()

print("\nSQL to execute in Supabase Dashboard:\n")
print(sql)
print("\n" + "=" * 60)
print("\n⚠️  The Supabase Python client doesn't support direct SQL execution.")
print("   Please run this SQL in the Supabase Dashboard:\n")
print("   1. Go to: https://supabase.com/dashboard/project/xctottgirqkkmjmutoon")
print("   2. Click 'SQL Editor' in the left sidebar")
print("   3. Click 'New Query'")
print("   4. Paste the SQL above")
print("   5. Click 'Run' (or press Ctrl+Enter)")
print("\n" + "=" * 60)
