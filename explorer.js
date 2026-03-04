/* ============================================================
   Synup SDK Explorer — interactive endpoint browser
   ============================================================ */

// --- Example Code Snippets ---
const EXAMPLES = {
  quickstart: {
    title: "Quick Start",
    filename: "01_quickstart.py",
    code: `from synup import SynupClient
import os

client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])

# Fetch first 5 locations
result = client.fetch_all_locations(first=5)

if result.get("success"):
    for loc in result["locations"]:
        print(f"{loc['name']} — {loc.get('city')}, {loc.get('stateIso')}")
    print(f"Has more pages: {result['page_info']['has_next_page']}")`
  },
  export: {
    title: "Bulk CSV Export",
    filename: "02_bulk_export_locations.py",
    code: `import csv
from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Fetch ALL locations (auto-paginates)
locations = client.fetch_all_locations(fetch_all=True)
print(f"Fetched {len(locations)} locations")

# Write to CSV
fields = ["id", "name", "storeId", "street", "city", "stateIso", "postalCode", "phone"]
with open("locations_export.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(locations)`
  },
  reviews: {
    title: "Review Monitoring",
    filename: "03_review_monitoring.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Get locations and check reviews
result = client.fetch_all_locations(first=5)
for loc in result["locations"]:
    reviews = client.fetch_interactions(loc["id"], first=10)

    for review in reviews.get("interactions", []):
        rating = review.get("rating", "N/A")
        author = review.get("authorName", "Anonymous")
        responded = bool(review.get("responses"))

        flag = " ** NEEDS ATTENTION **" if rating <= 2 else ""
        status = "Responded" if responded else "No reply"
        print(f"[{rating}] {author} ({status}){flag}")`
  },
  respond: {
    title: "Bulk Respond to Reviews",
    filename: "04_bulk_respond_reviews.py",
    code: `from synup import SynupClient, SynupAPIError

client = SynupClient(api_key="YOUR_API_KEY")

TEMPLATES = {
    5: "Thank you so much for the wonderful review!",
    4: "Thank you for your kind review!",
    3: "Thank you for your feedback. We'd love to hear more.",
    2: "We're sorry to hear about your experience.",
    1: "We sincerely apologize. Please reach out to us.",
}

reviews = client.fetch_interactions(16808, first=50)
unanswered = [r for r in reviews.get("interactions", [])
              if not r.get("responses") and r.get("interactionId")]

for review in unanswered:
    rating = review.get("rating", 3)
    template = TEMPLATES.get(rating, TEMPLATES[3])
    client.respond_to_review(review["interactionId"], template)
    print(f"Replied to {review.get('authorName')} ({rating} stars)")`
  },
  analytics: {
    title: "Analytics Report",
    filename: "05_analytics_report.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

locations = client.fetch_all_locations(fetch_all=True)

for loc in locations[:10]:
    loc_id = loc["id"]
    print(f"--- {loc['name']} ---")

    # Google profile analytics
    google = client.fetch_google_analytics(
        loc_id, from_date="2024-01-01", to_date="2024-12-31"
    )

    # Review analytics overview
    review_stats = client.fetch_review_analytics_overview(
        loc_id, start_date="2024-01-01", end_date="2024-12-31"
    )

    # Per-site breakdown
    sites = client.fetch_review_analytics_sites_stats(
        loc_id, start_date="2024-01-01", end_date="2024-12-31"
    )`
  },
  listings: {
    title: "Listings Audit",
    filename: "06_listings_audit.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

result = client.fetch_all_locations(first=10)
for loc in result["locations"]:
    loc_id = loc["id"]
    print(f"--- {loc['name']} ---")

    # Premium listings (Google, Yelp, Facebook, etc.)
    premium = client.fetch_premium_listings(loc_id)
    synced = [l for l in premium if l.get("syncStatus") == "SYNCED"]
    not_synced = [l for l in premium if l.get("syncStatus") != "SYNCED"]
    print(f"  Premium: {len(synced)} synced, {len(not_synced)} not synced")

    # Voice assistant listings
    voice = client.fetch_voice_listings(loc_id)
    print(f"  Voice: {len(voice)} listings")

    # AI listing suggestions
    ai = client.fetch_ai_listings(loc_id)
    if ai:
        print(f"  AI suggestions available")`
  },
  users: {
    title: "User Management",
    filename: "07_user_management.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# List current users
users = client.fetch_users()
for user in users:
    print(f"{user.get('email')} — {user.get('firstName')}")

# List available roles
roles = client.fetch_roles()
for role in roles:
    print(f"{role.get('name')} (id: {role.get('id')})")

# Create a new user
result = client.create_user(
    email="newuser@example.com",
    role_id=roles[0]["id"],
    first_name="Jane",
    last_name="Doe",
)

# Assign locations to user
if result.get("success"):
    user_id = result["user"]["id"]
    locations = client.fetch_all_locations(first=5)
    loc_ids = [loc["id"] for loc in locations["locations"]]
    client.add_user_locations(user_id, loc_ids)`
  },
  google: {
    title: "Google Connect Flow",
    filename: "08_google_connect_flow.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Step 1: Get OAuth URL
result = client.connect_google_account(
    success_url="https://yourapp.com/connect/success",
    error_url="https://yourapp.com/connect/error",
)
print(f"Redirect user to: {result.get('url')}")

# Step 2: List connected accounts
accounts = client.fetch_connected_accounts(publisher="google")
for acc in accounts.get("connectedAccounts", []):
    print(f"{acc.get('email')} — status: {acc.get('status')}")

    # Step 3: See connection suggestions
    suggestions = client.fetch_connection_suggestions(
        acc["id"], page=1, per_page=10
    )

    # Step 4: Get listings under this account
    listings = client.fetch_connected_account_listings(
        acc["id"], page=1, per_page=10
    )`
  },
  gridrank: {
    title: "Grid Rank Report",
    filename: "09_grid_rank_report.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Create a grid rank report
result = client.create_grid_report(
    location_id=16808,
    keywords=["italian restaurant", "pizza near me"],
    business_name="Your Business",
    business_street="123 Main St",
    business_city="New York",
    business_state="NY",
    business_country="US",
    latitude=40.7128,
    longitude=-74.0060,
    distance=10,
    distance_unit="mi",
    grid_size=3,
)

report_ids = result.get("reportIds", [])
print(f"Created {len(report_ids)} grid reports")

# Fetch results
for rid in report_ids:
    report = client.fetch_grid_report(rid)
    print(f"Keyword: {report.get('keyword')}")
    print(f"Grid points: {len(report.get('gridPoints', []))}")`
  },
  campaigns: {
    title: "Review Campaigns",
    filename: "10_review_campaign.py",
    code: `from synup import SynupClient

client = SynupClient(api_key="YOUR_API_KEY")

# Create a review campaign
customers = [
    {"name": "Alice Johnson", "email": "alice@example.com"},
    {"name": "Bob Smith", "email": "bob@example.com", "phone": "5551234567"},
]

result = client.create_review_campaign(
    location_id=16808,
    name="Q1 Feedback Campaign",
    location_customers=customers,
    screening=False,
)

if result.get("success"):
    campaign_id = result["reviewCampaign"]["id"]
    print(f"Created campaign: {result['reviewCampaign']['name']}")

    # Add more customers later
    client.add_review_campaign_customers(
        campaign_id,
        [{"name": "Charlie Davis", "email": "charlie@example.com"}],
    )`
  },
  fastapi: {
    title: "FastAPI Backend",
    filename: "11_fastapi_backend.py",
    code: `"""Wire the SDK into a FastAPI backend your frontend can call.
pip install synup-sdk fastapi uvicorn
SYNUP_API_KEY='key' uvicorn server:app --reload --port 8000
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from synup import SynupClient, SynupAPIError

app = FastAPI(title="Synup-powered API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])

@app.get("/locations")
def list_locations(first: int = Query(20), q: str | None = None):
    try:
        if q:
            return client.search_locations(query=q, first=first)
        return client.fetch_all_locations(first=first)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))

@app.get("/locations/{location_id}/listings")
def get_listings(location_id: str):
    try:
        return {
            "premium": client.fetch_premium_listings(location_id),
            "voice": client.fetch_voice_listings(location_id),
            "additional": client.fetch_additional_listings(location_id),
        }
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))

@app.get("/locations/{location_id}/reviews")
def get_reviews(location_id: str, first: int = Query(20)):
    try:
        return client.fetch_interactions(location_id, first=first)
    except SynupAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))`
  },
  fullstack: {
    title: "Full-stack Dashboard",
    filename: "fullstack/server.py",
    files: [
      {
        label: "Backend",
        filename: "fullstack/server.py",
        code: `"""Full-stack sample — FastAPI backend + basic frontend.

Run:
    pip install synup-sdk fastapi uvicorn
    SYNUP_API_KEY='key' python examples/fullstack/server.py
    # Open http://localhost:3000
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from synup import SynupClient, SynupAPIError

app = FastAPI()
client = SynupClient(api_key=os.environ["SYNUP_API_KEY"])
STATIC = Path(__file__).parent / "static"

# ── Locations (list, search, create, update, archive) ──

@app.get("/api/locations")
def list_locations(first: int = Query(10), q: str | None = None):
    if q:
        return client.search_locations(query=q, first=first)
    return client.fetch_all_locations(first=first)

@app.post("/api/locations")
def create_location(input: dict = Body(...)):
    return client.create_location(input)

@app.put("/api/locations")
def update_location(input: dict = Body(...)):
    return client.update_location(input)

@app.post("/api/locations/archive")
def archive_locations(location_ids: list[str] = Body(...)):
    return client.archive_locations(location_ids)

# ── Listings (premium, voice, additional — with links) ──

@app.get("/api/locations/{loc_id}/listings")
def get_listings(loc_id: str):
    return {
        "premium": client.fetch_premium_listings(loc_id),
        "voice": client.fetch_voice_listings(loc_id),
        "additional": client.fetch_additional_listings(loc_id),
    }

# ── Reviews (list + respond) ──

@app.get("/api/locations/{loc_id}/reviews")
def get_reviews(loc_id: str, first: int = Query(10)):
    return client.fetch_interactions(loc_id, first=first)

class ReviewResponse(BaseModel):
    content: str

@app.post("/api/reviews/{interaction_id}/respond")
def respond_to_review(interaction_id: str, body: ReviewResponse):
    return client.respond_to_review(interaction_id, body.content)

# ── Analytics, Grid Rank, Campaigns, Google Connect ──

@app.get("/api/locations/{loc_id}/analytics/google")
def google_analytics(loc_id: str):
    return client.fetch_google_analytics(loc_id)

@app.get("/api/locations/{loc_id}/analytics/reviews")
def review_analytics(loc_id: str):
    return client.fetch_review_analytics_overview(loc_id)

@app.get("/api/locations/{loc_id}/grid-reports")
def grid_reports(loc_id: str):
    return client.fetch_location_grid_reports(loc_id)

@app.get("/api/grid-report/{report_id}")
def get_grid_report(report_id: str):
    return client.fetch_grid_report(report_id)

@app.get("/api/locations/{loc_id}/campaigns")
def campaigns(loc_id: str):
    return client.fetch_review_campaigns(loc_id)

@app.post("/api/google/connect")
def google_connect(success_url: str = Body(...), error_url: str = Body(...)):
    return client.connect_google_account(
        success_url=success_url, error_url=error_url
    )

@app.get("/api/connected-accounts")
def connected_accounts():
    return client.fetch_connected_accounts(page=1, per_page=50)

# ── Serve frontend ──
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

@app.get("/")
def index():
    return FileResponse(str(STATIC / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)`
      },
      {
        label: "Frontend",
        filename: "fullstack/static/index.html",
        lang: "html",
        code: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Local Dashboard</title>
  <style>
    :root {
      --bg: #080A19; --bg-card: #0f1221; --accent: #0085FF;
      --green: #2cb735; --yellow: #e5c07b; --red: #e06c75;
      --text: #e1e4eb; --text-muted: #8b92a5;
      --border: rgba(255,255,255,0.08);
    }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }
    nav { border-bottom: 1px solid var(--border); padding: 12px 32px; display: flex; gap: 24px; }
    .nav-tab { padding: 8px 16px; border: none; background: none; color: var(--text-muted); cursor: pointer; }
    .nav-tab.active { color: var(--accent); background: rgba(0,133,255,0.1); border-radius: 6px; }
  </style>
</head>
<body>
  <nav>
    <a class="logo" href="#">Local Dashboard</a>
    <div class="nav-tabs">
      <button class="nav-tab active" onclick="showPage('home')">Home</button>
      <button class="nav-tab" onclick="showPage('analytics')">Analytics</button>
      <button class="nav-tab" onclick="showPage('gridrank')">Grid Rank</button>
      <button class="nav-tab" onclick="showPage('campaigns')">Campaigns</button>
      <button class="nav-tab" onclick="showPage('google')">Google Connect</button>
    </div>
  </nav>

  <div class="container">
    <!-- HOME: Location cards with search + add/edit/archive -->
    <div class="page active" id="page-home">
      <div class="search-row">
        <input id="locSearch" placeholder="Search locations...">
        <button class="btn btn-primary" onclick="searchLocations()">Search</button>
        <button class="btn btn-primary" onclick="openAddModal()">+ Add Location</button>
      </div>
      <div class="card-grid" id="locGrid"></div>
    </div>

    <!-- ANALYTICS: Google + Review analytics by location -->
    <div class="page" id="page-analytics">
      <input id="analyticsLocId" placeholder="Location ID">
      <button onclick="loadAnalytics()">Load Analytics</button>
      <div id="analyticsContent"></div>
    </div>

    <!-- GRID RANK: Reports table with drill-down -->
    <div class="page" id="page-gridrank">
      <input id="gridrankLocId" placeholder="Location ID">
      <button onclick="loadGridReports()">Load Reports</button>
      <div id="gridrankContent"></div>
    </div>

    <!-- CAMPAIGNS: Review campaign cards -->
    <div class="page" id="page-campaigns">
      <input id="campaignsLocId" placeholder="Location ID">
      <button onclick="loadCampaigns()">Load Campaigns</button>
      <div id="campaignsContent"></div>
    </div>

    <!-- GOOGLE CONNECT: OAuth flow + connected accounts -->
    <div class="page" id="page-google">
      <button onclick="startGoogleConnect()">Connect Google Account</button>
      <button onclick="loadConnectedAccounts()">View Connected Accounts</button>
      <div id="googleContent"></div>
    </div>
  </div>

  <!-- Detail panel: Listings + Reviews + Analytics tabs -->
  <div class="overlay" id="detailOverlay">
    <div class="panel">
      <h2 id="panelName"></h2>
      <div class="tab-bar">
        <button class="active" onclick="switchTab('listings')">Listings</button>
        <button onclick="switchTab('reviews')">Reviews</button>
        <button onclick="switchTab('analytics')">Analytics</button>
      </div>
      <div id="tab-listings"></div>
      <div id="tab-reviews"></div>
      <div id="tab-analytics"></div>
    </div>
  </div>

<script>
async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  return res.json();
}

// ── Locations ──
async function loadLocations(query) {
  const url = query ? \\\`/api/locations?q=\\\${query}&first=10\\\` : "/api/locations?first=10";
  const data = await api(url);
  renderLocationCards(data.locations || []);
}

function searchLocations() {
  loadLocations(document.getElementById("locSearch").value.trim());
}

// ── Detail panel with listings, reviews, respond ──
async function openDetail(loc) {
  currentLoc = loc;
  document.getElementById("panelName").textContent = loc.name;
  loadListings(loc.id);
  loadReviews(loc.id);
}

async function loadListings(locId) {
  const data = await api(\\\`/api/locations/\\\${locId}/listings\\\`);
  // Render premium, voice, additional listings in tables
}

async function loadReviews(locId) {
  const data = await api(\\\`/api/locations/\\\${locId}/reviews?first=10\\\`);
  // Render review cards with reply input for unanswered reviews
}

async function respondReview(interactionId) {
  const content = document.getElementById(\\\`reply-\\\${interactionId}\\\`).value;
  await api(\\\`/api/reviews/\\\${interactionId}/respond\\\`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

// ── Analytics ──
async function loadAnalytics() {
  const locId = document.getElementById("analyticsLocId").value;
  const [google, reviews] = await Promise.all([
    api(\\\`/api/locations/\\\${locId}/analytics/google\\\`),
    api(\\\`/api/locations/\\\${locId}/analytics/reviews\\\`),
  ]);
}

// ── Grid Rank ──
async function loadGridReports() {
  const locId = document.getElementById("gridrankLocId").value;
  const data = await api(\\\`/api/locations/\\\${locId}/grid-reports\\\`);
}

// ── Campaigns ──
async function loadCampaigns() {
  const locId = document.getElementById("campaignsLocId").value;
  const data = await api(\\\`/api/locations/\\\${locId}/campaigns\\\`);
}

// ── Google Connect ──
async function startGoogleConnect() {
  const data = await api("/api/google/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      success_url: location.origin + "/?google=success",
      error_url: location.origin + "/?google=error",
    }),
  });
  // Redirect user to data.url
}

async function loadConnectedAccounts() {
  const data = await api("/api/connected-accounts");
  // Render connected accounts table
}

document.addEventListener("DOMContentLoaded", () => loadLocations());
</script>
</body>
</html>`
      }
    ],
    code: `"""Full-stack sample — FastAPI backend + basic frontend.

Run:
    pip install synup-sdk fastapi uvicorn
    SYNUP_API_KEY='key' python examples/fullstack/server.py
    # Open http://localhost:3000

Full source: examples/fullstack/
    server.py          — FastAPI backend (all API routes)
    static/index.html  — Frontend (locations, listings, reviews, analytics)

Click the "Backend" and "Frontend" tabs above to see both files.
"""`
  },
};

