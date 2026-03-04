"""
FastAPI Backend — wire the Synup SDK into a REST API your frontend can call.

Install:
    pip install synup-sdk fastapi uvicorn

Run:
    SYNUP_API_KEY='your_key' uvicorn examples.11_fastapi_backend:app --reload --port 8000

Your frontend can then call:
    GET  /locations
    GET  /locations/:id
    GET  /locations/:id/listings
    GET  /locations/:id/reviews
    POST /locations/:id/reviews/:interaction_id/respond
"""

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from synup import SynupClient, SynupAPIError

# --- Init ---
app = FastAPI(title="Synup-powered API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])


# --- Routes ---

@app.get("/locations")
def list_locations(
    first: int = Query(20, ge=1, le=100),
    after: str | None = None,
    q: str | None = None,
):
    """Get locations with optional search and pagination."""
    try:
        if q:
            return client.search_locations(query=q, first=first)
        return client.fetch_all_locations(first=first, after=after)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/locations/{location_id}")
def get_location(location_id: str):
    """Get a single location by ID."""
    try:
        result = client.fetch_locations_by_ids([location_id])
        locations = result.get("locations", [])
        if not locations:
            raise HTTPException(status_code=404, detail="Location not found")
        return locations[0]
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/locations/{location_id}/listings")
def get_listings(location_id: str):
    """Get all listing types for a location."""
    try:
        return {
            "premium": client.fetch_premium_listings(location_id),
            "voice": client.fetch_voice_listings(location_id),
            "additional": client.fetch_additional_listings(location_id),
        }
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/locations/{location_id}/reviews")
def get_reviews(
    location_id: str,
    first: int = Query(20, ge=1, le=100),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get reviews for a location."""
    try:
        return client.fetch_interactions(
            location_id, first=first, start_date=start_date, end_date=end_date
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


class ReviewResponse(BaseModel):
    content: str


@app.post("/locations/{location_id}/reviews/{interaction_id}/respond")
def respond_to_review(location_id: str, interaction_id: str, body: ReviewResponse):
    """Respond to a review."""
    try:
        return client.respond_to_review(interaction_id, body.content)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
