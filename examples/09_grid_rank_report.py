"""Grid Rank: Create a Local Rank Grid report and fetch results.

A grid rank report shows your Google ranking for keywords at multiple
points on a geographic grid around your location.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 09_grid_rank_report.py
"""

import os
import time
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

LOCATION_ID = 16808  # Replace with your location ID

# Create a grid rank report
result = client.create_grid_report(
    location_id=LOCATION_ID,
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
    grid_size=3,  # 3x3 grid
)

report_ids = result.get("reportIds") or []
print(f"Created {len(report_ids)} grid reports")

# Wait and fetch results
if report_ids:
    print("Waiting for report generation...")
    time.sleep(10)

    for rid in report_ids:
        report = client.fetch_grid_report(rid)
        print(f"\nReport {rid}:")
        print(f"  Keyword: {report.get('keyword')}")
        print(f"  Grid data: {len(report.get('gridPoints', []))} points")

# List all reports for this location
all_reports = client.fetch_location_grid_reports(LOCATION_ID, page_size=5, page=1)
print(f"\nTotal grid reports: {all_reports.get('total', 0)}")
