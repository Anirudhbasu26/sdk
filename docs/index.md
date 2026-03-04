# Synup SDK

Python SDK for building custom applications on top of Synup's infrastructure.

## What is this?

The Synup SDK is a **pure API client** — a thin, developer-friendly wrapper around Synup's v4 REST API. It's built for teams who want to build their own dashboards, automations, or integrations on Synup's backend.

## Quick Install

```bash
pip install synup-sdk
```

## Quick Start

```python
from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Fetch locations
result = client.fetch_all_locations(first=10)
for loc in result["locations"]:
    print(loc["name"], loc["city"])
```

## What's Included

| Component | Description |
|-----------|-------------|
| **SDK** (`pip install synup-sdk`) | Pure API client — 97 methods covering all Synup endpoints |
| **[Examples](use-cases.md)** | 10 runnable scripts for common use cases |
| **[Dashboard](dashboard.md)** | Streamlit app to explore and test endpoints interactively |
| **[MCP Server](mcp.md)** | LLM tool server for AI agent integrations |
| **[API Reference](api-reference.md)** | Auto-generated docs for every method |

## Design Philosophy

- **Thin wrapper** — returns raw API data, no opinionated models
- **Predictable naming** — `fetch_*` for GET, `create_*`/`update_*` for POST
- **Minimal required params** — sensible defaults, optional pagination
- **Auto-encoding** — numeric location IDs are base64-encoded automatically
