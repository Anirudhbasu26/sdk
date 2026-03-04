"""Synup MCP Server — exposes synup-sdk methods as MCP tools for LLM agents.

Authentication:
    Set the SYNUP_API_KEY environment variable with your Synup API key.
    For HTTP transport, pass: Authorization: Bearer {base64(api_key:{key};user_email:{email})}

Usage:
    # stdio (Claude Desktop, MCP Inspector)
    SYNUP_API_KEY=your_key python server.py

    # Or configure in Claude Desktop's claude_desktop_config.json
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Any, Optional

from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated

from synup import SynupClient

mcp = FastMCP(
    name="Synup",
    instructions=(
        "You have access to the full Synup API through this MCP server. "
        "Use these tools to manage business locations, listings, reviews, "
        "rankings, and analytics. All write operations take effect immediately. "
        "Location IDs can be provided as numeric IDs or base64-encoded strings.\n\n"
        "EFFICIENCY RULES — always follow these:\n"
        "1. Use list_locations (not get_all_locations) when you only need IDs, names, or cities.\n"
        "2. Use get_account_review_summary (not looping get_review_analytics_overview) to get review totals across locations.\n"
        "3. Never call the same tool in a loop when an aggregate tool exists."
    ),
)


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Extract API key from SYNUP_API_KEY env var or HTTP Authorization header.

    Header format (HTTP transport):
        Authorization: Bearer {base64(api_key:{key};user_email:{email})}
    """
    api_key = os.getenv("SYNUP_API_KEY")
    if api_key:
        return api_key

    # Try to parse from Authorization header (HTTP transport)
    try:
        from fastmcp.server.context import get_http_headers  # type: ignore[import]
        headers = get_http_headers()
        if headers:
            auth = headers.get("authorization", "") or headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
                decoded = base64.b64decode(token + "==").decode("utf-8")
                for part in decoded.split(";"):
                    if part.startswith("api_key:"):
                        return part[8:].strip()
    except Exception:
        pass

    raise ValueError(
        "Synup API key not found. Set the SYNUP_API_KEY environment variable, "
        "or pass an Authorization header: "
        "Bearer {base64(api_key:YOUR_KEY;user_email:YOUR_EMAIL)}"
    )


def _get_client() -> SynupClient:
    """Create a SynupClient using the API key from the current request context."""
    return SynupClient(api_key=_get_api_key())


# ---------------------------------------------------------------------------
# Location tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_all_locations(
    first: Annotated[Optional[int], Field(default=None, description="Number of locations to return from the start (default: all)")] = None,
    after: Annotated[Optional[str], Field(default=None, description="Pagination cursor — return locations after this cursor")] = None,
    fetch_all: Annotated[bool, Field(default=False, description="If true, fetch all locations across all pages and return as a flat list")] = False,
    page_size: Annotated[int, Field(default=100, description="Page size when fetch_all is true (default: 100)")] = 100,
) -> dict[str, Any]:
    """Get all locations in the account with optional pagination.

    Returns a paginated list of locations, or all locations if fetch_all is true.
    Each location includes id, name, street, city, state, phone, storeId, and more.
    """
    client = _get_client()
    result = await asyncio.to_thread(
        client.fetch_all_locations,
        first=first,
        after=after,
        fetch_all=fetch_all,
        page_size=page_size,
    )
    if isinstance(result, list):
        return {"success": True, "locations": result, "total": len(result)}
    return result


