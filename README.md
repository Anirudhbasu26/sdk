---
title: Synup SDK
emoji: 🔧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Synup SDK

## Installation

```bash
pip install synup-sdk
```

For local development from the engineering-scripts:

```bash
pip install -e synup-sdk
```

## Configuration

Create a client with your API key. You can generate API keys from your Synup workspace: **Settings → Integrations → Generate**.

```python
from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")
```

Optional: use a custom base URL (default is `https://api.synup.com`):

```python
client = SynupClient(api_key="YOUR_API_KEY", base_url="https://api.synup.com")
```

## Fetch all locations

### Single page (with pagination)

Get one page of locations and use the returned cursors to paginate:

```python
result = client.fetch_all_locations(first=10)

# List of location dicts
locations = result["locations"]

# Pagination info
page_info = result["page_info"]
# page_info["has_next_page"], page_info["has_previous_page"]
# page_info["start_cursor"], page_info["end_cursor"]

# Next page
if page_info["has_next_page"]:
    next_result = client.fetch_all_locations(first=10, after=page_info["end_cursor"])
```

### All locations (auto-paginate)

Fetch every location in one call; the SDK will follow cursors until all are retrieved:

```python
all_locations = client.fetch_all_locations(fetch_all=True)
# all_locations is a list of location dicts
```

Optional: set page size when using `fetch_all=True` (default is 100):

```python
all_locations = client.fetch_all_locations(fetch_all=True, page_size=50)
```

## Search and filter locations

You can fetch locations by **location ID**, **store code**, **name** (search), **folder**, or **tags**.

### By location IDs

You can pass **numeric IDs** (e.g. `16808`) or **base64-encoded IDs** (e.g. `"TG9jYXRpb246MTY4MDg="`). Numeric IDs are encoded as `Location:{id}` under the hood.

```python
# Using numeric IDs (recommended)
locations = client.fetch_locations_by_ids([16808, 16749])

# Using base64-encoded IDs (also supported)
locations = client.fetch_locations_by_ids(["TG9jYXRpb246MTY4MDg=", "TG9jYXRpb246MTY3NDk="])
```

### By store codes

```python
locations = client.fetch_locations_by_store_codes(["STORE01", "STORE02"])
```

### By name (search)

Searches location name, street address, and store_id by default. Optional `fields` limits search to specific fields (e.g. `["store_id"]`, `["name"]`).

```python
# One page
result = client.search_locations("cafe", first=10)
locations = result["locations"]
page_info = result["page_info"]

# All matches (auto-paginate)
all_matches = client.search_locations("cafe", fetch_all=True)
```

### By folder

Fetch all locations under a folder (and its subfolders). Use either folder ID or folder name.

```python
# By folder name
locations = client.fetch_locations_by_folder(folder_name="franchise")

# By folder ID (UUID)
locations = client.fetch_locations_by_folder(folder_id="67049f29-3bc6-4e82-875b-02159b4b1fea")
```

### By tags

Fetch locations that have any of the given tags.

```python
# One page
result = client.fetch_locations_by_tags(["recent", "vip"], first=10)

# All (auto-paginate)
locations = client.fetch_locations_by_tags(["recent"], fetch_all=True)

# Only active
locations = client.fetch_locations_by_tags(["recent"], archived=False, fetch_all=True)
```

## Listings for a location

All listing methods accept a **location ID** as numeric (e.g. `16808`) or base64-encoded; numeric IDs are encoded automatically.

### Premium listings

```python
listings = client.fetch_premium_listings(16808)
# List of dicts: id, site, syncStatus, displayStatus, listingUrl, etc.
```

### Voice assistant listings (Google, Alexa, Siri, etc.)

```python
listings = client.fetch_voice_listings(16808)
# name, voiceIdentifier, syncStatus, etc.
```

## Interactions (reviews)

Fetch reviews and social interactions for a location (last 30 days by default). Pagination is cursor-based.

```python
# One page
result = client.fetch_interactions(16808, first=10)
interactions = result["interactions"]
page_info = result["page_info"]
total_count = result["total_count"]

# All interactions (auto-paginate)
all_reviews = client.fetch_interactions(16808, fetch_all=True)

# With filters (date range, site, category, rating)
result = client.fetch_interactions(
    16808,
    first=20,
    start_date="2024-01-01",
    end_date="2024-01-31",
    site_urls=["maps.google.com", "yelp.com"],
    category="Review",
    rating_filters=[4, 5],
)
```

