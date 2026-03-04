"""Bulk respond: Reply to all unanswered reviews with a template.

This example shows the pattern. In production, use an LLM to generate
personalized responses based on review content.

Usage:
    export SYNUP_API_KEY="your_api_key"
    python 04_bulk_respond_reviews.py
"""

import os
from synup import SynupClient, SynupAPIError

api_key = os.environ["SYNUP_API_KEY"]
client = SynupClient(api_key=api_key)

LOCATION_ID = 16808  # Replace with your location ID

TEMPLATES = {
    5: "Thank you so much for the wonderful review! We're thrilled you had a great experience.",
    4: "Thank you for your kind review! We're glad you enjoyed your visit.",
    3: "Thank you for your feedback. We'd love to hear how we can improve — please reach out to us directly.",
    2: "We're sorry to hear about your experience. Please contact us so we can make it right.",
    1: "We sincerely apologize for your experience. Please reach out to us directly so we can resolve this.",
}

# Fetch unanswered reviews
reviews = client.fetch_interactions(LOCATION_ID, first=50)

unanswered = [
    r for r in reviews.get("interactions", [])
    if not r.get("responses") and r.get("interactionId")
]
print(f"Found {len(unanswered)} unanswered reviews")

for review in unanswered:
    rating = review.get("rating", 3)
    template = TEMPLATES.get(rating, TEMPLATES[3])
    interaction_id = review["interactionId"]

    try:
        client.respond_to_review(interaction_id, template)
        print(f"  Replied to {review.get('authorName', 'Anonymous')} ({rating} stars)")
    except SynupAPIError as e:
        print(f"  Failed: {e} (status {e.status_code})")