@mcp.tool()
async def get_locations_by_ids(
    location_ids: Annotated[list[str], Field(description="List of location IDs (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get specific locations by their IDs.

    Accepts numeric IDs (e.g. 16808) or base64-encoded IDs. Returns full location details.
    """
    client = _get_client()
    locations = await asyncio.to_thread(client.fetch_locations_by_ids, location_ids)
    return {"success": True, "locations": locations, "total": len(locations)}


@mcp.tool()
async def get_locations_by_store_codes(
    store_codes: Annotated[list[str], Field(description="List of store codes (e.g. ['STORE01', 'STORE02'])")],
) -> dict[str, Any]:
    """Get locations by their store codes.

    Useful when you know the store identifiers but not the internal location IDs.
    """
    client = _get_client()
    locations = await asyncio.to_thread(client.fetch_locations_by_store_codes, store_codes)
    return {"success": True, "locations": locations, "total": len(locations)}


@mcp.tool()
async def search_locations(
    query: Annotated[str, Field(description="Search term to match against location name, street, or store ID")],
    fields: Annotated[Optional[list[str]], Field(default=None, description="Restrict search to specific fields, e.g. ['name'] or ['store_id']. If omitted, all fields are searched.")] = None,
    first: Annotated[Optional[int], Field(default=None, description="Max number of results to return")] = None,
    fetch_all: Annotated[bool, Field(default=False, description="If true, return all matching locations across all pages")] = False,
) -> dict[str, Any]:
    """Search locations by keyword across name, address, or store ID.

    Returns matching locations with full details. Use fetch_all=true to get all matches.
    """
    client = _get_client()
    result = await asyncio.to_thread(
        client.search_locations,
        query=query,
        fields=fields,
        first=first,
        fetch_all=fetch_all,
    )
    if isinstance(result, list):
        return {"success": True, "locations": result, "total": len(result)}
    return result


@mcp.tool()
async def get_locations_by_folder(
    folder_id: Annotated[Optional[str], Field(default=None, description="Folder UUID")] = None,
    folder_name: Annotated[Optional[str], Field(default=None, description="Human-readable folder name (e.g. 'franchise')")] = None,
) -> dict[str, Any]:
    """Get all locations in a folder (including subfolders).

    Provide either folder_id or folder_name. Returns all locations in that folder.
    """
    client = _get_client()
    locations = await asyncio.to_thread(
        client.fetch_locations_by_folder,
        folder_id=folder_id,
        folder_name=folder_name,
    )
    return {"success": True, "locations": locations, "total": len(locations)}


@mcp.tool()
async def get_locations_by_tags(
    tags: Annotated[list[str], Field(description="List of tag names — locations with any of these tags are returned")],
    archived: Annotated[Optional[bool], Field(default=None, description="Filter by archived status: true=archived only, false=active only, null=both")] = None,
    fetch_all: Annotated[bool, Field(default=False, description="If true, return all matching locations across all pages")] = False,
) -> dict[str, Any]:
    """Get locations that have any of the specified tags.

    Returns all locations tagged with at least one of the provided tag names.
    """
    client = _get_client()
    result = await asyncio.to_thread(
        client.fetch_locations_by_tags,
        tags=tags,
        archived=archived,
        fetch_all=fetch_all,
    )
    if isinstance(result, list):
        return {"success": True, "locations": result, "total": len(result)}
    return result


@mcp.tool()
async def create_location(
    name: Annotated[str, Field(description="Business name")],
    store_id: Annotated[str, Field(description="Unique store code/identifier for this location")],
    street: Annotated[str, Field(description="Street address")],
    city: Annotated[str, Field(description="City name")],
    state_iso: Annotated[str, Field(description="State/region code (e.g. 'CA', 'NY')")],
    postal_code: Annotated[str, Field(description="ZIP or postal code")],
    country_iso: Annotated[str, Field(description="Country code (e.g. 'US', 'CA', 'GB')")],
    phone: Annotated[str, Field(description="Business phone number")],
    description: Annotated[Optional[str], Field(default=None, description="Business description")] = None,
    website: Annotated[Optional[str], Field(default=None, description="Business website URL")] = None,
    email: Annotated[Optional[str], Field(default=None, description="Business email address")] = None,
    owner_name: Annotated[Optional[str], Field(default=None, description="Owner's name")] = None,
    owner_email: Annotated[Optional[str], Field(default=None, description="Owner's email address")] = None,
) -> dict[str, Any]:
    """Create a new location in the account.

    All required fields must be provided. Returns the created location object on success.
    """
    client = _get_client()
    input_data: dict[str, Any] = {
        "name": name,
        "storeId": store_id,
        "street": street,
        "city": city,
        "stateIso": state_iso,
        "postalCode": postal_code,
        "countryIso": country_iso,
        "phone": phone,
    }
    if description is not None:
        input_data["description"] = description
    if website is not None:
        input_data["website"] = website
    if email is not None:
        input_data["email"] = email
    if owner_name is not None:
        input_data["ownerName"] = owner_name
    if owner_email is not None:
        input_data["ownerEmail"] = owner_email
    return await asyncio.to_thread(client.create_location, input_data)


@mcp.tool()
async def update_location(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    name: Annotated[Optional[str], Field(default=None, description="Business name")] = None,
    phone: Annotated[Optional[str], Field(default=None, description="Phone number")] = None,
    street: Annotated[Optional[str], Field(default=None, description="Street address")] = None,
    city: Annotated[Optional[str], Field(default=None, description="City name")] = None,
    state_iso: Annotated[Optional[str], Field(default=None, description="State/region code (e.g. 'CA')")] = None,
    country_iso: Annotated[Optional[str], Field(default=None, description="Country code (e.g. 'US')")] = None,
    postal_code: Annotated[Optional[str], Field(default=None, description="ZIP/postal code")] = None,
    website: Annotated[Optional[str], Field(default=None, description="Website URL")] = None,
    description: Annotated[Optional[str], Field(default=None, description="Business description")] = None,
    store_id: Annotated[Optional[str], Field(default=None, description="Store code/identifier")] = None,
    email: Annotated[Optional[str], Field(default=None, description="Business email address")] = None,
    temporarily_closed: Annotated[Optional[bool], Field(default=None, description="Whether the location is temporarily closed")] = None,
    tags: Annotated[Optional[list[str]], Field(default=None, description="List of tags to set on the location")] = None,
) -> dict[str, Any]:
    """Update a location's information.

    Only pass fields you want to change. The location_id is always required.
    Returns the updated location on success.
    """
    client = _get_client()
    input_data: dict[str, Any] = {"id": location_id}
    if name is not None:
        input_data["name"] = name
    if phone is not None:
        input_data["phone"] = phone
    if street is not None:
        input_data["street"] = street
    if city is not None:
        input_data["city"] = city
    if state_iso is not None:
        input_data["stateIso"] = state_iso
    if country_iso is not None:
        input_data["countryIso"] = country_iso
    if postal_code is not None:
        input_data["postalCode"] = postal_code
    if website is not None:
        input_data["website"] = website
    if description is not None:
        input_data["description"] = description
    if store_id is not None:
        input_data["storeId"] = store_id
    if email is not None:
        input_data["email"] = email
    if temporarily_closed is not None:
        input_data["temporarilyClosed"] = temporarily_closed
    if tags is not None:
        input_data["tags"] = tags
    return await asyncio.to_thread(client.update_location, input_data)


@mcp.tool()
async def archive_locations(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to archive")],
) -> dict[str, Any]:
    """Archive one or more locations (hidden, not deleted).

    Archived locations can be reactivated later with activate_locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.archive_locations, location_ids)


@mcp.tool()
async def activate_locations(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to reactivate")],
) -> dict[str, Any]:
    """Reactivate previously archived locations.

    Use this to restore locations that were archived with archive_locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.activate_locations, location_ids)


# ---------------------------------------------------------------------------
# User management tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_users() -> dict[str, Any]:
    """Get all users in the account.

    Returns a list of users with their id, email, name, role, and other details.
    """
    client = _get_client()
    users = await asyncio.to_thread(client.fetch_users)
    return {"success": True, "users": users, "total": len(users)}


# ---------------------------------------------------------------------------
# Lightweight / aggregate tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_locations(
    search: Annotated[Optional[str], Field(default=None, description="Optional search term to filter locations by name, address, or store ID")] = None,
) -> dict[str, Any]:
    """Get a lightweight list of all locations — just id, name, city, state, and storeId.

    PREFER THIS over get_all_locations when you only need to identify locations or
    show a summary list. Much smaller response, much faster.
    """
    client = _get_client()
    if search:
        raw = await asyncio.to_thread(client.search_locations, query=search, fetch_all=True)
    else:
        raw = await asyncio.to_thread(client.fetch_all_locations, fetch_all=True)
    locations = raw if isinstance(raw, list) else raw.get("locations", [])
    slim = [
        {
            "id": loc.get("id"),
            "name": loc.get("name"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "storeId": loc.get("storeId"),
            "phone": loc.get("phone"),
        }
        for loc in locations
    ]
    return {"success": True, "locations": slim, "total": len(slim)}


@mcp.tool()
async def get_account_review_summary(
    location_ids: Annotated[Optional[list[str]], Field(default=None, description="Specific location IDs to summarize. If omitted, all locations in the account are included.")] = None,
    start_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get aggregated review stats rolled up across all (or specified) locations.

    USE THIS instead of calling get_review_analytics_overview in a loop.
    Returns total review count, average rating, and response rate in a single call.
    Also lists which locations have reviews so you can drill in if needed.
    """
    client = _get_client()

    if location_ids is None:
        raw = await asyncio.to_thread(client.fetch_all_locations, fetch_all=True)
        locs = raw if isinstance(raw, list) else raw.get("locations", [])
        location_ids = [loc["id"] for loc in locs]

    total_reviews = 0
    ratings: list[float] = []
    response_rates: list[float] = []
    locations_with_reviews: list[dict[str, Any]] = []

    for loc_id in location_ids:
        try:
            result = await asyncio.to_thread(
                client.fetch_review_analytics_overview,
                location_id=loc_id,
                start_date=start_date,
                end_date=end_date,
            )
            stats = {s["name"]: s["value"] for s in result.get("stats", [])}
            count = stats.get("total-reviews", 0)
            rating = stats.get("overall-rating", 0)
            response_rate = stats.get("review-response-rate", 0)
            total_reviews += count
            if count > 0:
                ratings.append(rating)
                response_rates.append(response_rate)
                locations_with_reviews.append({
                    "location_id": loc_id,
                    "total_reviews": count,
                    "rating": rating,
                    "response_rate": response_rate,
                })
        except Exception:
            pass

    return {
        "success": True,
        "total_reviews": total_reviews,
        "locations_checked": len(location_ids),
        "locations_with_reviews": len(locations_with_reviews),
        "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "average_response_rate": round(sum(response_rates) / len(response_rates), 2) if response_rates else 0,
        "breakdown": locations_with_reviews,
    }


# ---------------------------------------------------------------------------
# Folder management tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_folder(
    name: Annotated[str, Field(description="Name for the new folder")],
    parent_folder: Annotated[Optional[str], Field(default=None, description="Parent folder UUID (to nest this folder under another)")] = None,
    parent_folder_name: Annotated[Optional[str], Field(default=None, description="Parent folder name (alternative to parent_folder UUID)")] = None,
) -> dict[str, Any]:
    """Create a folder to organize locations.

    Folders can be nested by providing a parent folder. Returns the created folder.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_folder,
        name=name,
        parent_folder=parent_folder,
        parent_folder_name=parent_folder_name,
    )


@mcp.tool()
async def rename_folder(
    old_name: Annotated[str, Field(description="Current folder name")],
    new_name: Annotated[str, Field(description="New name for the folder")],
) -> dict[str, Any]:
    """Rename an existing folder."""
    client = _get_client()
    return await asyncio.to_thread(client.rename_folder, old_name=old_name, new_name=new_name)


@mcp.tool()
async def delete_folder(
    name: Annotated[str, Field(description="Exact folder name to delete")],
) -> dict[str, Any]:
    """Delete a folder by name.

    Locations in the folder are NOT deleted — they are unassigned from the folder.
    """
    client = _get_client()
    return await asyncio.to_thread(client.delete_folder, name=name)


@mcp.tool()
async def add_locations_to_folder(
    folder_name: Annotated[str, Field(description="Folder name (created automatically if it does not exist)")],
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to add to the folder")],
) -> dict[str, Any]:
    """Add locations to a folder.

    The folder is created if it does not already exist.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.add_locations_to_folder,
        folder_name=folder_name,
        location_ids=location_ids,
    )


