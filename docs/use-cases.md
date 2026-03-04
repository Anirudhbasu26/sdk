# Use Cases

Runnable example scripts in the `examples/` folder. Set your API key first:

```bash
export SYNUP_API_KEY="your_api_key"
```

## 1. Quick Start — Fetch Locations

```python
from synup import SynupClient
import os

client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])
result = client.fetch_all_locations(first=5)
for loc in result["locations"]:
    print(f"{loc['name']} — {loc['city']}")
```

Run: `python examples/01_quickstart.py`

## 2. Bulk Export to CSV

Export all locations to a CSV file with auto-pagination.

```python
import csv
locations = client.fetch_all_locations(fetch_all=True)
with open("locations.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "city", "phone"], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(locations)
```

Run: `python examples/02_bulk_export_locations.py`

## 3. Review Monitoring

Scan locations for negative reviews that need attention.

```python
reviews = client.fetch_interactions(location_id, first=20)
for review in reviews["interactions"]:
    if review.get("rating", 5) <= 2:
        print(f"NEEDS ATTENTION: {review['authorName']} ({review['rating']} stars)")
```

Run: `python examples/03_review_monitoring.py`

## 4. Bulk Respond to Reviews

Auto-reply to unanswered reviews using templates (or LLM-generated responses).

```python
client.respond_to_review(
    interaction_id="review-uuid",
    response_content="Thank you for your feedback!"
)
```

Run: `python examples/04_bulk_respond_reviews.py`

## 5. Analytics Report

Pull Google, Bing, and review analytics across all locations.

```python
google = client.fetch_google_analytics(location_id, from_date="2024-01-01", to_date="2024-12-31")
review_stats = client.fetch_review_analytics_overview(location_id, start_date="2024-01-01", end_date="2024-12-31")
```

Run: `python examples/05_analytics_report.py`

## 6. Listings Audit

Audit listing sync status across locations — flag unsynced listings.

```python
# Premium listings (Google, Yelp, Facebook, etc.)
premium = client.fetch_premium_listings(location_id)
for l in premium:
    if l.get("syncStatus") != "SYNCED":
        print(f"Not synced: {l['site']} — {l['syncStatus']}")

# Voice assistant listings
voice = client.fetch_voice_listings(location_id)

# AI listing suggestions
ai = client.fetch_ai_listings(location_id)
```

Run: `python examples/06_listings_audit.py`

## 7. User Management

Create users, assign roles, and control location access.

```python
result = client.create_user("user@example.com", role_id, "Jane", last_name="Doe")
client.add_user_locations(user_id, [loc_id_1, loc_id_2])
```

Run: `python examples/07_user_management.py`

## 8. Google Connect Flow

Full OAuth flow for connecting Google Business Profiles.

```python
# Get OAuth URL
result = client.connect_google_account("https://app.com/success", "https://app.com/error")
# After connection, list accounts and trigger matching
accounts = client.fetch_connected_accounts(publisher="google")
```

Run: `python examples/08_google_connect_flow.py`

## 9. Grid Rank Reports

Create Local Rank Grid reports to see your Google rankings across a geographic area.

```python
result = client.create_grid_report(
    location_id=16808,
    keywords=["pizza near me"],
    business_name="Joe's Pizza",
    business_street="123 Main St", business_city="NYC",
    business_state="NY", business_country="US",
    latitude=40.7128, longitude=-74.006,
    distance=10, distance_unit="mi", grid_size=3,
)
```

Run: `python examples/09_grid_rank_report.py`

## 10. Review Campaigns

Create campaigns to solicit reviews from customers.

```python
result = client.create_review_campaign(
    location_id=16808,
    name="Q1 Feedback",
    location_customers=[{"name": "Alice", "email": "alice@example.com"}],
)
```

Run: `python examples/10_review_campaign.py`
