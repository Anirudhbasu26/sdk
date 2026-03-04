"""Quickstart: Connect to Synup and fetch your first locations.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 01_quickstart.py
"""

import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# Fetch first 5 locations
result = client.fetch_all_locations(first=5)
if result.get("success"):
    for loc in result["locations"]:
        print(f"{loc['name']} — {loc.get('city', 'N/A')}, {loc.get('stateIso', 'N/A')}")
    print(f"\nHas more pages: {result['page_info']['has_next_page']}")
else:
    print("Failed to fetch locations:", result)
