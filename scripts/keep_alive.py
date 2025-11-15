#!/usr/bin/env python3
"""
Supabase Keep-Alive Script
Pings the app every 6 days to prevent Supabase from pausing due to inactivity
Run this as a scheduled task or cron job
"""

import requests
import time
from datetime import datetime

# Your app URLs
URLS_TO_PING = [
    "https://dept56.rndpig.com/",
    # Add more URLs if needed
]

# Supabase API endpoint (to keep database active)
SUPABASE_URL = "https://gxabjmvtzxslojsgawdh.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "your-anon-key-here"  # Replace with your anon key

def ping_website(url):
    """Ping a website to keep it active"""
    try:
        print(f"[{datetime.now()}] Pinging {url}...")
        response = requests.get(url, timeout=30)
        print(f"  ✓ Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def ping_supabase():
    """Make a simple query to keep Supabase active"""
    try:
        print(f"[{datetime.now()}] Pinging Supabase...")
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        # Simple health check query
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/houses?limit=1",
            headers=headers,
            timeout=30
        )
        print(f"  ✓ Supabase Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ✗ Supabase Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Supabase Keep-Alive Script")
    print("=" * 60)
    
    # Ping all URLs
    for url in URLS_TO_PING:
        ping_website(url)
        time.sleep(2)  # Small delay between requests
    
    # Ping Supabase directly
    ping_supabase()
    
    print("=" * 60)
    print("Keep-alive complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