## Rankings (keywords)

```python
# Keywords added to a location
keywords = client.fetch_keywords(16808)

# Keyword ranking performance (optional date range)
performance = client.fetch_keywords_performance(16808, from_date="2024-01-01", to_date="2024-01-31")
```

## Review campaigns

```python
campaigns = client.fetch_review_campaigns(16808)
# Optional date range
campaigns = client.fetch_review_campaigns(16808, start_date="2024-01-01", end_date="2024-12-31")
```

## Profile analytics

Bing, Google (GMB), and Facebook profile analytics for a location. Optional date range (`YYYY-MM-DD`).

```python
bing = client.fetch_bing_analytics(16808, from_date="2024-01-01", to_date="2024-01-31")
google = client.fetch_google_analytics(16808, from_date="2024-01-01", to_date="2024-01-31")
facebook = client.fetch_facebook_analytics(16808, from_date="2024-01-01", to_date="2024-01-31")
```

## Photos and connection info

```python
photos = client.fetch_location_photos(16808)
connection_info = client.fetch_connection_info(16808)  # Google/Facebook OAuth connection info
```

## Review settings and analytics

```python
# Interaction/review source settings for a location (sites and URLs)
settings = client.fetch_review_settings(16808)

# Review analytics (overview, timeline, per-site stats). Optional start_date, end_date.
overview = client.fetch_review_analytics_overview(16808, start_date="2024-01-01", end_date="2024-01-31")
timeline = client.fetch_review_analytics_timeline(16808, start_date="2024-01-01", end_date="2024-01-31")
sites_stats = client.fetch_review_analytics_sites_stats(16808, start_date="2024-01-01", end_date="2024-01-31")

# Account-level: eligible review sites for the plan
site_config = client.fetch_review_site_config()
```

## Plan sites and countries

Account-level: supported directories and countries/states (ISO codes).

```python
plan_sites = client.fetch_plan_sites()
countries = client.fetch_countries()
```

## Create location (POST)