@mcp.tool()
async def remove_locations_from_folder(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to remove from their current folder")],
) -> dict[str, Any]:
    """Remove locations from their current folder."""
    client = _get_client()
    return await asyncio.to_thread(client.remove_locations_from_folder, location_ids)


# ---------------------------------------------------------------------------
# Tag management tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def add_location_tag(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    tag: Annotated[str, Field(description="Tag name to add (e.g. 'vip', 'new', 'franchise')")],
) -> dict[str, Any]:
    """Add a tag to a location.

    The tag is created automatically if it does not already exist.
    """
    client = _get_client()
    return await asyncio.to_thread(client.add_location_tag, location_id=location_id, tag=tag)


@mcp.tool()
async def remove_location_tag(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    tag: Annotated[str, Field(description="Tag name to remove")],
) -> dict[str, Any]:
    """Remove a tag from a location."""
    client = _get_client()
    return await asyncio.to_thread(client.remove_location_tag, location_id=location_id, tag=tag)


# ---------------------------------------------------------------------------
# Listings tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_premium_listings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get premium (directory) listings for a location.

    Returns listings from sites like Google Business Profile, Yelp, Bing Places, etc.
    Each listing includes site name, sync status, display status, and listing URL.
    """
    client = _get_client()
    listings = await asyncio.to_thread(client.fetch_premium_listings, location_id)
    return {"success": True, "listings": listings, "total": len(listings)}


@mcp.tool()
async def get_voice_listings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get voice assistant listings for a location.

    Returns listings for voice platforms like Google Assistant, Amazon Alexa, and Apple Siri.
    """
    client = _get_client()
    listings = await asyncio.to_thread(client.fetch_voice_listings, location_id)
    return {"success": True, "listings": listings, "total": len(listings)}


# ---------------------------------------------------------------------------
# Reviews & Interactions tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_interactions(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    first: Annotated[Optional[int], Field(default=None, description="Number of interactions to return")] = None,
    site_urls: Annotated[Optional[list[str]], Field(default=None, description="Filter by site URLs (e.g. ['maps.google.com', 'yelp.com'])")] = None,
    start_date: Annotated[Optional[str], Field(default=None, description="Start date filter in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date filter in YYYY-MM-DD format")] = None,
    category: Annotated[Optional[str], Field(default=None, description="Filter by category: 'Review' or 'Social'")] = None,
    rating_filters: Annotated[Optional[list[int]], Field(default=None, description="Filter by star ratings (e.g. [4, 5] for 4 and 5 star reviews)")] = None,
    fetch_all: Annotated[bool, Field(default=False, description="If true, return all interactions across all pages")] = False,
) -> dict[str, Any]:
    """Get reviews and social interactions for a location.

    Defaults to the last 30 days if no date range is provided.
    Returns reviews with content, rating, site, reviewer name, response status, and more.
    """
    client = _get_client()
    result = await asyncio.to_thread(
        client.fetch_interactions,
        location_id=location_id,
        first=first,
        site_urls=site_urls,
        start_date=start_date,
        end_date=end_date,
        category=category,
        rating_filters=rating_filters,
        fetch_all=fetch_all,
    )
    if isinstance(result, list):
        return {"success": True, "interactions": result, "total": len(result)}
    return result


@mcp.tool()
async def respond_to_review(
    interaction_id: Annotated[str, Field(description="UUID of the interaction (review) to respond to")],
    response_content: Annotated[str, Field(description="Text of your reply (shown publicly where applicable)")],
) -> dict[str, Any]:
    """Post a reply to a review or interaction.

    Get the interaction_id from get_interactions. The response is published publicly
    on the review platform where applicable.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.respond_to_review,
        interaction_id=interaction_id,
        response_content=response_content,
    )


@mcp.tool()
async def edit_review_response(
    review_id: Annotated[str, Field(description="ID of the review (interaction)")],
    response_id: Annotated[str, Field(description="ID of the existing response to edit")],
    response_content: Annotated[str, Field(description="New reply text to replace the current response")],
) -> dict[str, Any]:
    """Edit an existing reply to a review.

    Both the review ID and response ID are required. Get these from get_interactions.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.edit_review_response,
        review_id=review_id,
        response_id=response_id,
        response_content=response_content,
    )


@mcp.tool()
async def archive_review_response(
    response_id: Annotated[str, Field(description="ID of the response to archive/hide")],
) -> dict[str, Any]:
    """Archive (hide) an existing reply to a review.

    The response is hidden but not permanently deleted.
    """
    client = _get_client()
    return await asyncio.to_thread(client.archive_review_response, response_id=response_id)


# ---------------------------------------------------------------------------
# Review analytics tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_review_analytics_overview(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    start_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get overall review analytics for a location.

    Returns aggregate stats: total reviews, average rating, response rate, and more.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_review_analytics_overview,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
