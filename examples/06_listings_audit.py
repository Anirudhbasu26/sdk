"""Listings audit: Check listing sync status across locations.

Pulls premium and voice listings for each location and prints
a summary of sync status and AI suggestions.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 06_listings_audit.py
"""

import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# Get locations (first 10 for demo, use fetch_all=True for all)
result = client.fetch_all_locations(first=10)
locations = result["locations"]
print(f"Auditing listings for {len(locations)} locations\n")

for loc in locations:
    loc_id = loc["id"]
    name = loc["name"]
    print(f"--- {name} ---")

    # Premium listings (Google, Yelp, Facebook, etc.)
    premium = client.fetch_premium_listings(loc_id)
    synced = [l for l in premium if l.get("syncStatus") == "SYNCED"]
    not_synced = [l for l in premium if l.get("syncStatus") != "SYNCED"]
    print(f"  Premium: {len(synced)} synced, {len(not_synced)} not synced")
    for l in not_synced:
        print(f"    [{l.get('syncStatus', 'UNKNOWN')}] {l.get('site', 'N/A')}")

    # Voice assistant listings
    voice = client.fetch_voice_listings(loc_id)
    print(f"  Voice: {len(voice)} listings")

    # AI listing suggestions
    ai = client.fetch_ai_listings(loc_id)
    if ai:
        print(f"  AI suggestions available: {bool(ai)}")

    print()