function highlightPython(code) {
  // Escape HTML
  let html = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Comments (must come first)
  html = html.replace(/(#.*)/g, '<span class="py-cmt">$1</span>');

  // Strings (double and single quoted, including f-strings)
  html = html.replace(/(f?"[^"]*"|f?'[^']*')/g, '<span class="py-str">$1</span>');

  // Keywords
  const kws = ['from', 'import', 'if', 'for', 'in', 'not', 'and', 'or', 'with', 'as', 'try', 'except', 'True', 'False', 'None', 'return', 'def', 'class', 'else', 'elif', 'print', 'open', 'len', 'bool', 'int', 'str'];
  kws.forEach(kw => {
    html = html.replace(new RegExp(`\\b(${kw})\\b(?![^<]*>)`, 'g'), '<span class="py-kw">$1</span>');
  });

  // Class names (capitalized words like SynupClient, DictWriter)
  html = html.replace(/\b([A-Z][a-zA-Z]+)\b(?![^<]*>)/g, '<span class="py-cls">$1</span>');

  // Numbers
  html = html.replace(/\b(\d+\.?\d*)\b(?![^<]*>)/g, '<span class="py-num">$1</span>');

  return html;
}

let activeExampleKey = null;
let activeFileIndex = 0;

function showExample(key) {
  const ex = EXAMPLES[key];
  if (!ex) return;
  activeExampleKey = key;
  activeFileIndex = 0;

  document.getElementById("modalTitle").textContent = ex.title;
  const tabsEl = document.getElementById("modalTabs");

  if (ex.files && ex.files.length > 1) {
    // Multi-file example: show tabs
    tabsEl.style.display = "flex";
    tabsEl.innerHTML = ex.files.map((f, i) =>
      `<button class="modal-tab${i === 0 ? ' active' : ''}" onclick="switchExampleTab(${i})">${f.label}</button>`
    ).join("");
    renderExampleFile(ex.files[0]);
  } else {
    // Single-file example
    tabsEl.style.display = "none";
    tabsEl.innerHTML = "";
    document.getElementById("modalFilename").textContent = ex.filename;
    document.getElementById("modalCode").innerHTML = highlightPython(ex.code);
  }

  document.getElementById("exampleModal").classList.add("active");
}

function switchExampleTab(index) {
  const ex = EXAMPLES[activeExampleKey];
  if (!ex || !ex.files) return;
  activeFileIndex = index;

  // Update tab active state
  document.querySelectorAll("#modalTabs .modal-tab").forEach((btn, i) => {
    btn.classList.toggle("active", i === index);
  });

  renderExampleFile(ex.files[index]);
}

function renderExampleFile(file) {
  document.getElementById("modalFilename").textContent = file.filename;
  if (file.lang === "html") {
    document.getElementById("modalCode").innerHTML = highlightHTML(file.code);
  } else {
    document.getElementById("modalCode").innerHTML = highlightPython(file.code);
  }
}

function highlightHTML(code) {
  let html = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // Tags
  html = html.replace(/(&lt;\/?)([\w-]+)/g, '$1<span class="py-kw">$2</span>');
  // Attributes
  html = html.replace(/\b(class|id|type|href|src|onclick|placeholder|value|style|charset|name|content|rel|lang)=/g, '<span class="py-cls">$1</span>=');
  // Strings
  html = html.replace(/("(?:[^"\\]|\\.)*")/g, '<span class="py-str">$1</span>');
  // Comments
  html = html.replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="py-cmt">$1</span>');
  // JS keywords inside script
  const jsKws = ['async', 'await', 'function', 'const', 'let', 'var', 'return', 'if', 'for', 'document', 'window', 'location'];
  jsKws.forEach(kw => {
    html = html.replace(new RegExp(`\\b(${kw})\\b(?![^<]*>)`, 'g'), '<span class="py-kw">$1</span>');
  });
  return html;
}

function closeExample(event) {
  if (event && event.target !== event.currentTarget) return;
  document.getElementById("exampleModal").classList.remove("active");
}

function copyCode() {
  const ex = EXAMPLES[activeExampleKey];
  let code;
  if (ex && ex.files && ex.files.length > 1) {
    code = ex.files[activeFileIndex].code;
  } else {
    code = document.getElementById("modalCode").textContent;
  }
  const btn = document.getElementById("copyBtn");
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copy";
      btn.classList.remove("copied");
    }, 2000);
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.getElementById("exampleModal").classList.remove("active");
  }
});