async def get_review_analytics_timeline(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    start_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get review analytics over time for a location.

    Returns review count and rating by time period — useful for trend analysis.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_review_analytics_timeline,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
async def get_review_analytics_sites_stats(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    start_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get review analytics broken down by site (Google, Yelp, etc.) for a location.

    Returns per-site review counts, average ratings, and response rates.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_review_analytics_sites_stats,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
async def get_review_campaigns(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    start_date: Annotated[Optional[str], Field(default=None, description="Filter campaigns starting from this date (YYYY-MM-DD)")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="Filter campaigns ending before this date (YYYY-MM-DD)")] = None,
) -> dict[str, Any]:
    """Get review campaigns for a location.

    Returns a list of review request campaigns with their status and metrics.
    """
    client = _get_client()
    campaigns = await asyncio.to_thread(
        client.fetch_review_campaigns,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
    )
    return {"success": True, "campaigns": campaigns, "total": len(campaigns)}


@mcp.tool()
async def create_review_campaign(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    name: Annotated[str, Field(description="Campaign name")],
    customers: Annotated[list[dict[str, Any]], Field(description="List of customer dicts with 'name' (required) and optional 'email' and 'phone'. Example: [{'name': 'John', 'email': 'john@example.com'}]")],
    screening: Annotated[Optional[bool], Field(default=None, description="Enable review screening (filters negative reviews before they go public)")] = None,
) -> dict[str, Any]:
    """Create a review campaign to request reviews from customers.

    Sends review requests to the provided customer list. Returns the created campaign.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_review_campaign,
        location_id=location_id,
        name=name,
        location_customers=customers,
        screening=screening,
    )


# ---------------------------------------------------------------------------
# Keywords & Rankings tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_keywords(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get all keywords tracked for a location's ranking performance.

    Returns the list of keywords being monitored, with their IDs and names.
    """
    client = _get_client()
    keywords = await asyncio.to_thread(client.fetch_keywords, location_id)
    return {"success": True, "keywords": keywords, "total": len(keywords)}


@mcp.tool()
async def get_keywords_performance(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    from_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    to_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get ranking performance data for a location's keywords.

    Returns keyword positions and trends over the specified date range.
    """
    client = _get_client()
    performance = await asyncio.to_thread(
        client.fetch_keywords_performance,
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
    )
    return {"success": True, "performance": performance, "total": len(performance)}


@mcp.tool()
async def add_keywords(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    keywords: Annotated[list[str], Field(description="List of keywords to track (e.g. ['plumber near me', 'emergency plumber'])")],
) -> dict[str, Any]:
    """Add keywords to a location for ranking tracking.

    Returns the created keyword objects with their IDs.
    """
    client = _get_client()
    created = await asyncio.to_thread(client.add_keywords, location_id=location_id, keywords=keywords)
    return {"success": True, "keywords": created, "total": len(created)}


@mcp.tool()
async def archive_keyword(
    keyword_id: Annotated[str, Field(description="Base64-encoded keyword ID (from get_keywords or add_keywords)")],
) -> dict[str, Any]:
    """Archive a keyword so it is no longer tracked.

    Get the keyword_id from get_keywords or add_keywords.
    """
    client = _get_client()
    return await asyncio.to_thread(client.archive_keyword, keyword_id=keyword_id)


@mcp.tool()
async def get_ranking_analytics_timeline(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs")],
    from_date: Annotated[str, Field(description="Start date in YYYY-MM-DD format")],
    to_date: Annotated[str, Field(description="End date in YYYY-MM-DD format")],
    source: Annotated[list[str], Field(description="List of ranking sources (e.g. ['Google', 'Bing'])")],
) -> dict[str, Any]:
    """Get keyword ranking positions over time for one or more locations.

    Returns timeline data showing how positions have changed across the date range.
    """
    client = _get_client()
    timeline = await asyncio.to_thread(
        client.fetch_ranking_analytics_timeline,
        location_ids=location_ids,
        from_date=from_date,
        to_date=to_date,
        source=source,
    )
    return {"success": True, "timeline": timeline}


@mcp.tool()
async def get_ranking_sitewise_histogram(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs")],
    from_date: Annotated[str, Field(description="Start date in YYYY-MM-DD format")],
    to_date: Annotated[str, Field(description="End date in YYYY-MM-DD format")],
    source: Annotated[list[str], Field(description="List of ranking sources (e.g. ['Google'])")],
) -> dict[str, Any]:
    """Get a histogram of keyword rankings by position bucket (e.g. top 3, 4-10, 11-20).

    Useful for understanding the distribution of keyword ranking positions.
    """
    client = _get_client()
    histogram = await asyncio.to_thread(
        client.fetch_ranking_sitewise_histogram,
        location_ids=location_ids,
        from_date=from_date,
        to_date=to_date,
        source=source,
    )
    return {"success": True, "histogram": histogram}


# ---------------------------------------------------------------------------
# Analytics tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_google_analytics(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    from_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    to_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get Google Business Profile analytics for a location.

    Returns Google insights: searches, views, calls, direction requests, website clicks, etc.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_google_analytics,
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
    )


@mcp.tool()
async def get_bing_analytics(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    from_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    to_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get Bing Places analytics for a location.

    Returns Bing insights: views, clicks, and actions on the Bing listing.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_bing_analytics,
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
    )


@mcp.tool()
async def get_facebook_analytics(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    from_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    to_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> dict[str, Any]:
    """Get Facebook page analytics for a location.

    Returns Facebook insights: reach, impressions, page views, and engagement.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_facebook_analytics,
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
    )


# ---------------------------------------------------------------------------
# Connected accounts tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def connect_google_account(
    success_url: Annotated[str, Field(description="Your app URL where users are redirected after successful connection")],
    error_url: Annotated[str, Field(description="Your app URL where users are redirected if connection fails")],
) -> dict[str, Any]:
    """Get a URL to connect a Google account for bulk location management.

    The returned URL is valid for 24 hours. Redirect your user to it to start the OAuth flow.
    After connecting, use trigger_connected_account_matches to link Google locations to Synup locations.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.connect_google_account,
        success_url=success_url,
        error_url=error_url,
    )


@mcp.tool()
async def connect_facebook_account(
    success_url: Annotated[str, Field(description="Your app URL where users are redirected after successful connection")],
    error_url: Annotated[str, Field(description="Your app URL where users are redirected if connection fails")],
) -> dict[str, Any]:
    """Get a URL to connect a Facebook account for bulk location management.

    The returned URL is valid for 24 hours. Redirect your user to it to start the OAuth flow.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.connect_facebook_account,
        success_url=success_url,
        error_url=error_url,
    )


@mcp.tool()
async def disconnect_google_account(
    connected_account_id: Annotated[str, Field(description="ID of the Google connected account to disconnect")],
) -> dict[str, Any]:
    """Disconnect a Google connected account from bulk location management."""
    client = _get_client()
    return await asyncio.to_thread(
        client.disconnect_google_account,
        connected_account_id=connected_account_id,
    )


