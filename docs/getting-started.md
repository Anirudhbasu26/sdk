# Getting Started

## Installation

```bash
pip install synup-sdk
```

## Authentication

Get your API key from **Settings > Integrations > Generate** in your Synup workspace.

```python
from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")
```

Or use an environment variable:

```python
import os
from synup import SynupClient

client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])
```

## Your First API Call

```python
# Fetch the first 5 locations
result = client.fetch_all_locations(first=5)

if result.get("success"):
    for loc in result["locations"]:
        print(f"{loc['name']} — {loc['city']}, {loc['stateIso']}")

    # Check if there are more pages
    if result["page_info"]["has_next_page"]:
        cursor = result["page_info"]["end_cursor"]
        next_page = client.fetch_all_locations(first=5, after=cursor)
```

## Fetch All (Auto-Pagination)

For bulk operations, use `fetch_all=True` to automatically follow all pages:

```python
all_locations = client.fetch_all_locations(fetch_all=True)
print(f"Total: {len(all_locations)} locations")
```

## Error Handling

All API errors raise `SynupAPIError` with the HTTP status code and response body:

```python
from synup import SynupClient, SynupAPIError

try:
    client.fetch_all_locations()
except SynupAPIError as e:
    if e.status_code == 401:
        print("Invalid API key")
    else:
        print(f"Error {e.status_code}: {e.response_body}")
```

## Location IDs

Most methods accept location IDs as either:

- **Numeric**: `16808`
- **Base64-encoded**: `"TG9jYXRpb246MTY4MDg="`

The SDK auto-encodes numeric IDs, so both work:

```python
# These are equivalent
client.fetch_premium_listings(16808)
client.fetch_premium_listings("TG9jYXRpb246MTY4MDg=")
```

## Next Steps

- Browse [Use Cases](use-cases.md) for runnable examples
- Open the [Dashboard](dashboard.md) to test endpoints interactively
- See the full [API Reference](api-reference.md)