const SDK_METHODS = [
  // --- Locations ---
  { name: "fetch_all_locations", category: "Locations", doc: "Get locations for the account, with optional pagination or fetch-all.", params: [
    { name: "first", type: "int", required: false },
    { name: "after", type: "str", required: false },
  ]},
  { name: "fetch_locations_by_ids", category: "Locations", doc: "Get locations by a list of IDs. Accepts numeric or base64-encoded IDs.", params: [
    { name: "location_ids", type: "json", required: true, placeholder: '["16808"]' },
  ]},
  { name: "fetch_locations_by_store_codes", category: "Locations", doc: "Get locations that match the given store codes.", params: [
    { name: "store_codes", type: "json", required: true, placeholder: '["STORE01"]' },
  ]},
  { name: "search_locations", category: "Locations", doc: "Search locations by keyword (name, address, or store ID).", params: [
    { name: "query", type: "str", required: true },
    { name: "first", type: "int", required: false },
  ]},
  { name: "fetch_locations_by_folder", category: "Locations", doc: "Get all locations in a folder.", params: [
    { name: "folder_name", type: "str", required: false },
    { name: "folder_id", type: "str", required: false },
  ]},
  { name: "fetch_locations_by_tags", category: "Locations", doc: "Get locations that have any of the given tags.", params: [
    { name: "tags", type: "json", required: true, placeholder: '["recent"]' },
    { name: "first", type: "int", required: false },
  ]},
  { name: "create_location", category: "Locations", doc: "Create a new location. Use camelCase keys.", params: [
    { name: "input", type: "json", required: true, placeholder: '{"name":"...","storeId":"...","street":"...","city":"...","stateIso":"...","postalCode":"...","countryIso":"...","phone":"..."}' },
  ]},
  { name: "update_location", category: "Locations", doc: "Update a location. Pass id plus fields to change.", params: [
    { name: "input", type: "json", required: true, placeholder: '{"id":"16808","phone":"5559876543"}' },
  ]},
  { name: "archive_locations", category: "Locations", doc: "Archive one or more locations.", params: [
    { name: "location_ids", type: "json", required: true, placeholder: '["16808"]' },
  ]},
  { name: "activate_locations", category: "Locations", doc: "Reactivate previously archived locations.", params: [
    { name: "location_ids", type: "json", required: true, placeholder: '["16808"]' },
  ]},

  // --- Listings ---
  { name: "fetch_premium_listings", category: "Listings", doc: "Get premium (directory) listings for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "fetch_voice_listings", category: "Listings", doc: "Get voice assistant listings for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "fetch_additional_listings", category: "Listings", doc: "Get additional (non-premium) listings for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "fetch_ai_listings", category: "Listings", doc: "Get AI-generated listing suggestions for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},

  // --- Reviews ---
  { name: "fetch_interactions", category: "Reviews", doc: "Get reviews and interactions for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "first", type: "int", required: false },
    { name: "start_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "end_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},
  { name: "fetch_review_settings", category: "Reviews", doc: "Get review source settings for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "respond_to_review", category: "Reviews", doc: "Post a reply to a review.", params: [
    { name: "interaction_id", type: "str", required: true },
    { name: "response_content", type: "str", required: true },
  ]},
  { name: "fetch_review_analytics_overview", category: "Reviews", doc: "Get overall review analytics for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "start_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "end_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},

  // --- Rankings ---
  { name: "fetch_keywords", category: "Rankings", doc: "Get all keywords tracked for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "fetch_keywords_performance", category: "Rankings", doc: "Get ranking performance for a location's keywords.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "from_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "to_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},
  { name: "add_keywords", category: "Rankings", doc: "Add keywords to a location for ranking tracking.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "keywords", type: "json", required: true, placeholder: '["plumber","plumbing near me"]' },
  ]},

  // --- Analytics ---
  { name: "fetch_google_analytics", category: "Analytics", doc: "Get Google (GMB) profile analytics for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "from_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "to_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},
  { name: "fetch_bing_analytics", category: "Analytics", doc: "Get Bing profile analytics for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "from_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "to_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},
  { name: "fetch_facebook_analytics", category: "Analytics", doc: "Get Facebook page analytics for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "from_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "to_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},

  // --- Photos ---
  { name: "fetch_location_photos", category: "Photos", doc: "Get photos and media attached to a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
  { name: "add_location_photos", category: "Photos", doc: "Add photos to a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "photos", type: "json", required: true, placeholder: '[{"photo":"https://...","type":"LOGO"}]' },
  ]},

  // --- Folders ---
  { name: "fetch_folders_flat", category: "Folders", doc: "Get all folders as a flat list.", params: [] },
  { name: "fetch_folders_tree", category: "Folders", doc: "Get all folders as a nested tree structure.", params: [] },
  { name: "create_folder", category: "Folders", doc: "Create a folder to organize locations.", params: [
    { name: "name", type: "str", required: true },
    { name: "parent_folder_name", type: "str", required: false },
  ]},

  // --- Tags ---
  { name: "fetch_tags", category: "Tags", doc: "Get all tags defined in the account.", params: [] },
  { name: "add_location_tag", category: "Tags", doc: "Add a tag to a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "tag", type: "str", required: true },
  ]},

  // --- Users ---
  { name: "fetch_users", category: "Users", doc: "Get all users in the account.", params: [] },
  { name: "fetch_roles", category: "Users", doc: "Get all roles defined in the account.", params: [] },
  { name: "create_user", category: "Users", doc: "Create a user with the given role.", params: [
    { name: "email", type: "str", required: true },
    { name: "role_id", type: "str", required: true },
    { name: "first_name", type: "str", required: true },
    { name: "last_name", type: "str", required: false },
  ]},

  // --- Grid Rank ---
  { name: "fetch_location_grid_reports", category: "Grid Rank", doc: "Get all Local Rank Grid reports for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "page_size", type: "int", required: false },
    { name: "page", type: "int", required: false },
  ]},
  { name: "fetch_grid_report", category: "Grid Rank", doc: "Get a grid rank report by its ID.", params: [
    { name: "report_id", type: "str", required: true },
  ]},

  // --- Review Campaigns ---
  { name: "fetch_review_campaigns", category: "Campaigns", doc: "Get review campaigns for a location.", params: [
    { name: "location_id", type: "str", required: true },
    { name: "start_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
    { name: "end_date", type: "str", required: false, placeholder: "YYYY-MM-DD" },
  ]},

  // --- Connected Accounts ---
  { name: "fetch_connected_accounts", category: "Connected Accounts", doc: "Get connected third-party accounts.", params: [
    { name: "publisher", type: "str", required: false, placeholder: "google" },
    { name: "page", type: "int", required: false },
  ]},

  // --- Account ---
  { name: "fetch_plan_sites", category: "Account", doc: "Get supported directories for your plan.", params: [] },
  { name: "fetch_countries", category: "Account", doc: "Get supported countries and states.", params: [] },
  { name: "fetch_subscriptions", category: "Account", doc: "Get active subscriptions for the account.", params: [] },
  { name: "fetch_review_site_config", category: "Account", doc: "Get eligible review sources and site config.", params: [] },
  { name: "fetch_connection_info", category: "Account", doc: "Get OAuth connection status for a location.", params: [
    { name: "location_id", type: "str", required: true },
  ]},
];

// --- State ---
let selectedMethod = null;

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  populateCategories();
  renderMethodList();

  document.getElementById("categorySelect").addEventListener("change", renderMethodList);
  document.getElementById("searchInput").addEventListener("input", renderMethodList);
});

function populateCategories() {
  const select = document.getElementById("categorySelect");
  const cats = [...new Set(SDK_METHODS.map(m => m.category))].sort();
  cats.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    select.appendChild(opt);
  });
}