@mcp.tool()
async def disconnect_facebook_account(
    connected_account_id: Annotated[str, Field(description="ID of the Facebook connected account to disconnect")],
) -> dict[str, Any]:
    """Disconnect a Facebook connected account from bulk location management."""
    client = _get_client()
    return await asyncio.to_thread(
        client.disconnect_facebook_account,
        connected_account_id=connected_account_id,
    )


@mcp.tool()
async def get_connected_account_listings(
    connected_account_id: Annotated[str, Field(description="ID of the connected Google or Facebook account")],
    location_info: Annotated[Optional[str], Field(default=None, description="Optional filter: substring to match in street, city, phone, or business name")] = None,
    page: Annotated[Optional[int], Field(default=None, description="Page number for pagination")] = None,
    per_page: Annotated[Optional[int], Field(default=None, description="Items per page (max 500)")] = None,
) -> dict[str, Any]:
    """Get listings (locations) accessible through a connected Google or Facebook account.

    Use this to see which Google/Facebook locations can be linked to Synup locations.
    After reviewing, use confirm_connected_account_matches to link them.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_connected_account_listings,
        connected_account_id=connected_account_id,
        location_info=location_info,
        page=page,
        per_page=per_page,
    )


@mcp.tool()
async def trigger_connected_account_matches(
    connected_account_ids: Annotated[list[str], Field(description="List of connected account IDs to run matching for")],
) -> dict[str, Any]:
    """Trigger matching of Google/Facebook profile locations to Synup locations.

    Synup will attempt to automatically match connected account listings to Synup locations.
    After triggering, use get_connected_account_listings to review and confirm matches.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.trigger_connected_account_matches,
        connected_account_ids=connected_account_ids,
    )


@mcp.tool()
async def confirm_connected_account_matches(
    match_record_ids: Annotated[list[str], Field(description="List of base64-encoded match record IDs to confirm")],
) -> dict[str, Any]:
    """Confirm suggested matches between connected account listings and Synup locations.

    Get match_record_ids from get_connected_account_listings. Confirming a match
    links the Google/Facebook listing to the corresponding Synup location.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.confirm_connected_account_matches,
        match_record_ids=match_record_ids,
    )


@mcp.tool()
async def connect_listing(
    location_id: Annotated[str, Field(description="Synup location ID (numeric or base64-encoded)")],
    connected_account_listing_id: Annotated[str, Field(description="Listing ID from get_connected_account_listings (records[].id)")],
    connected_account_id: Annotated[str, Field(description="Connected account ID")],
) -> dict[str, Any]:
    """Link a Synup location to a listing from a connected Google or Facebook account.

    Use IDs from get_connected_account_listings to link a specific listing to a Synup location.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.connect_listing,
        location_id=location_id,
        connected_account_listing_id=connected_account_listing_id,
        connected_account_id=connected_account_id,
    )


@mcp.tool()
async def disconnect_listing(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    site: Annotated[str, Field(description="Platform to disconnect: 'GOOGLE' or 'FACEBOOK'")],
) -> dict[str, Any]:
    """Unlink a location from its Google or Facebook listing."""
    client = _get_client()
    return await asyncio.to_thread(
        client.disconnect_listing,
        location_id=location_id,
        site=site,
    )


@mcp.tool()
async def create_gmb_listing(
    location_id: Annotated[str, Field(description="Synup location ID (numeric or base64-encoded)")],
    connected_account_id: Annotated[str, Field(description="Google connected account ID")],
    folder_id: Annotated[Optional[str], Field(default=None, description="Optional GMB folder/group ID")] = None,
) -> dict[str, Any]:
    """Create a Google Business Profile listing for an existing Synup location.

    This process is asynchronous — creation may complete in the background after the call returns.
    Check success in the response and monitor for completion.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_gmb_listing,
        location_id=location_id,
        connected_account_id=connected_account_id,
        folder_id=folder_id,
    )


# ---------------------------------------------------------------------------
# Review settings tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_review_settings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get review source settings for a location (which sites/URLs are configured).

    Returns the configured review sites and URLs used for collecting reviews.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_review_settings, location_id)


@mcp.tool()
async def edit_review_settings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    site_urls: Annotated[list[dict[str, Any]], Field(description="List of dicts with 'name' and 'url' (e.g. [{'name': 'trulia.com', 'url': 'https://trulia.com/biz/...'}])")],
) -> dict[str, Any]:
    """Set or update review source URLs for a location.

    Each item is a dict with site name and URL. Updates the review sources configuration.
    """
    client = _get_client()
    return await asyncio.to_thread(client.edit_review_settings, location_id, site_urls)


# ---------------------------------------------------------------------------
# Location photos tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_location_photos(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get photos and media attached to a location.

    Returns a list of photos with their IDs, URLs, type (LOGO, COVER, ADDITIONAL), and starred status.
    """
    client = _get_client()
    photos = await asyncio.to_thread(client.fetch_location_photos, location_id)
    return {"success": True, "photos": photos, "total": len(photos)}


@mcp.tool()
async def add_location_photos(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    photos: Annotated[list[dict[str, Any]], Field(description="List of photo dicts with 'photo' (URL) and 'type' (LOGO, COVER, or ADDITIONAL). Example: [{'photo': 'https://example.com/logo.png', 'type': 'LOGO'}]")],
) -> dict[str, Any]:
    """Add one or more photos to a location.

    Each photo needs a URL and type (LOGO, COVER, or ADDITIONAL).
    """
    client = _get_client()
    return await asyncio.to_thread(client.add_location_photos, location_id, photos)


@mcp.tool()
async def remove_location_photos(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    photo_ids: Annotated[list[str], Field(description="List of base64-encoded photo IDs to remove (only ADDITIONAL photos can be removed)")],
) -> dict[str, Any]:
    """Remove photos from a location. Only ADDITIONAL photos can be removed.

    Get photo IDs from get_location_photos.
    """
    client = _get_client()
    return await asyncio.to_thread(client.remove_location_photos, location_id, photo_ids)


@mcp.tool()
async def star_location_photos(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    media_ids: Annotated[list[str], Field(description="List of media IDs to star or unstar")],
    starred: Annotated[bool, Field(description="True to star, False to unstar")],
) -> dict[str, Any]:
    """Star or unstar photos for a location. Account can have at most 4 starred photos.

    Get media IDs from get_location_photos.
    """
    client = _get_client()
    return await asyncio.to_thread(client.star_location_photos, location_id, media_ids, starred)


# ---------------------------------------------------------------------------
# Connection info & account config tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_connection_info(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get OAuth connection status (Google/Facebook) for a location.

    Returns which platforms are connected and their connection details.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_connection_info, location_id)


@mcp.tool()
async def get_plan_sites() -> dict[str, Any]:
    """Get supported directories and site details for your account plan.

    Returns a list of all sites/directories available in your subscription.
    """
    client = _get_client()
    sites = await asyncio.to_thread(client.fetch_plan_sites)
    return {"success": True, "sites": sites, "total": len(sites)}


