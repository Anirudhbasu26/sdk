"""Bulk export: Download all locations to a CSV file.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 02_bulk_export_locations.py
"""

import csv
import os
from synup import SynupClient

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

# Fetch ALL locations (auto-paginates)
locations = client.fetch_all_locations(fetch_all=True)
print(f"Fetched {len(locations)} locations")

# Write to CSV
output_file = "locations_export.csv"
fields = ["id", "name", "storeId", "street", "city", "stateIso", "postalCode", "countryIso", "phone"]

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(locations)

print(f"Exported to {output_file}")
