"""Review monitoring: Fetch recent reviews and flag negative ones.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 03_review_monitoring.py
"""

import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# Get first 5 locations
result = client.fetch_all_locations(first=5)
locations = result["locations"]

for loc in locations:
    loc_id = loc["id"]
    print(f"\n--- {loc['name']} ---")

    # Fetch recent reviews (last 30 days by default)
    reviews = client.fetch_interactions(loc_id, first=10)
    if not reviews.get("interactions"):
        print("  No recent reviews")
        continue

    for review in reviews["interactions"]:
        rating = review.get("rating", "N/A")
        author = review.get("authorName", "Anonymous")
        site = review.get("siteName", "Unknown")
        content = (review.get("content") or "")[:80]
        responded = bool(review.get("responses"))

        flag = " ** NEEDS ATTENTION **" if isinstance(rating, (int, float)) and rating <= 2 else ""
        status = "Responded" if responded else "No reply"
        print(f"  [{rating}] {author} on {site} ({status}){flag}")
        if content:
            print(f"       {content}...")