@mcp.tool()
async def get_countries() -> dict[str, Any]:
    """Get supported countries and states (ISO codes) for the account.

    Returns all available countries and their states/regions with ISO codes.
    """
    client = _get_client()
    countries = await asyncio.to_thread(client.fetch_countries)
    return {"success": True, "countries": countries, "total": len(countries)}


@mcp.tool()
async def get_review_site_config() -> dict[str, Any]:
    """Get eligible review sources and site config for the account.

    Returns the list of review sites that can be configured for your locations.
    """
    client = _get_client()
    config = await asyncio.to_thread(client.fetch_review_site_config)
    return {"success": True, "config": config, "total": len(config)}


# ---------------------------------------------------------------------------
# Location archival tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def cancel_archive_locations(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to cancel archival for")],
    selection_type: Annotated[str, Field(description="'ALL_ITEMS' or 'SELECTED_ITEMS'")],
    changed_by: Annotated[str, Field(description="Identifier of who is performing the action (e.g. user email)")],
) -> dict[str, Any]:
    """Cancel a scheduled archival for one or more locations.

    Use this to prevent locations from being archived if archival was previously scheduled.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.cancel_archive_locations,
        location_ids=location_ids,
        selection_type=selection_type,
        changed_by=changed_by,
    )


# ---------------------------------------------------------------------------
# Listings duplicate management tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def mark_listings_as_duplicate(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    listing_item_ids: Annotated[list[str], Field(description="List of base64-encoded listing item IDs to mark as duplicate")],
) -> dict[str, Any]:
    """Mark one or more listing items as duplicate for a location.

    Get listing item IDs from get_premium_listings or get_voice_listings.
    """
    client = _get_client()
    return await asyncio.to_thread(client.mark_listings_as_duplicate, location_id, listing_item_ids)


@mcp.tool()
async def mark_listings_as_not_duplicate(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    listing_item_ids: Annotated[list[str], Field(description="List of base64-encoded listing item IDs to clear duplicate status for")],
) -> dict[str, Any]:
    """Clear duplicate status for listing items on a location.

    Use this to undo mark_listings_as_duplicate.
    """
    client = _get_client()
    return await asyncio.to_thread(client.mark_listings_as_not_duplicate, location_id, listing_item_ids)


# ---------------------------------------------------------------------------
# Review campaign customer tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def add_review_campaign_customers(
    review_campaign_id: Annotated[str, Field(description="UUID of the review campaign")],
    customers: Annotated[list[dict[str, Any]], Field(description="List of customer dicts with 'name' (required), optional 'email' and 'phone'. Example: [{'name': 'Jane', 'email': 'jane@example.com'}]")],
) -> dict[str, Any]:
    """Add customers to an existing review campaign.

    Get the campaign ID from create_review_campaign or get_review_campaigns.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.add_review_campaign_customers,
        review_campaign_id=review_campaign_id,
        location_customers=customers,
    )


# ---------------------------------------------------------------------------
# User management tools (create, update, assign)
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_user(
    email: Annotated[str, Field(description="User's email address")],
    role_id: Annotated[str, Field(description="Base64-encoded role ID (from your account's roles)")],
    first_name: Annotated[str, Field(description="User's first name")],
    last_name: Annotated[Optional[str], Field(default=None, description="User's last name")] = None,
    direct_customer: Annotated[Optional[bool], Field(default=None, description="Whether user is a direct customer")] = None,
) -> dict[str, Any]:
    """Create a new user in the account with the given role.

    Returns the created user object with id, email, name, and role.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_user,
        email=email,
        role_id=role_id,
        first_name=first_name,
        last_name=last_name,
        direct_customer=direct_customer,
    )


@mcp.tool()
async def update_user(
    user_id: Annotated[str, Field(description="Base64-encoded user ID to update")],
    email: Annotated[Optional[str], Field(default=None, description="New email address")] = None,
    role_id: Annotated[Optional[str], Field(default=None, description="New role ID")] = None,
    first_name: Annotated[Optional[str], Field(default=None, description="New first name")] = None,
    last_name: Annotated[Optional[str], Field(default=None, description="New last name")] = None,
    phone: Annotated[Optional[str], Field(default=None, description="New phone number")] = None,
    archived: Annotated[Optional[bool], Field(default=None, description="True to archive, False to activate")] = None,
    direct_customer: Annotated[Optional[bool], Field(default=None, description="Whether user is a direct customer")] = None,
) -> dict[str, Any]:
    """Update a user's information. Only pass fields you want to change.

    Returns the updated user object.
    """
    client = _get_client()
    kwargs: dict[str, Any] = {"user_id": user_id}
    if email is not None:
        kwargs["email"] = email
    if role_id is not None:
        kwargs["role_id"] = role_id
    if first_name is not None:
        kwargs["first_name"] = first_name
    if last_name is not None:
        kwargs["last_name"] = last_name
    if phone is not None:
        kwargs["phone"] = phone
    if archived is not None:
        kwargs["archived"] = archived
    if direct_customer is not None:
        kwargs["direct_customer"] = direct_customer
    return await asyncio.to_thread(lambda: client.update_user(**kwargs))


@mcp.tool()
async def add_user_locations(
    user_id: Annotated[str, Field(description="Base64-encoded user ID")],
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to assign to the user")],
) -> dict[str, Any]:
    """Assign locations to a user so they can manage them.

    Get user IDs from list_users and location IDs from list_locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.add_user_locations, user_id, location_ids)


