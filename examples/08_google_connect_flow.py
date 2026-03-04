"""Google connect flow: Connect Google profiles to locations.

This shows the full flow for connecting a Google Business Profile:
1. Connect a Google account (get OAuth URL)
2. List connected accounts
3. Trigger matching
4. Review and confirm matches

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 08_google_connect_flow.py
"""

import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# Step 1: Get OAuth URL for Google account connection
result = client.connect_google_account(
    success_url="https://yourapp.com/connect/success",
    error_url="https://yourapp.com/connect/error",
)
print(f"Step 1 — Redirect user to: {result.get('url', 'N/A')}")

# Step 2: List already connected accounts
accounts = client.fetch_connected_accounts(publisher="google")
print(f"\nStep 2 — Connected Google accounts:")
for acc in (accounts.get("connectedAccounts") or []):
    print(f"  {acc.get('email')} — status: {acc.get('status')}")
    acc_id = acc.get("id")

    # Step 3: See connection suggestions
    suggestions = client.fetch_connection_suggestions(acc_id, page=1, per_page=10)
    records = suggestions.get("matchedRecords") or []
    print(f"  Suggestions: {len(records)} matches found")

    # Step 4: Get listings under this account
    listings = client.fetch_connected_account_listings(acc_id, page=1, per_page=10)
    for rec in (listings.get("records") or [])[:3]:
        print(f"    - {rec.get('locationName')} ({rec.get('address', 'N/A')})")
