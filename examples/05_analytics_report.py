"""Analytics report: Pull Google and review analytics for your locations.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 05_analytics_report.py
"""

import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

FROM_DATE = "2024-01-01"
TO_DATE = "2024-12-31"

# Get all locations
locations = client.fetch_all_locations(fetch_all=True)
print(f"Generating report for {len(locations)} locations ({FROM_DATE} to {TO_DATE})\n")

for loc in locations[:10]:  # Limit to first 10 for demo
    loc_id = loc["id"]
    name = loc["name"]
    print(f"--- {name} ---")

    # Google profile analytics
    google = client.fetch_google_analytics(loc_id, from_date=FROM_DATE, to_date=TO_DATE)
    if google:
        print(f"  Google: {google}")

    # Review analytics overview
    review_stats = client.fetch_review_analytics_overview(loc_id, start_date=FROM_DATE, end_date=TO_DATE)
    if review_stats:
        print(f"  Reviews: {review_stats}")

    # Per-site review breakdown
    sites = client.fetch_review_analytics_sites_stats(loc_id, start_date=FROM_DATE, end_date=TO_DATE)
    if sites:
        print(f"  Sites: {sites}")

    print()
