"""
Full-stack sample — FastAPI backend + basic frontend.

Install:
    pip install synup-sdk fastapi uvicorn

Run:
    python examples/fullstack/server.py

Then open http://localhost:3000
Users provide their own API key via the X-API-Key header.
"""

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from synup import SynupClient, SynupAPIError

SYNUP_API_BASE = "https://api.synup.com/api/v4"

app = FastAPI(title="Synup Full-stack Sample")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


def get_client(x_api_key: str) -> SynupClient:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    return SynupClient(api_key=x_api_key)


# ── Locations ──────────────────────────────────────────────

@app.get("/api/locations")
def list_locations(
    first: int = Query(10, ge=1, le=100),
    after: str | None = None,
    q: str | None = None,
    x_api_key: str = Header(...),
):
    try:
        client = get_client(x_api_key)
        if q:
            return client.search_locations(query=q, first=first)
        return client.fetch_all_locations(first=first, after=after)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/locations/{location_id}")
def get_location(location_id: str, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        result = client.fetch_locations_by_ids([location_id])
        locations = result.get("locations", [])
        if not locations:
            raise HTTPException(status_code=404, detail="Location not found")
        return locations[0]
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/locations")
def create_location(input: dict = Body(...), x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.create_location(input)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.put("/api/locations")
def update_location(input: dict = Body(...), x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.update_location(input)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/locations/archive")
def archive_locations(location_ids: list[str] = Body(...), x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.archive_locations(location_ids)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Listings ───────────────────────────────────────────────

@app.get("/api/locations/{location_id}/listings")
def get_listings(location_id: str, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        premium = client.fetch_premium_listings(location_id)
        voice = client.fetch_voice_listings(location_id)
        additional = client.fetch_additional_listings(location_id)
        return {"premium": premium, "voice": voice, "additional": additional}
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Reviews ────────────────────────────────────────────────

@app.get("/api/locations/{location_id}/reviews")
def get_reviews(location_id: str, first: int = Query(10, ge=1, le=50), x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.fetch_interactions(location_id, first=first)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


class ReviewResponseBody(BaseModel):
    content: str


@app.post("/api/reviews/{interaction_id}/respond")
def respond_to_review(interaction_id: str, body: ReviewResponseBody, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.respond_to_review(interaction_id, body.content)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Analytics ──────────────────────────────────────────────

@app.get("/api/locations/{location_id}/analytics/google")
def google_analytics(
    location_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    x_api_key: str = Header(...),
):
    try:
        client = get_client(x_api_key)
        return client.fetch_google_analytics(location_id, from_date=from_date, to_date=to_date)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/locations/{location_id}/analytics/reviews")
def review_analytics(
    location_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    x_api_key: str = Header(...),
):
    try:
        client = get_client(x_api_key)
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
    x_api_key: str = Header(...),
):
    try:
        client = get_client(x_api_key)
        return client.fetch_location_grid_reports(
            location_id, page=page, page_size=page_size
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/grid-report/{report_id}")
def get_grid_report(report_id: str, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.fetch_grid_report(report_id)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Review Campaigns ──────────────────────────────────────

@app.get("/api/locations/{location_id}/campaigns")
def list_campaigns(location_id: str, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        return client.fetch_review_campaigns(location_id)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Google Connect ─────────────────────────────────────────

@app.post("/api/google/connect")
def google_connect(
    success_url: str = Body(...),
    error_url: str = Body(...),
    x_api_key: str = Header(...),
):
    try:
        client = get_client(x_api_key)
        return client.connect_google_account(
            success_url=success_url, error_url=error_url
        )
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/connected-accounts")
def connected_accounts(publisher: str | None = None, page: int = 1, x_api_key: str = Header(...)):
    try:
        client = get_client(x_api_key)
        kwargs = {"page": page, "per_page": 50}
        if publisher:
            kwargs["publisher"] = publisher
        return client.fetch_connected_accounts(**kwargs)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Proxy: forward /api/v4/* to Synup API ─────────────────

@app.api_route("/api/v4/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_synup(path: str, request: Request):
    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    target = f"{SYNUP_API_BASE}/{path}"
    if request.url.query:
        target += f"?{request.url.query}"
    fwd_headers = {
        "Authorization": f"API {api_key}",
        "Content-Type": "application/json",
    }
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(
            method=request.method,
            url=target,
            headers=fwd_headers,
            content=body if body else None,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


# ── Serve frontend ─────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("Synup Full-stack Sample → http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