@mcp.tool()
async def remove_user_locations(
    user_id: Annotated[str, Field(description="Base64-encoded user ID")],
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to remove from the user")],
) -> dict[str, Any]:
    """Remove location assignments from a user.

    The user will no longer be able to manage the specified locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.remove_user_locations, user_id, location_ids)


@mcp.tool()
async def add_user_folders(
    user_id: Annotated[str, Field(description="Base64-encoded user ID")],
    folder_ids: Annotated[list[str], Field(description="List of folder UUIDs to assign to the user")],
) -> dict[str, Any]:
    """Assign folders to a user so they can manage locations in those folders.

    Get user IDs from list_users.
    """
    client = _get_client()
    return await asyncio.to_thread(client.add_user_folders, user_id, folder_ids)


@mcp.tool()
async def remove_user_folders(
    user_id: Annotated[str, Field(description="Base64-encoded user ID")],
    folder_ids: Annotated[list[str], Field(description="List of folder UUIDs to remove from the user")],
) -> dict[str, Any]:
    """Remove folder assignments from a user.

    The user will no longer have access to the specified folders.
    """
    client = _get_client()
    return await asyncio.to_thread(client.remove_user_folders, user_id, folder_ids)


@mcp.tool()
async def add_user_and_folder(
    role_id: Annotated[str, Field(description="Base64-encoded role ID for the new user")],
    first_name: Annotated[str, Field(description="User's first name")],
    email: Annotated[str, Field(description="User's email address")],
    folder_name: Annotated[str, Field(description="Name for the new folder")],
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to add to the folder")],
    last_name: Annotated[Optional[str], Field(default=None, description="User's last name")] = None,
) -> dict[str, Any]:
    """Create a user and a folder, then assign the folder to the user — all in one call.

    Convenience tool for onboarding: creates user, creates folder, assigns locations to folder,
    and assigns folder to user in a single operation.
    """
    client = _get_client()
    input_data: dict[str, Any] = {
        "roleId": role_id,
        "firstName": first_name,
        "email": email,
        "name": folder_name,
        "locationIds": location_ids,
    }
    if last_name is not None:
        input_data["lastName"] = last_name
    return await asyncio.to_thread(client.add_user_and_folder, input_data)


# ---------------------------------------------------------------------------
# Automation tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_temporary_close_automation(
    name: Annotated[str, Field(description="Name for the automation")],
    start_date: Annotated[str, Field(description="Close date in YYYY-MM-DD format")],
    start_time: Annotated[str, Field(description="Close time (e.g. '10:00:00')")],
    end_date: Annotated[str, Field(description="Reopen date in YYYY-MM-DD format")],
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Create an automation that temporarily closes a location and reopens on a set date.

    Works with Google and Facebook listings. The location will be marked as
    temporarily closed on start_date and reopened on end_date.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_temporary_close_automation,
        name=name,
        start_date=start_date,
        start_time=start_time,
        end_date=end_date,
        location_id=location_id,
    )


# ---------------------------------------------------------------------------
# OAuth profile connect tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_oauth_connect_url(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    site: Annotated[str, Field(description="Platform to connect: 'GOOGLE' or 'FACEBOOK'")],
    success_url: Annotated[str, Field(description="Your app URL where users are redirected after successful connection")],
    error_url: Annotated[str, Field(description="Your app URL where users are redirected if connection fails")],
) -> dict[str, Any]:
    """Get a URL to connect a Google or Facebook profile to a specific location.

    The returned URL is valid for 24 hours. Redirect your user to it to start the OAuth flow.
    This connects a single location (vs connect_google_account which connects an account for bulk use).
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.get_oauth_connect_url,
        location_id=location_id,
        site=site,
        success_url=success_url,
        error_url=error_url,
    )


@mcp.tool()
async def oauth_disconnect(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    site: Annotated[str, Field(description="Platform to disconnect: 'GOOGLE' or 'FACEBOOK'")],
) -> dict[str, Any]:
    """Disconnect a Google or Facebook profile from a specific location.

    This disconnects a single location (vs disconnect_google_account which disconnects the whole account).
    """
    client = _get_client()
    return await asyncio.to_thread(client.oauth_disconnect, location_id, site)


# ---------------------------------------------------------------------------
# Grid report (Local Rank) tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_grid_report(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    keywords: Annotated[list[str], Field(description="List of keywords to rank (max 25)")],
    business_name: Annotated[str, Field(description="Business name")],
    business_street: Annotated[str, Field(description="Business street address")],
    business_city: Annotated[str, Field(description="Business city")],
    business_state: Annotated[str, Field(description="Business state/region")],
    business_country: Annotated[str, Field(description="Business country")],
    latitude: Annotated[float, Field(description="Center latitude of the grid (decimal degrees)")],
    longitude: Annotated[float, Field(description="Center longitude of the grid (decimal degrees)")],
    distance: Annotated[int, Field(description="Grid radius (number of miles or km)")],
    distance_unit: Annotated[str, Field(description="Distance unit: 'mi' or 'km'")],
    grid_size: Annotated[int, Field(description="Grid dimension: 3, 5, or 7")],
) -> dict[str, Any]:
    """Create a Local Rank Grid report showing ranking positions across a geographic grid.

    Generates a grid of search results around a center point to visualize local ranking
    performance across the area. Max 25 keywords per report.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.create_grid_report,
        location_id=location_id,
        keywords=keywords,
        business_name=business_name,
        business_street=business_street,
        business_city=business_city,
        business_state=business_state,
        business_country=business_country,
        latitude=latitude,
        longitude=longitude,
        distance=distance,
        distance_unit=distance_unit,
        grid_size=grid_size,
    )


@mcp.tool()
async def get_grid_report(
    report_id: Annotated[str, Field(description="Grid report UUID (from create_grid_report or get_location_grid_reports)")],
) -> dict[str, Any]:
    """Get a Local Rank Grid report by its ID.

    Returns the full report data including keyword positions at each grid point.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_grid_report, report_id)


@mcp.tool()
async def get_location_grid_reports(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
    search_string: Annotated[Optional[str], Field(default=None, description="Filter reports by keyword")] = None,
    grid_size: Annotated[Optional[int], Field(default=None, description="Filter by grid size (3, 5, or 7)")] = None,
    from_date: Annotated[Optional[str], Field(default=None, description="Start date filter in YYYY-MM-DD format")] = None,
    to_date: Annotated[Optional[str], Field(default=None, description="End date filter in YYYY-MM-DD format")] = None,
    sort_field: Annotated[Optional[str], Field(default=None, description="Field to sort by")] = None,
    sort_order: Annotated[Optional[str], Field(default=None, description="Sort order: 'asc' or 'desc'")] = None,
    page_size: Annotated[Optional[int], Field(default=None, description="Number of reports per page")] = None,
    page: Annotated[Optional[int], Field(default=None, description="Page number")] = None,
) -> dict[str, Any]:
    """Get all Local Rank Grid reports for a location with optional filtering and pagination.

    Returns a list of grid reports with their IDs, dates, keywords, and grid sizes.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_location_grid_reports,
        location_id=location_id,
        search_string=search_string,
        grid_size=grid_size,
        from_date=from_date,
        to_date=to_date,
        sort_field=sort_field,
        sort_order=sort_order,
        page_size=page_size,
        page=page,
    )


# ---------------------------------------------------------------------------
# Photo Upload Status
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_photo_upload_status(
    request_id: Annotated[str, Field(description="Request ID returned from a bulk photo upload")],
) -> dict[str, Any]:
    """Check the processing status of a bulk photo upload request.

    Returns status, counts, and any errors for the upload batch.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_photo_upload_status, request_id)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_subscriptions() -> list[dict[str, Any]]:
    """Get all active subscription tenures for the account.

    Useful for accounts with multiple subscriptions — returns tenure names
    (e.g. 'Monthly', 'Half Yearly') that can be specified when creating locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_subscriptions)


# ---------------------------------------------------------------------------
# Folders (flat / tree / details)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_folders_flat() -> list[dict[str, Any]]:
    """List all folders in the account as a flat list.

    Returns folder id, name, parentFolderName, and locationCount for each folder.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_folders_flat)


