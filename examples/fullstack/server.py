"""
Full-stack sample — FastAPI backend + basic frontend.

Install:
    pip install synup-sdk fastapi uvicorn

Run:
    SYNUP_API_KEY='your_key' python examples/fullstack/server.py

Then open http://localhost:3000
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from synup import SynupClient, SynupAPIError

app = FastAPI(title="Synup Full-stack Sample")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])
STATIC_DIR = Path(__file__).parent / "static"


# ── Locations ──────────────────────────────────────────────

@app.get("/api/locations")
def list_locations(
    first: int = Query(10, ge=1, le=100),
    after: str | None = None,
    q: str | None = None,
):
    try:
        if q:
            return client.search_locations(query=q, first=first)
        return client.fetch_all_locations(first=first, after=after)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/locations/{location_id}")
def get_location(location_id: str):
    try:
        result = client.fetch_locations_by_ids([location_id])
        locations = result.get("locations", [])
        if not locations:
            raise HTTPException(status_code=404, detail="Location not found")
        return locations[0]
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/locations")
def create_location(input: dict = Body(...)):
    try:
        return client.create_location(input)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.put("/api/locations")
def update_location(input: dict = Body(...)):
    try:
        return client.update_location(input)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/locations/archive")
def archive_locations(location_ids: list[str] = Body(...)):
    try:
        return client.archive_locations(location_ids)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Listings ───────────────────────────────────────────────

@app.get("/api/locations/{location_id}/listings")
def get_listings(location_id: str):
    try:
        premium = client.fetch_premium_listings(location_id)
        voice = client.fetch_voice_listings(location_id)
        additional = client.fetch_additional_listings(location_id)
        return {"premium": premium, "voice": voice, "additional": additional}
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Reviews ────────────────────────────────────────────────

@app.get("/api/locations/{location_id}/reviews")
def get_reviews(location_id: str, first: int = Query(10, ge=1, le=50)):
    try:
        return client.fetch_interactions(location_id, first=first)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


class ReviewResponseBody(BaseModel):
    content: str


@app.post("/api/reviews/{interaction_id}/respond")
def respond_to_review(interaction_id: str, body: ReviewResponseBody):
    try:
        return client.respond_to_review(interaction_id, body.content)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Analytics ──────────────────────────────────────────────

@app.get("/api/locations/{location_id}/analytics/google")
def google_analytics(
    location_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
):
    try:
        return client.fetch_google_analytics(location_id, from_date=from_date, to_date=to_date)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/locations/{location_id}/analytics/reviews")
def review_analytics(
    location_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
):
    try:
        return client.fetch_review_analytics_overview(
            location_id, start_date=start_date, end_date=end_date
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Grid Rank ──────────────────────────────────────────────

@app.get("/api/locations/{location_id}/grid-reports")
def list_grid_reports(
    location_id: str,
    page: int = Query(1),
    page_size: int = Query(10),
):
    try:
        return client.fetch_location_grid_reports(
            location_id, page=page, page_size=page_size
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/grid-report/{report_id}")
def get_grid_report(report_id: str):
    try:
        return client.fetch_grid_report(report_id)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Review Campaigns ──────────────────────────────────────

@app.get("/api/locations/{location_id}/campaigns")
def list_campaigns(location_id: str):
    try:
        return client.fetch_review_campaigns(location_id)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Google Connect ─────────────────────────────────────────

@app.post("/api/google/connect")
def google_connect(
    success_url: str = Body(...),
    error_url: str = Body(...),
):
    try:
        return client.connect_google_account(
            success_url=success_url, error_url=error_url
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/connected-accounts")
def connected_accounts(publisher: str | None = None, page: int = 1):
    try:
        kwargs = {"page": page, "per_page": 50}
        if publisher:
            kwargs["publisher"] = publisher
        return client.fetch_connected_accounts(**kwargs)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Serve frontend ─────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("Synup Full-stack Sample → http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
