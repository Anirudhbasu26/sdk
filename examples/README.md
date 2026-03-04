# Synup SDK Examples

Runnable scripts demonstrating common use cases. Set your API key before running:

```bash
export SYNUP_API_KEY="your_api_key"
```

| # | Script | Description |
|---|--------|-------------|
| 01 | `01_quickstart.py` | Connect and fetch your first locations |
| 02 | `02_bulk_export_locations.py` | Export all locations to CSV |
| 03 | `03_review_monitoring.py` | Monitor reviews and flag negative ones |
| 04 | `04_bulk_respond_reviews.py` | Auto-reply to unanswered reviews |
| 05 | `05_analytics_report.py` | Pull Google and review analytics |
| 06 | `06_listings_audit.py` | Audit listing sync status and find duplicates |
| 07 | `07_user_management.py` | Create users and manage access |
| 08 | `08_google_connect_flow.py` | Connect Google Business Profiles |
| 09 | `09_grid_rank_report.py` | Create Local Rank Grid reports |
| 10 | `10_review_campaign.py` | Run review solicitation campaigns |
| 11 | `11_fastapi_backend.py` | Wire the SDK into a FastAPI backend |

## Full-stack Sample

The `fullstack/` directory contains a complete working app — a **Locations & Listings Dashboard** with a FastAPI backend and HTML frontend.

```bash
pip install synup-sdk fastapi uvicorn
SYNUP_API_KEY='your_key' python examples/fullstack/server.py
# Open http://localhost:3000
```

Features:
- Browse locations in a card grid with search
- Click a location to see its listings (premium, voice, additional) and reviews
- Slide-out detail panel with tabbed view