Create a new location in your account. Pass an `input` dict with API field names (camelCase). Required fields typically include `name`, `storeId`, `street`, `city`, `stateIso`, `postalCode`, `countryIso`, `phone`. See the [API attributes](https://docs.synup.com/v4/locations) for the full list.

```python
result = client.create_location({
    "name": "Acme Inc",
    "storeId": "ACME01",
    "street": "123 Jump Street",
    "city": "New York",
    "stateIso": "NY",
    "postalCode": "33133",
    "countryIso": "US",
    "phone": "6443859313",
    "description": "Optional description...",
    "ownerEmail": "owner@example.com",
})
# result["location"] (created location), result["success"], result["errors"]
```

### Update, archive, activate locations (POST)

```python
client.update_location({"id": "TG9jYXRpb246MTM2OTc=", "phone": "9910991111"})
client.archive_locations(["TG9jYXRpb246MTM5OTg="])
client.activate_locations(["TG9jYXRpb246MTM5OTg="])
client.cancel_archive_locations(["TG9jYXRpb246ODQ3NzM="], selection_type="SELECTED_ITEMS", changed_by="admin")
```

### Location photos (POST)

```python
client.add_location_photos(16808, [{"photo": "https://example.com/image.jpg", "type": "ADDITIONAL"}])
client.remove_location_photos(16808, ["TG9jYXRpb25QaG90bzoxMjI2MA=="])
client.star_location_photos(16808, ["TWVkaWFGaWxlOjg4MjY5Nw=="], starred=True)
```

### Folders and tags (organizing locations) (POST)

```python
client.create_folder("franchise", parent_folder_name="all_franchise")
client.rename_folder("Acme", "Acme New")
client.add_locations_to_folder("Acme", ["TG9jYXRpb246MTY4NjE=", "TG9jYXRpb246MTY4NjA="])
client.remove_locations_from_folder(["TG9jYXRpb246MTY4NDY="])
client.delete_folder("Acme New")

client.add_location_tag(16808, "New")
client.remove_location_tag(16808, "Old")
```

### Listings: mark duplicate (POST)

```python
client.mark_listings_as_duplicate(16808, ["TGlzdGluZ0l0ZW06MzMzMjkzOA=="])
client.mark_listings_as_not_duplicate(16808, ["TGlzdGluZ0l0ZW06MzMzMjkzOA=="])
```

### Reviews: respond and settings (POST)

```python
client.respond_to_review(interaction_id="2090753a-ece6-4837-8336-8494ad308523", response_content="Thank you!")
client.edit_review_response(review_id="...", response_id="...", response_content="Updated response")
client.archive_review_response(response_id="...")
client.edit_review_settings(16808, [{"name": "trulia.com", "url": "https://test.com"}])
```

### User: add user and folder (POST)

```python
client.add_user_and_folder({"roleId": "...", "firstName": "Jane", "email": "j@example.com", "name": "folder_name", "locationIds": ["..."]})
```

### Rankings analytics (POST)

```python
timeline = client.fetch_ranking_analytics_timeline(["TG9jYXRpb246NzkwODQ="], "2023-03-11", "2023-03-15", ["Google"])
histogram = client.fetch_ranking_sitewise_histogram(["TG9jYXRpb246NzkwODQ="], "2023-03-11", "2023-03-15", ["Google"])
```

## Create review campaign (POST)

Create a review campaign for a location and optionally add customers, screening, and templates.

```python
result = client.create_review_campaign(
    location_id=16808,
    name="Holiday Feedback",
    location_customers=[
        {"name": "John", "email": "john@example.com", "phone": "1234567890"},
    ],
    screening=False,
)
# result["reviewCampaign"], result["success"], result["errors"]

# Add more customers to an existing campaign
client.add_review_campaign_customers(
    review_campaign_id="794be682-a321-4eac-953c-37dcac0a55a2",
    location_customers=[{"name": "Jane", "email": "jane@example.com"}],
)
```

## Keywords: add and archive (POST)

```python
keywords = client.add_keywords(16808, ["plumber", "plumbing near me"])
# Returns list of created keywords (id, name)

client.archive_keyword("S2V5d29yZDo3NjQzMTE=")
```

## User management (POST)

Create and update users, assign locations and folders.

```python
# Create user
result = client.create_user(
    email="user@example.com",
    role_id="Q3VzdG9tUm9sZToyMDgzMQ==",
    first_name="Jane",
    last_name="Doe",
    direct_customer=True,
)

# Update user
client.update_user(user_id="VXNlcjo5OTY0", first_name="Jane Updated", role_id="...")

# Add/remove locations and folders
client.add_user_locations("VXNlcjoxMDAyOA==", ["TG9jYXRpb246NDA5ODE="])
client.remove_user_locations("VXNlcjoxMDAyOA==", ["TG9jYXRpb246NTE1MzA="])
client.add_user_folders("VXNlcjoxMDAyOA==", ["folder-uuid-1"])
client.remove_user_folders("VXNlcjoxMDAyOA==", ["folder-uuid-1"])
```

## Automations (POST)

Temporarily close a location with a reopening date (Google and Facebook locations).

```python
result = client.create_temporary_close_automation(
    name="Holiday closure",
    start_date="2025-02-25",
    start_time="10:00:00",
    end_date="2025-02-28",
    location_id=85006,
)
# result["flow"]["id"], result["success"]
```

## OAuth connect / disconnect (POST)

Get a URL to connect a Google or Facebook profile to a location (valid 24 hours), or disconnect.

```python
# Connect (get redirect URL)
url_result = client.get_oauth_connect_url(
    location_id=16808,
    site="GOOGLE",
    success_url="https://yoursite.com/success",
    error_url="https://yoursite.com/error",
)
# Redirect user to url_result["url"]

# Disconnect
client.oauth_disconnect(16808, "FACEBOOK")
```

## Connected accounts (POST)

Bulk connect/disconnect Google or Facebook accounts (multiple locations). URLs are valid 24 hours.

```python
# Get connect URL
google = client.connect_google_account("https://ok.com", "https://err.com")
facebook = client.connect_facebook_account("https://ok.com", "https://err.com")
# Redirect user to google["url"] or facebook["url"]

# Disconnect by connected account ID
client.disconnect_google_account(connected_account_id="...")
client.disconnect_facebook_account(connected_account_id="...")
```

### Connected accounts: matches, listings, connect/disconnect (POST)

Trigger matching of GMB/Facebook profiles with Synup locations; fetch and connect listings.

```python
# Trigger matching for connected accounts
client.trigger_connected_account_matches(["6eb312f7-df32-4d76-ad8a-26bcfeab601e"])

# Fetch listings a connected account has access to (optional filter, pagination)
listings = client.fetch_connected_account_listings(
    "3db66afa-151d-4212-a8b7-949f9fe9aaf9",
    location_info="123 William St",
    page=1,
    per_page=100,
)
# listings["pageInfo"], listings["records"] (each has id, locationName, address, etc.)

# Confirm matches from connection suggestions (match_record_ids are base64-encoded)
client.confirm_connected_account_matches(["R21iTG9jYXRpb25NYXRjaGVkRGF0YTplNGZh..."])

# Connect a location to a listing (use id from fetch_connected_account_listings as connected_account_listing_id)
client.connect_listing(location_id=73933, connected_account_listing_id="R21iQnVsa0...", connected_account_id="3db66afa-...")

# Disconnect a location from its Google or Facebook listing
client.disconnect_listing(16808, "GOOGLE")

# Create a GMB listing for an existing location (async)
client.create_gmb_listing(location_id=14055, connected_account_id="bc818dc7-...", folder_id="accounts/1154433325552997863009")
```

## Grid rank (Local Rank Grid)

Create and fetch Local Rank Grid reports (ranking positions across a geographic grid).

```python
# Create report (max 25 keywords; grid_size 3, 5, or 7; distance_unit "mi" or "km")
result = client.create_grid_report(
    location_id=16808,
    keywords=["italian restaurant"],
    business_name="Chianti, Koramangala",
    business_street="No 12, 5th Block",
    business_city="Bengaluru",
    business_state="Karnataka",
    business_country="India",
    latitude=12.935216,
    longitude=77.619961,
    distance=20,
    distance_unit="km",
    grid_size=3,
)
# result["data"]["reportIds"]

# Fetch report by ID
report = client.fetch_grid_report("report-uuid")

# List all grid reports for a location
data = client.fetch_location_grid_reports(16808, page_size=20, page=1)
# data["reports"], data["total"]
```

## Errors

On non-2xx API responses, the client raises `SynupAPIError`:

```python
from synup import SynupClient, SynupAPIError

client = SynupClient(api_key="...")
try:
    client.fetch_all_locations()
except SynupAPIError as e:
    print(e.status_code, e.response_body)
```

## SDK Design Philosophy & Development Guidelines

### What This SDK Is

This SDK is a developer toolkit that lets you build applications on top of Synup’s backend. Use it from scripts, apps, or automated flows — the SDK handles Synup API calls with minimal friction.

### Core Principle: Simple, Predictable Design

Every API, method, and response is designed to be easy to use from any kind of client:

- **Simple, flat method signatures** — no deeply nested configs or complex builder patterns
- **Predictable, consistent naming** — verb-first names (`fetch_locations`, `create_campaign`, `add_keywords`) so behavior is easy to infer
- **Self-describing responses** — structured objects with clear field names; paginated and mutation responses include a `success` field where appropriate so callers can branch without extra context
- **Minimal required parameters** — sensible defaults; only what’s truly necessary is required
- **Forgiving inputs** — e.g. location IDs as numeric or base64-encoded

### How Users Build With This SDK

1. The user gets a message or intent from their end-user (or from their own application logic).
2. They decide which SDK methods to call.
3. The call is simple enough to construct correctly on the first try.
4. The SDK returns a clear, structured response that’s easy to reason about and return to the user.

The SDK sits *between* your application and Synup’s backend. Our job is to make that integration invisible and frictionless.

### Code Standards

- **Method design:** Prefer `do_thing(input, options?)`. Return typed, flat response objects. Every method is usable in one line with minimal cognitive load. Errors are descriptive and actionable.
- **Response structure:** Structured objects with clear field names; `success` or `status` where it helps callers branch; avoid raw primitives when a small object is clearer.
- **Documentation:** Every public method has a one-line description, plain-English parameter docs, and a short usage example in its docstring.
- **Naming:** Verb-first method names; no internal jargon; names should be guessable from context.

### What to Avoid

- Do not design for internal backend complexity — abstract it away.
- Do not require users to understand our infrastructure.
- Keep auth/setup to 2–3 lines max.
- Do not return errors that require internal docs to understand.
- Use optional config for edge-case parameters.

### The Bar for Every Feature

Before finalizing any method or feature, ask:

> “Could a developer (or automated client), given just the method signature and a one-line description, call this correctly and handle the response — without any additional context?”

If the answer is no, simplify until it is.

## Version

Current version: 0.3.0