@mcp.tool()
async def get_folders_tree() -> list[dict[str, Any]]:
    """List all folders in the account as a nested hierarchical tree.

    Returns folders with nested subFolders, showing the complete folder structure.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_folders_tree)


@mcp.tool()
async def get_folder_details(
    folder_id: Annotated[Optional[str], Field(default=None, description="Folder UUID. Provide this or folder_name.")] = None,
    folder_name: Annotated[Optional[str], Field(default=None, description="Folder name. Provide this or folder_id.")] = None,
) -> dict[str, Any]:
    """Get details for a specific folder by its ID or name.

    At least one of folder_id or folder_name must be provided.
    Returns folder details including locations, parent folder, and creation date.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_folder_details, folder_id=folder_id, folder_name=folder_name
    )


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_tags() -> list[dict[str, Any]]:
    """List all tags defined in the account.

    Returns tag id and name for each tag. Use these tag names with
    get_locations_by_tags to find tagged locations.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_tags)


# ---------------------------------------------------------------------------
# AI Listings
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_ai_listings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> dict[str, Any]:
    """Get AI-generated listing visibility data for a location.

    Returns AI visibility score, per-site accuracy scores (ChatGPT, Gemini,
    Perplexity, Copilot, etc.), business improvement tips, and live links.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_ai_listings, location_id)


# ---------------------------------------------------------------------------
# Additional & Duplicate Listings
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_additional_listings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> list[dict[str, Any]]:
    """Get additional (non-premium) listings for a location.

    Returns listing details including site, sync status, and live URLs.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_additional_listings, location_id)


@mcp.tool()
async def get_duplicate_listings(
    location_id: Annotated[str, Field(description="Location ID (numeric or base64-encoded)")],
) -> list[dict[str, Any]]:
    """Get duplicate listings detected for a specific location.

    Returns grouped duplicate listings by site, with details about each duplicate
    (name, address, phone validity, processing state, live link).
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_duplicate_listings, location_id)


@mcp.tool()
async def get_all_duplicate_listings(
    tag: Annotated[Optional[str], Field(default=None, description="Filter duplicates by tag name")] = None,
    page: Annotated[Optional[int], Field(default=None, description="Page number for pagination")] = None,
) -> dict[str, Any]:
    """Get a paginated rollup of all duplicate listings across the account.

    Returns duplicate records with page info. Optionally filter by tag name.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_all_duplicate_listings, tag=tag, page=page
    )


# ---------------------------------------------------------------------------
# Review Details & Phrases
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_review_details(
    interaction_ids: Annotated[list[str], Field(description="List of interaction (review) IDs to look up")],
) -> dict[str, Any]:
    """Get detailed information for specific reviews by their interaction IDs.

    Returns full review objects including content, rating, author, responses,
    and response status.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_review_details, interaction_ids)


@mcp.tool()
async def get_review_phrases(
    location_ids: Annotated[list[str], Field(description="List of base64-encoded location IDs to analyze")],
    site_urls: Annotated[Optional[list[str]], Field(default=None, description="Filter to specific review sites (e.g. ['maps.google.com', 'facebook.com'])")] = None,
    start_date: Annotated[Optional[str], Field(default=None, description="Start date in YYYY-MM-DD format")] = None,
    end_date: Annotated[Optional[str], Field(default=None, description="End date in YYYY-MM-DD format")] = None,
) -> list[dict[str, Any]]:
    """Get commonly mentioned review phrases/keywords for locations.

    Returns phrase text with stats (review count, average rating, delta).
    Useful for sentiment analysis and understanding customer feedback themes.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_review_phrases,
        location_ids=location_ids,
        site_urls=site_urls,
        start_date=start_date,
        end_date=end_date,
    )


# ---------------------------------------------------------------------------
# Review Campaign Customers
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_review_campaign_customers(
    review_campaign_id: Annotated[str, Field(description="Review campaign ID (UUID)")],
) -> dict[str, Any]:
    """List customers and their responses for a specific review campaign.

    Returns campaign name and customer details including name, email, phone,
    rating, response, delivery timestamps, and follow-up status.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_review_campaign_customers, review_campaign_id
    )


# ---------------------------------------------------------------------------
# Connected Accounts (list, folders, details, suggestions)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_connected_accounts(
    publisher: Annotated[Optional[str], Field(default=None, description="Filter by publisher type: 'FacebookAccount' or 'GoogleAccount'")] = None,
    status: Annotated[Optional[str], Field(default=None, description="Filter by status: 'Connected' or 'ConnectionIssue'")] = None,
    page: Annotated[Optional[int], Field(default=None, description="Page number (default 1)")] = None,
    per_page: Annotated[Optional[int], Field(default=None, description="Records per page (default 20)")] = None,
) -> dict[str, Any]:
    """List all connected third-party accounts (Google, Facebook) with optional filters.

    Returns paginated records with account type, email, connection status,
    connected locations count, and match request status.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_connected_accounts,
        publisher=publisher,
        status=status,
        page=page,
        per_page=per_page,
    )


@mcp.tool()
async def get_connected_account_folders(
    connected_account_id: Annotated[str, Field(description="Connected account ID (UUID)")],
    folder_name: Annotated[Optional[str], Field(default=None, description="Optional folder name filter")] = None,
) -> list[dict[str, Any]]:
    """List Google My Business folders (groups) under a connected Google account.

    Returns folder name, location count, and GMB folder ID for each folder.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_connected_account_folders,
        connected_account_id=connected_account_id,
        folder_name=folder_name,
    )


@mcp.tool()
async def get_connected_account_details(
    connected_account_id: Annotated[str, Field(description="Connected account ID (UUID)")],
) -> dict[str, Any]:
    """Get detailed information about a specific connected account.

    Returns account type, email, connection status, connected locations count,
    match request status, and connectivity issues.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_connected_account_details, connected_account_id
    )


@mcp.tool()
async def get_connection_suggestions(
    connected_account_id: Annotated[str, Field(description="Connected account ID (UUID)")],
    page: Annotated[Optional[int], Field(default=None, description="Page number (default 1)")] = None,
    per_page: Annotated[Optional[int], Field(default=None, description="Records per page (default 20)")] = None,
) -> dict[str, Any]:
    """Get suggested matches between a connected account's listings and Synup locations.

    Returns paginated suggestions with Synup location info and suggested
    GMB/Facebook profile info side-by-side for review.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.fetch_connection_suggestions,
        connected_account_id=connected_account_id,
        page=page,
        per_page=per_page,
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_roles() -> list[dict[str, Any]]:
    """List all user roles defined in the account.

    Returns role id, name, and timestamps. Use role IDs when creating or
    updating users.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_roles)


# ---------------------------------------------------------------------------
# User Resources & Lookup
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_user_resources(
    user_id: Annotated[str, Field(description="Base64-encoded user ID")],
) -> list[dict[str, Any]]:
    """List all resources (locations and folders) assigned to a specific user.

    Returns resources with their type (Folder or LocationSummary), id, and name.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_user_resources, user_id)


@mcp.tool()
async def get_users_by_ids(
    user_ids: Annotated[list[str], Field(description="List of base64-encoded user IDs")],
) -> list[dict[str, Any]]:
    """Get user details for specific user IDs.

    Returns user info including email, name, role, direct customer flag,
    creation date, and invite status.
    """
    client = _get_client()
    return await asyncio.to_thread(client.fetch_users_by_ids, user_ids)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Synup MCP server using stdio transport (default for Claude Desktop)."""
    mcp.run()


if __name__ == "__main__":
    main()