function renderMethodList() {
  const list = document.getElementById("methodList");
  const category = document.getElementById("categorySelect").value;
  const search = document.getElementById("searchInput").value.toLowerCase();

  let filtered = SDK_METHODS;
  if (category !== "all") {
    filtered = filtered.filter(m => m.category === category);
  }
  if (search) {
    filtered = filtered.filter(m => m.name.toLowerCase().includes(search));
  }

  list.innerHTML = "";
  filtered.forEach(method => {
    const el = document.createElement("div");
    el.className = "method-item" + (selectedMethod === method.name ? " active" : "");
    el.textContent = method.name;
    el.addEventListener("click", () => selectMethod(method));
    list.appendChild(el);
  });
}

function selectMethod(method) {
  selectedMethod = method.name;
  renderMethodList();
  renderMethodDetail(method);
}

function renderMethodDetail(method) {
  const detail = document.getElementById("methodDetail");

  let paramsHTML = "";
  if (method.params.length > 0) {
    paramsHTML = `<div class="explorer-params">`;
    method.params.forEach(p => {
      const req = p.required ? '<span class="required">*</span>' : '';
      paramsHTML += `
        <div class="param-row">
          <label class="param-label">${p.name}${req}</label>
          <input class="param-input" id="param-${p.name}" type="text"
                 placeholder="${p.placeholder || p.type}" data-type="${p.type}">
        </div>`;
    });
    paramsHTML += `</div>`;
  }

  detail.innerHTML = `
    <div class="explorer-method-title">${method.name}</div>
    <div class="explorer-method-doc">${method.doc}</div>
    ${paramsHTML}
    <button class="explorer-execute" onclick="executeMethod('${method.name}')">Execute</button>
    <div class="explorer-result" id="result" style="display:none">
      <pre id="resultPre"></pre>
    </div>
  `;
}

