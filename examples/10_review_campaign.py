"""Review campaigns: Create a campaign and add customers to solicit reviews.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 10_review_campaign.py
"""

import os
from synup import SynupClient, SynupAPIError

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

LOCATION_ID = 16808  # Replace with your location ID

# Create a review campaign
customers = [
    {"name": "Alice Johnson", "email": "alice@example.com"},
    {"name": "Bob Smith", "email": "bob@example.com", "phone": "5551234567"},
]

result = client.create_review_campaign(
    location_id=LOCATION_ID,
    name="Q1 Feedback Campaign",
    location_customers=customers,
    screening=False,
)

if result.get("success"):
    campaign = result.get("reviewCampaign", {})
    campaign_id = campaign.get("id")
    print(f"Created campaign: {campaign.get('name')} (id: {campaign_id})")

    # Add more customers later
    more_customers = [
        {"name": "Charlie Davis", "email": "charlie@example.com"},
    ]
    add_result = client.add_review_campaign_customers(campaign_id, more_customers)
    print(f"Added customers: {add_result}")

    # List campaign customers
    info = client.fetch_review_campaign_customers(campaign_id)
    print(f"Campaign info: {info}")
else:
    print(f"Failed: {result.get('errors')}")

# List all campaigns for this location
campaigns = client.fetch_review_campaigns(LOCATION_ID)
print(f"\nAll campaigns ({len(campaigns)}):")
for c in campaigns:
    print(f"  {c.get('name')} — {c.get('status', 'N/A')}")