async function executeMethod(methodName) {
  const apiKey = document.getElementById("apiKeyInput").value;
  if (!apiKey) {
    showResult({ error: "Enter your API key in the sidebar" });
    return;
  }

  const method = SDK_METHODS.find(m => m.name === methodName);
  if (!method) return;

  // Collect params
  const params = {};
  method.params.forEach(p => {
    const input = document.getElementById(`param-${p.name}`);
    if (!input) return;
    const val = input.value.trim();
    if (!val) return;

    if (p.type === "int") {
      params[p.name] = parseInt(val, 10);
    } else if (p.type === "json") {
      try { params[p.name] = JSON.parse(val); }
      catch { params[p.name] = val; }
    } else {
      params[p.name] = val;
    }
  });

  showResult({ status: "Loading..." });

  // Build the Python-style method call description for display
  try {
    const response = await callSynupAPI(apiKey, methodName, params, method);
    showResult(response);
  } catch (err) {
    showResult({ error: err.message });
  }
}

async function callSynupAPI(apiKey, methodName, params, method) {
  // Route through HF backend proxy which forwards to Synup API
  const isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  const BACKEND = isLocal ? "" : "https://basu2604-synup-sdk.hf.space";
  const BASE = `${BACKEND}/api/v4`;
  const headers = {
    "X-API-Key": apiKey,
    "Content-Type": "application/json",
  };

  // Encode location ID helper
  function encodeLocId(id) {
    const s = String(id).trim();
    if (/^\d+$/.test(s)) {
      return btoa(`Location:${s}`);
    }
    return s;
  }

  // Route to the correct endpoint
  let url, fetchOpts;

  switch (methodName) {
    // --- GET: Locations ---
    case "fetch_all_locations": {
      const qs = new URLSearchParams();
      if (params.first) qs.set("first", params.first);
      if (params.after) qs.set("after", params.after);
      url = `${BASE}/locations?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_locations_by_ids": {
      const ids = (params.location_ids || []).map(encodeLocId);
      url = `${BASE}/locations-by-ids?ids=${encodeURIComponent(JSON.stringify(ids))}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_locations_by_store_codes": {
      url = `${BASE}/locations-by-store-codes?storeCodes=${encodeURIComponent(JSON.stringify(params.store_codes || []))}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "search_locations": {
      const qs = new URLSearchParams({ query: params.query || "" });
      if (params.first) qs.set("first", params.first);
      url = `${BASE}/locations/search?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_locations_by_folder": {
      const qs = new URLSearchParams();
      if (params.folder_id) qs.set("folderId", params.folder_id);
      if (params.folder_name) qs.set("folderName", params.folder_name);
      url = `${BASE}/folder-locations?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_locations_by_tags": {
      const qs = new URLSearchParams({ tags: JSON.stringify(params.tags || []) });
      if (params.first) qs.set("first", params.first);
      url = `${BASE}/tags/locations?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }

    // --- POST: Location mutations ---
    case "create_location":
      url = `${BASE}/locations`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: params.input }) };
      break;
    case "update_location": {
      const input = { ...params.input };
      if (input.id) input.id = encodeLocId(input.id);
      url = `${BASE}/locations/update`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input }) };
      break;
    }
    case "archive_locations": {
      const ids = (params.location_ids || []).map(encodeLocId);
      url = `${BASE}/locations/archive`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: { locationIds: ids } }) };
      break;
    }
    case "activate_locations": {
      const ids = (params.location_ids || []).map(encodeLocId);
      url = `${BASE}/locations/activate`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: { locationIds: ids } }) };
      break;
    }

    // --- GET: Listings ---
    case "fetch_premium_listings":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/listings/premium`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_voice_listings":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/voice-assistants`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_additional_listings":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/listings/additional`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_ai_listings":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/ai-listings`;
      fetchOpts = { method: "GET", headers };
      break;

    // --- GET/POST: Reviews ---
    case "fetch_interactions": {
      const qs = new URLSearchParams();
      if (params.first) qs.set("first", params.first);
      if (params.start_date) qs.set("startDate", params.start_date);
      if (params.end_date) qs.set("endDate", params.end_date);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/reviews?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_review_settings":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/reviews/settings`;
      fetchOpts = { method: "GET", headers };
      break;
    case "respond_to_review":
      url = `${BASE}/locations/reviews/respond`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ interactionId: params.interaction_id, responseContent: params.response_content }) };
      break;
    case "fetch_review_analytics_overview": {
      const qs = new URLSearchParams();
      if (params.start_date) qs.set("startDate", params.start_date);
      if (params.end_date) qs.set("endDate", params.end_date);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/review-analytics-overview?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }

    // --- Rankings ---
    case "fetch_keywords":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/keywords`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_keywords_performance": {
      const qs = new URLSearchParams();
      if (params.from_date) qs.set("fromDate", params.from_date);
      if (params.to_date) qs.set("toDate", params.to_date);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/keywords-performance?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "add_keywords":
      url = `${BASE}/locations/keywords`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ locationId: encodeLocId(params.location_id), inputKeywords: params.keywords }) };
      break;

    // --- Analytics ---
    case "fetch_google_analytics":
    case "fetch_bing_analytics":
    case "fetch_facebook_analytics": {
      const typeMap = { fetch_google_analytics: "google-analytics", fetch_bing_analytics: "bing-analytics", fetch_facebook_analytics: "facebook-analytics" };
      const qs = new URLSearchParams();
      if (params.from_date) qs.set("fromDate", params.from_date);
      if (params.to_date) qs.set("toDate", params.to_date);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/${typeMap[methodName]}?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }

    // --- Photos ---
    case "fetch_location_photos":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/photos`;
      fetchOpts = { method: "GET", headers };
      break;
    case "add_location_photos":
      url = `${BASE}/locations/photos`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: { locationId: encodeLocId(params.location_id), photos: params.photos } }) };
      break;

    // --- Folders ---
    case "fetch_folders_flat":
      url = `${BASE}/folders/flat`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_folders_tree":
      url = `${BASE}/folders/tree`;
      fetchOpts = { method: "GET", headers };
      break;
    case "create_folder": {
      const payload = { name: params.name };
      if (params.parent_folder_name) payload.parentFolderName = params.parent_folder_name;
      url = `${BASE}/folders/create`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: payload }) };
      break;
    }

    // --- Tags ---
    case "fetch_tags":
      url = `${BASE}/tags`;
      fetchOpts = { method: "GET", headers };
      break;
    case "add_location_tag":
      url = `${BASE}/locations/tags`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: { locationId: encodeLocId(params.location_id), tag: params.tag } }) };
      break;

    // --- Users ---
    case "fetch_users":
      url = `${BASE}/users`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_roles":
      url = `${BASE}/roles`;
      fetchOpts = { method: "GET", headers };
      break;
    case "create_user":
      url = `${BASE}/users/create`;
      fetchOpts = { method: "POST", headers, body: JSON.stringify({ input: { email: params.email, roleId: params.role_id, firstName: params.first_name, lastName: params.last_name } }) };
      break;

    // --- Grid Rank ---
    case "fetch_location_grid_reports": {
      const qs = new URLSearchParams();
      if (params.page_size) qs.set("pageSize", params.page_size);
      if (params.page) qs.set("page", params.page);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/grid-reports?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }
    case "fetch_grid_report":
      url = `${BASE}/grid-report/${params.report_id}`;
      fetchOpts = { method: "GET", headers };
      break;

    // --- Review Campaigns ---
    case "fetch_review_campaigns": {
      const qs = new URLSearchParams();
      if (params.start_date) qs.set("startDate", params.start_date);
      if (params.end_date) qs.set("endDate", params.end_date);
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/review-campaigns?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }

    // --- Connected Accounts ---
    case "fetch_connected_accounts": {
      const qs = new URLSearchParams();
      if (params.publisher) qs.set("publisher", params.publisher);
      if (params.page) qs.set("page", params.page);
      url = `${BASE}/connected-accounts?${qs}`;
      fetchOpts = { method: "GET", headers };
      break;
    }

    // --- Account ---
    case "fetch_plan_sites":
      url = `${BASE}/plan-sites`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_countries":
      url = `${BASE}/countries`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_subscriptions":
      url = `${BASE}/subscriptions`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_review_site_config":
      url = `${BASE}/reviews/site-config`;
      fetchOpts = { method: "GET", headers };
      break;
    case "fetch_connection_info":
      url = `${BASE}/locations/${encodeLocId(params.location_id)}/connection_info`;
      fetchOpts = { method: "GET", headers };
      break;

    default:
      return { error: `Method ${methodName} not implemented in explorer yet` };
  }

  const resp = await fetch(url, fetchOpts);
  const data = await resp.json();
  return data;
}

function showResult(data) {
  const container = document.getElementById("result");
  const pre = document.getElementById("resultPre");
  if (container && pre) {
    container.style.display = "block";
    pre.textContent = JSON.stringify(data, null, 2);
  }
}
