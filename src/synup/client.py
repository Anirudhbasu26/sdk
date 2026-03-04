"""Synup SDK — developer toolkit for building applications on top of Synup backend services.

This SDK is designed for LLM-first consumption: simple method signatures, predictable naming,
self-describing responses, and minimal required parameters. Users bring their own LLM
(OpenAI, Anthropic, Gemini, Ollama, etc.) and use this client to call Synup APIs with
minimal friction.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import requests

from synup.exceptions import SynupAPIError

DEFAULT_BASE_URL = "https://api.synup.com"


def _encode_location_id(id_value: str | int) -> str:
    """Convert a numeric location ID to base64-encoded form, or return as-is if already encoded."""
    if isinstance(id_value, int):
        return base64.b64encode(f"Location:{id_value}".encode()).decode("ascii")
    s = str(id_value).strip()
    if s.isdigit():
        return base64.b64encode(f"Location:{s}".encode()).decode("ascii")
    return s


class SynupClient:
    """Client for the Synup v4 API. Create with an API key; all methods return structured data.

    Example:
        client = SynupClient(api_key="YOUR_API_KEY")
        locations = client.fetch_all_locations(first=10)
        if locations.get("success"):
            for loc in locations["locations"]:
                print(loc["name"])
    """

    def __init__(self, api_key: str, base_url: str | None = None):
        """Create a Synup API client. Setup is 2–3 lines: import, instantiate, call.

        Args:
            api_key: Your Synup API key (from Settings → Integrations → Generate in your workspace).
            base_url: Optional. API base URL; defaults to https://api.synup.com.
        """
        self._api_key = api_key
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"API {self._api_key}",
                "Content-Type": "application/json",
            }
        )

    def fetch_all_locations(
        self,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
        fetch_all: bool = False,
        page_size: int = 100,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Get locations for the account, with optional pagination or fetch-all.

        Args:
            first: How many locations to return from the start of the list.
            after: Pagination cursor — return locations after this cursor.
            before: Pagination cursor — return locations before this cursor.
            last: How many locations to return from the end of the list.
            fetch_all: If True, automatically follow pages and return one flat list of all locations.
            page_size: When using fetch_all, how many locations to request per API call (default 100).

        Returns:
            If fetch_all is False: dict with success, locations (list), page_info (has_next_page, end_cursor, etc.).
            If fetch_all is True: list of location dicts (id, name, city, storeId, etc.).

        Example:
            result = client.fetch_all_locations(first=10)
            if result.get("success"):
                for loc in result["locations"]:
                    print(loc["name"])
        """
        if fetch_all:
            return self._fetch_all_locations_paginated(page_size=page_size)
        return self._fetch_locations_page(first=first, after=after, before=before, last=last)

    def _fetch_locations_page(
        self,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> dict[str, Any]:
        """Perform a single GET to /api/v4/locations and return parsed result."""
        params: dict[str, str | int] = {}
        if first is not None:
            params["first"] = first
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if last is not None:
            params["last"] = last

        url = f"{self._base_url}/api/v4/locations"
        response = self._session.get(url, params=params)

        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )

        data = response.json()
        all_locations = data.get("data", {}).get("allLocations") or {}
        edges = all_locations.get("edges") or []
        page_info = all_locations.get("pageInfo") or {}

        locations = [edge["node"] for edge in edges]
        start_cursor = edges[0]["cursor"] if edges else None
        end_cursor = edges[-1]["cursor"] if edges else None

        return {
            "success": True,
            "locations": locations,
            "page_info": {
                "has_next_page": page_info.get("hasNextPage", False),
                "has_previous_page": page_info.get("hasPreviousPage", False),
                "start_cursor": start_cursor,
                "end_cursor": end_cursor,
            },
            "raw": data,
        }

    def _fetch_all_locations_paginated(self, page_size: int = 100) -> list[dict[str, Any]]:
        """Auto-paginate and return all location nodes."""
        all_nodes: list[dict[str, Any]] = []
        after: str | None = None

        while True:
            page = self._fetch_locations_page(first=page_size, after=after)
            nodes = page["locations"]
            all_nodes.extend(nodes)
            if not page["page_info"]["has_next_page"]:
                break
            after = page["page_info"]["end_cursor"]
            if not after:
                break

        return all_nodes

    def fetch_locations_by_ids(
        self, location_ids: list[str | int]
    ) -> list[dict[str, Any]]:
        """Get locations by a list of IDs. Accepts numeric or base64-encoded IDs.

        Args:
            location_ids: List of location IDs. Use numbers (e.g. 16808) or base64 strings;
                both are accepted and normalized automatically.

        Returns:
            List of location dicts (id, name, street, city, etc.). Empty list if none found.

        Example:
            locations = client.fetch_locations_by_ids([16808, 16749])
        """
        if not location_ids:
            return []
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        url = f"{self._base_url}/api/v4/locations-by-ids"
        params = {"ids": json.dumps(encoded_ids)}
        response = self._session.get(url, params=params)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        data = response.json()
        return data.get("data", {}).get("getLocationsByIds") or []

    def fetch_locations_by_store_codes(self, store_codes: list[str]) -> list[dict[str, Any]]:
        """Get locations that match the given store codes (e.g. STORE01, STORE02).

        Args:
            store_codes: List of store identifiers as used in your account.

        Returns:
            List of location dicts. Empty list if none match.

        Example:
            locations = client.fetch_locations_by_store_codes(["STORE01", "STORE02"])
        """
        if not store_codes:
            return []
        url = f"{self._base_url}/api/v4/locations-by-store-codes"
        params = {"storeCodes": json.dumps(store_codes)}
        response = self._session.get(url, params=params)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        data = response.json()
        return data.get("data", {}).get("getLocationsByStoreCodes") or []

    def search_locations(
        self,
        query: str,
        fields: list[str] | None = None,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
        fetch_all: bool = False,
        page_size: int = 100,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Search locations by keyword (name, address, or store ID).

        Args:
            query: Search term to match against location name, street, or store_id.
            fields: Optional. Restrict search to specific fields, e.g. ["name"] or ["store_id"]; if omitted, all are searched.
            first, after, before, last: Pagination; same semantics as fetch_all_locations.
            fetch_all: If True, return one flat list of all matching locations.
            page_size: When fetch_all is True, how many to fetch per request.

        Returns:
            If fetch_all is False: dict with success, locations, page_info.
            If fetch_all is True: list of location dicts.

        Example:
            result = client.search_locations("cafe", first=20)
            locations = result["locations"]
        """
        if fetch_all:
            return self._search_locations_paginated(query, fields=fields, page_size=page_size)
        return self._search_locations_page(
            query, fields=fields, first=first, after=after, before=before, last=last
        )

    def _search_locations_page(
        self,
        query: str,
        fields: list[str] | None = None,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/api/v4/locations/search"
        params: dict[str, str | int] = {"query": query}
        if fields is not None:
            params["fields"] = json.dumps(fields)
        if first is not None:
            params["first"] = first
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if last is not None:
            params["last"] = last
        response = self._session.get(url, params=params)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        data = response.json()
        search_result = data.get("data", {}).get("searchLocations") or {}
        edges = search_result.get("edges") or []
        page_info = search_result.get("pageInfo") or {}
        locations = [e["node"] for e in edges]
        start_cursor = edges[0]["cursor"] if edges else None
        end_cursor = edges[-1]["cursor"] if edges else None
        return {
            "success": True,
            "locations": locations,
            "page_info": {
                "has_next_page": page_info.get("hasNextPage", False),
                "has_previous_page": page_info.get("hasPreviousPage", False),
                "start_cursor": start_cursor,
                "end_cursor": end_cursor,
                "total": page_info.get("total"),
            },
            "raw": data,
        }

    def _search_locations_paginated(
        self,
        query: str,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        all_nodes: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            page = self._search_locations_page(
                query, fields=fields, first=page_size, after=after
            )
            all_nodes.extend(page["locations"])
            if not page["page_info"].get("has_next_page"):
                break
            after = page["page_info"].get("end_cursor")
            if not after:
                break
        return all_nodes

    def fetch_locations_by_folder(
        self,
        folder_id: str | None = None,
        folder_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all locations in a folder (including subfolders). Use folder_id or folder_name.

        Args:
            folder_id: Folder UUID from your account.
            folder_name: Human-readable folder name (e.g. "franchise"). Either this or folder_id is required.

        Returns:
            List of location dicts. Empty list if folder is empty or not found.

        Example:
            locations = client.fetch_locations_by_folder(folder_name="franchise")
        """
        if not folder_id and not folder_name:
            raise ValueError("Provide either folder_id or folder_name")
        url = f"{self._base_url}/api/v4/folder-locations"
        params: dict[str, str] = {}
        if folder_id:
            params["folderId"] = folder_id
        if folder_name:
            params["folderName"] = folder_name
        response = self._session.get(url, params=params)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        data = response.json()
        return data.get("data", {}).get("getLocationsForFolder") or []

    def fetch_locations_by_tags(
        self,
        tags: list[str],
        archived: bool | None = None,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
        fetch_all: bool = False,
        page_size: int = 100,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Get locations that have any of the given tags. Optional filter by archived status.

        Args:
            tags: List of tag names (e.g. ["recent", "vip"]). Locations with any of these tags are returned.
            archived: If True, only archived locations; if False, only active; if None, both.
            first, after, before, last: Pagination cursors and limits.
            fetch_all: If True, return one flat list of all matching locations.
            page_size: When fetch_all is True, page size per request.

        Returns:
            If fetch_all is False: dict with success, locations, page_info.
            If fetch_all is True: list of location dicts.

        Example:
            locations = client.fetch_locations_by_tags(["recent"], archived=False, fetch_all=True)
        """
        if not tags:
            return [] if fetch_all else {"success": True, "locations": [], "page_info": {}, "raw": {}}
        if fetch_all:
            return self._fetch_locations_by_tags_paginated(tags, archived=archived, page_size=page_size)
        return self._fetch_locations_by_tags_page(
            tags, archived=archived, first=first, after=after, before=before, last=last
        )

    def _fetch_locations_by_tags_page(
        self,
        tags: list[str],
        archived: bool | None = None,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/api/v4/tags/locations"
        params: dict[str, str | int] = {"tags": json.dumps(tags)}
        if archived is not None:
            params["archived"] = json.dumps(archived)
        if first is not None:
            params["first"] = first
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if last is not None:
            params["last"] = last
        response = self._session.get(url, params=params)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        data = response.json()
        tag_result = data.get("data", {}).get("searchLocationsByTag") or {}
        edges = tag_result.get("edges") or []
        page_info = tag_result.get("pageInfo") or {}
        locations = [e["node"] for e in edges]
        start_cursor = edges[0]["cursor"] if edges else None
        end_cursor = edges[-1]["cursor"] if edges else None
        return {
            "success": True,
            "locations": locations,
            "page_info": {
                "has_next_page": page_info.get("hasNextPage", False),
                "has_previous_page": page_info.get("hasPreviousPage", False),
                "start_cursor": start_cursor,
                "end_cursor": end_cursor,
                "total": page_info.get("total"),
            },
            "raw": data,
        }

    def _fetch_locations_by_tags_paginated(
        self,
        tags: list[str],
        archived: bool | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        all_nodes: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            page = self._fetch_locations_by_tags_page(
                tags, archived=archived, first=page_size, after=after
            )
            all_nodes.extend(page["locations"])
            if not page["page_info"].get("has_next_page"):
                break
            after = page["page_info"].get("end_cursor")
            if not after:
                break
        return all_nodes

    def _listings_get(
        self, location_id: str | int, path_suffix: str, params: dict | None = None
    ) -> dict[str, Any]:
        """GET a location-scoped endpoint and return parsed JSON."""
        encoded_id = _encode_location_id(location_id)
        url = f"{self._base_url}/api/v4/locations/{encoded_id}/{path_suffix}"
        response = self._session.get(url, params=params or {})
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        return response.json()

    def _api_get(self, path_suffix: str, params: dict | None = None) -> dict[str, Any]:
        """GET an account-level API path and return parsed JSON."""
        url = f"{self._base_url}/api/v4/{path_suffix}"
        response = self._session.get(url, params=params or {})
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        return response.json()

    def _api_post(self, path_suffix: str, json_body: dict[str, Any]) -> dict[str, Any]:
        """POST to an API path with JSON body and return parsed JSON."""
        url = f"{self._base_url}/api/v4/{path_suffix}"
        response = self._session.post(url, json=json_body)
        if not response.ok:
            raise SynupAPIError(
                message=f"API request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        return response.json()

    def fetch_premium_listings(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get premium (directory) listings for a location (Google, Yelp, etc.).

        Args:
            location_id: Location ID — numeric (e.g. 16808) or base64-encoded string.

        Returns:
            List of listing dicts with id, site, syncStatus, displayStatus, listingUrl, etc.

        Example:
            listings = client.fetch_premium_listings(16808)
        """
        data = self._listings_get(location_id, "listings/premium")
        return data.get("data", {}).get("listingsForLocation") or []

    def fetch_voice_listings(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get voice assistant listings for a location (Google, Alexa, Siri, etc.).

        Args:
            location_id: Location ID — numeric or base64-encoded.

        Returns:
            List of dicts with name, voiceIdentifier, syncStatus, etc.

        Example:
            voice_listings = client.fetch_voice_listings(16808)
        """
        data = self._listings_get(location_id, "voice-assistants")
        return data.get("data", {}).get("voiceAssistantsForLocation") or []

    # --- Interactions (reviews) ---

    def fetch_interactions(
        self,
        location_id: str | int,
        first: int | None = None,
        after: str | None = None,
        before: str | None = None,
        last: int | None = None,
        site_urls: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        category: str | None = None,
        rating_filters: list[int] | None = None,
        fetch_all: bool = False,
        page_size: int = 100,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Get reviews and social interactions for a location (default: last 30 days).

        Args:
            location_id: Location ID — numeric or base64-encoded.
            first, after, before, last: Cursor-based pagination.
            site_urls: Optional. Restrict to specific sites (e.g. maps.google.com, yelp.com).
            start_date, end_date: Optional. Date range in YYYY-MM-DD.
            category: Optional. "Review" or "Social".
            rating_filters: Optional. Star ratings to include (e.g. [4, 5]).
            fetch_all: If True, return one flat list of all interactions.
            page_size: When fetch_all is True, items per request.

        Returns:
            If fetch_all is False: dict with success, interactions, page_info, total_count.
            If fetch_all is True: list of interaction dicts.

        Example:
            result = client.fetch_interactions(16808, first=10, rating_filters=[4, 5])
            reviews = result["interactions"]
        """
        params: dict[str, Any] = {}
        if first is not None:
            params["first"] = first
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if last is not None:
            params["last"] = last
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        if category is not None:
            params["category"] = category
        if site_urls is not None:
            params["siteUrls"] = json.dumps(site_urls)
        if rating_filters is not None:
            params["ratingFilters"] = json.dumps(rating_filters)

        if fetch_all:
            all_nodes: list[dict[str, Any]] = []
            after_cursor: str | None = None
            while True:
                p = dict(params)
                p["first"] = page_size
                if after_cursor is not None:
                    p["after"] = after_cursor
                data = self._listings_get(location_id, "reviews", params=p)
                interactions_data = data.get("data", {}).get("interactions") or {}
                edges = interactions_data.get("edges") or []
                page_info = interactions_data.get("pageInfo") or {}
                all_nodes.extend(edge["node"] for edge in edges)
                if not page_info.get("hasNextPage") or not edges:
                    break
                after_cursor = edges[-1].get("cursor")
                if not after_cursor:
                    break
            return all_nodes

        data = self._listings_get(location_id, "reviews", params=params)
        interactions_data = data.get("data", {}).get("interactions") or {}
        edges = interactions_data.get("edges") or []
        page_info = interactions_data.get("pageInfo") or {}
        interactions_list = [edge["node"] for edge in edges]
        start_cursor = edges[0]["cursor"] if edges else None
        end_cursor = edges[-1]["cursor"] if edges else None
        return {
            "success": True,
            "interactions": interactions_list,
            "page_info": {
                "has_next_page": page_info.get("hasNextPage", False),
                "has_previous_page": page_info.get("hasPreviousPage", False),
                "start_cursor": start_cursor,
                "end_cursor": end_cursor,
            },
            "total_count": interactions_data.get("totalCount"),
            "raw": data,
        }

    def fetch_review_settings(self, location_id: str | int) -> dict[str, Any]:
        """Get review source settings for a location (which sites/URLs are configured).

        Args:
            location_id: Location ID — numeric or base64-encoded.

        Returns:
            Dict with site list and URLs used for reviews.

        Example:
            settings = client.fetch_review_settings(16808)
        """
        data = self._listings_get(location_id, "reviews/settings")
        return data.get("data", {}).get("interactionsSetting") or {}

    def fetch_review_analytics_overview(
        self,
        location_id: str | int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get overall review analytics for a location (totals, rating, response rate).

        Args:
            location_id: Location ID — numeric or base64-encoded.
            start_date, end_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with aggregate review stats.

        Example:
            overview = client.fetch_review_analytics_overview(16808, start_date="2024-01-01", end_date="2024-12-31")
        """
        params: dict[str, str] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        data = self._listings_get(location_id, "review-analytics-overview", params=params)
        return data.get("data", {}).get("interactionsAnalyticsStats") or {}

    def fetch_review_analytics_timeline(
        self,
        location_id: str | int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get review analytics over time (rating and count by period) for a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            start_date, end_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with timeline/chart data.

        Example:
            timeline = client.fetch_review_analytics_timeline(16808, start_date="2024-01-01", end_date="2024-06-30")
        """
        params: dict[str, str] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        data = self._listings_get(location_id, "review-analytics-timeline", params=params)
        return data.get("data", {}).get("interactionsChartData") or {}

    def fetch_review_analytics_sites_stats(
        self,
        location_id: str | int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get review analytics broken down by site (e.g. Google, Yelp) for a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            start_date, end_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with per-site stats.

        Example:
            sites_stats = client.fetch_review_analytics_sites_stats(16808)
        """
        params: dict[str, str] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        data = self._listings_get(location_id, "review-analytics-sites-stats", params=params)
        return data.get("data", {}).get("interactionsSitesStats") or {}

    # --- Rankings (keywords) ---

    def fetch_keywords(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get all keywords tracked for a location (for rankings).

        Args:
            location_id: Location ID — numeric or base64-encoded.

        Returns:
            List of keyword dicts (id, name, etc.).

        Example:
            keywords = client.fetch_keywords(16808)
        """
        data = self._listings_get(location_id, "keywords")
        return data.get("data", {}).get("keywordsByLocationId") or []

    def fetch_keywords_performance(
        self,
        location_id: str | int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get ranking performance for a location's keywords over an optional date range.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            from_date, to_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            List of keyword performance dicts.

        Example:
            performance = client.fetch_keywords_performance(16808, from_date="2024-01-01", to_date="2024-01-31")
        """
        params: dict[str, str] = {}
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        data = self._listings_get(location_id, "keywords-performance", params=params)
        return data.get("data", {}).get("keywordsByLocationId") or []

    # --- Review campaigns ---

    def fetch_review_campaigns(
        self,
        location_id: str | int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get review campaigns for a location, optionally filtered by date range.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            start_date, end_date: Optional. Filter campaigns by date in YYYY-MM-DD.

        Returns:
            List of review campaign dicts.

        Example:
            campaigns = client.fetch_review_campaigns(16808, start_date="2024-01-01", end_date="2024-12-31")
        """
        params: dict[str, str] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        data = self._listings_get(location_id, "review-campaigns", params=params)
        list_data = data.get("data", {}).get("listReviewCampaigns") or {}
        return list_data.get("reviewCampaigns") or []

    # --- Profile analytics ---

    def fetch_bing_analytics(
        self,
        location_id: str | int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get Bing profile analytics for a location (e.g. weekly views, actions).

        Args:
            location_id: Location ID — numeric or base64-encoded.
            from_date, to_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with Bing insights data.

        Example:
            bing = client.fetch_bing_analytics(16808, from_date="2024-01-01", to_date="2024-01-31")
        """
        params: dict[str, str] = {}
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        data = self._listings_get(location_id, "bing-analytics", params=params)
        return data.get("data", {}).get("bingInsights") or {}

    def fetch_google_analytics(
        self,
        location_id: str | int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get Google (GMB) profile analytics for a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            from_date, to_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with Google insights data.

        Example:
            google = client.fetch_google_analytics(16808)
        """
        params: dict[str, str] = {}
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        data = self._listings_get(location_id, "google-analytics", params=params)
        return data.get("data", {}).get("googleInsights") or {}

    def fetch_facebook_analytics(
        self,
        location_id: str | int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get Facebook page analytics for a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.
            from_date, to_date: Optional. Date range in YYYY-MM-DD.

        Returns:
            Dict with Facebook insights data.

        Example:
            facebook = client.fetch_facebook_analytics(16808)
        """
        params: dict[str, str] = {}
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        data = self._listings_get(location_id, "facebook-analytics", params=params)
        return data.get("data", {}).get("facebookInsights") or {}

    # --- Photos, connection info, plan-sites, countries ---

    def fetch_location_photos(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get photos and media attached to a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.

        Returns:
            List of media/photo dicts.

        Example:
            photos = client.fetch_location_photos(16808)
        """
        data = self._listings_get(location_id, "photos")
        return data.get("data", {}).get("mediaFilesOfLocation") or []

    def fetch_connection_info(self, location_id: str | int) -> dict[str, Any]:
        """Get OAuth connection status (Google/Facebook) for a location.

        Args:
            location_id: Location ID — numeric or base64-encoded.

        Returns:
            Dict with connection/linking info per site.

        Example:
            info = client.fetch_connection_info(16808)
        """
        data = self._listings_get(location_id, "connection_info")
        return data.get("data", {}).get("locationConnectionInfo") or {}

    def fetch_plan_sites(self) -> list[dict[str, Any]]:
        """Get supported directories and site details for your plan (account-level).

        Returns:
            List of plan/site dicts.

        Example:
            sites = client.fetch_plan_sites()
        """
        data = self._api_get("plan-sites")
        return data.get("data", {}).get("planSites") or []

    def fetch_countries(self) -> list[dict[str, Any]]:
        """Get supported countries and states (ISO codes) for the account.

        Returns:
            List of country/state dicts.

        Example:
            countries = client.fetch_countries()
        """
        data = self._api_get("countries")
        return data.get("data", {}).get("supportedCountries") or []

    def fetch_review_site_config(self) -> list[dict[str, Any]]:
        """Get eligible review sources and site config for the account (account-level).

        Returns:
            List of review site config dicts.

        Example:
            config = client.fetch_review_site_config()
        """
        data = self._api_get("reviews/site-config")
        return data.get("data", {}).get("interactionSiteConfig") or []

    # --- POST: Create location ---

    def create_location(self, input: dict[str, Any]) -> dict[str, Any]:
        """Create a new location in your account. Use camelCase keys (name, storeId, street, city, etc.).

        Args:
            input: Location data. Required: name, storeId, street, city, stateIso, postalCode, countryIso, phone.
                Optional: description, ownerEmail, ownerName, and others per API.

        Returns:
            Dict with location (created object), success (bool), and errors (if any). Branch on success.

        Example:
            result = client.create_location({"name": "Acme Inc", "storeId": "ACME01", "street": "123 Main St", "city": "NYC", "stateIso": "NY", "postalCode": "10001", "countryIso": "US", "phone": "5551234567"})
        """
        data = self._api_post("locations", {"input": input})
        return data.get("data", {}).get("createLocation") or {}

    def update_location(self, input: dict[str, Any]) -> dict[str, Any]:
        """Update a location. Pass id (location ID) plus any fields to change (e.g. phone, name).

        Args:
            input: Must include id (base64 or numeric). Other keys are fields to update (camelCase).

        Returns:
            Dict with updated location, success, and optional errors.

        Example:
            client.update_location({"id": "TG9jYXRpb246MTM2OTc=", "phone": "5559876543"})
        """
        # Ensure the location ID is base64-encoded
        if "id" in input:
            input = {**input, "id": _encode_location_id(input["id"])}
        data = self._api_post("locations/update", {"input": input})
        return data.get("data", {}).get("updateLocation") or {}

    def archive_locations(self, location_ids: list[str]) -> dict[str, Any]:
        """Archive one or more locations (they are hidden, not deleted). Accepts numeric or base64 location IDs.

        Args:
            location_ids: List of location IDs (numeric or base64-encoded).

        Returns:
            Dict with success and any errors. Check success to confirm.

        Example:
            client.archive_locations(["TG9jYXRpb246MTM5OTg="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post("locations/archive", {"input": {"locationIds": encoded_ids}})
        return data.get("data", {}).get("archiveLocations") or {}

    def activate_locations(self, location_ids: list[str]) -> dict[str, Any]:
        """Reactivate previously archived locations. Accepts numeric or base64 location IDs.

        Args:
            location_ids: List of location IDs (numeric or base64-encoded).

        Returns:
            Dict with success and any errors.

        Example:
            client.activate_locations(["TG9jYXRpb246MTM5OTg="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post("locations/activate", {"input": {"locationIds": encoded_ids}})
        return data.get("data", {}).get("activateLocations") or {}

    def cancel_archive_locations(
        self,
        location_ids: list[str],
        selection_type: str,
        changed_by: str,
    ) -> dict[str, Any]:
        """Cancel scheduled archival for the given locations.

        Args:
            location_ids: Base64-encoded location IDs.
            selection_type: "ALL_ITEMS" or "SELECTED_ITEMS".
            changed_by: Identifier of who is performing the action (e.g. user email or id).

        Returns:
            Dict with success and any errors.

        Example:
            client.cancel_archive_locations(["TG9jYXRpb246ODQ3NzM="], "SELECTED_ITEMS", "admin@example.com")
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "locations/cancel_archive",
            {"input": {"locationIds": encoded_ids, "selectionType": selection_type, "changedBy": changed_by}},
        )
        return data.get("data", {}).get("cancelLocationsArchive") or {}

    # --- POST: Location photos ---

    def add_location_photos(
        self, location_id: str | int, photos: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Add one or more photos to a location. Each item needs photo (URL) and type (LOGO, COVER, or ADDITIONAL).

        Args:
            location_id: Location ID — numeric or base64.
            photos: List of dicts with "photo" (URL string) and "type" (LOGO, COVER, or ADDITIONAL). Optional: partnerMediaId.

        Returns:
            Dict with addLocationPhotos result; check success for outcome.

        Example:
            client.add_location_photos(16808, [{"photo": "https://example.com/logo.png", "type": "LOGO"}])
        """
        data = self._api_post(
            "locations/photos",
            {"input": {"locationId": _encode_location_id(location_id), "photos": photos}},
        )
        return data.get("data", {}).get("addLocationPhotos") or {}

    def remove_location_photos(
        self, location_id: str | int, photo_ids: list[str]
    ) -> dict[str, Any]:
        """Remove photos from a location. Only ADDITIONAL photos can be removed; pass their photo IDs.

        Args:
            location_id: Location ID — numeric or base64.
            photo_ids: List of base64 photo IDs to remove.

        Returns:
            Dict with removeLocationPhotos result.

        Example:
            client.remove_location_photos(16808, ["TG9jYXRpb25QaG90bzoxMjI2MA=="])
        """
        data = self._api_post(
            "locations/photos/remove",
            {"input": {"locationId": _encode_location_id(location_id), "photoIds": photo_ids}},
        )
        return data.get("data", {}).get("removeLocationPhotos") or {}

    def star_location_photos(
        self, location_id: str | int, media_ids: list[str], starred: bool
    ) -> dict[str, Any]:
        """Mark location photos as starred or unstarred. Account can have at most 4 starred photos.

        Args:
            location_id: Location ID — numeric or base64.
            media_ids: List of media IDs to star or unstar.
            starred: True to star, False to unstar.

        Returns:
            Dict with starUnstarLocationPhotos result.

        Example:
            client.star_location_photos(16808, ["TWVkaWFGaWxlOjg4MjY5Nw=="], starred=True)
        """
        data = self._api_post(
            "locations/photos/star",
            {"input": {"locationId": _encode_location_id(location_id), "mediaIds": media_ids, "starred": starred}},
        )
        return data.get("data", {}).get("starUnstarLocationPhotos") or {}

    # --- POST: Folders (organizing locations) ---

    def create_folder(
        self,
        name: str,
        parent_folder: str | None = None,
        parent_folder_name: str | None = None,
    ) -> dict[str, Any]:
        """Create a folder to organize locations. Optionally nest under a parent by ID or name.

        Args:
            name: Name for the new folder.
            parent_folder: Optional. Parent folder UUID.
            parent_folder_name: Optional. Parent folder name (e.g. "all_franchise").

        Returns:
            Dict with created folder and success.

        Example:
            client.create_folder("franchise", parent_folder_name="all_franchise")
        """
        payload: dict[str, Any] = {"name": name}
        if parent_folder is not None:
            payload["parentFolder"] = parent_folder
        if parent_folder_name is not None:
            payload["parentFolderName"] = parent_folder_name
        data = self._api_post("folders/create", {"input": payload})
        return data.get("data", {}).get("createFolder") or {}

    def rename_folder(self, old_name: str, new_name: str) -> dict[str, Any]:
        """Rename an existing folder.

        Args:
            old_name: Current folder name.
            new_name: New name to set.

        Returns:
            Dict with rename result and success.

        Example:
            client.rename_folder("Acme", "Acme New")
        """
        data = self._api_post(
            "locations/folders/rename",
            {"input": {"oldName": old_name, "name": new_name}},
        )
        return data.get("data", {}).get("renameFolder") or {}

    def add_locations_to_folder(
        self, folder_name: str, location_ids: list[str]
    ) -> dict[str, Any]:
        """Add locations to a folder. Folder is created if it does not exist. Pass base64 location IDs.

        Args:
            folder_name: Name of the folder (created if missing).
            location_ids: List of base64-encoded location IDs to add.

        Returns:
            Dict with add result and success.

        Example:
            client.add_locations_to_folder("Acme", ["TG9jYXRpb246MTY4NjE=", "TG9jYXRpb246MTY4NjA="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "locations/folders",
            {"input": {"name": folder_name, "locationIds": encoded_ids}},
        )
        return data.get("data", {}).get("addLocationsToFolder") or {}

    def remove_locations_from_folder(self, location_ids: list[str]) -> dict[str, Any]:
        """Remove locations from their current folder. Pass base64 location IDs.

        Args:
            location_ids: List of base64-encoded location IDs to remove from folders.

        Returns:
            Dict with result and success.

        Example:
            client.remove_locations_from_folder(["TG9jYXRpb246MTY4NDY="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "locations/folders/remove",
            {"input": {"locationIds": encoded_ids}},
        )
        return data.get("data", {}).get("deleteLocationsFromFolder") or {}

    def delete_folder(self, name: str) -> dict[str, Any]:
        """Delete a folder by its name. Locations in the folder are not deleted.

        Args:
            name: Exact folder name to delete.

        Returns:
            Dict with delete result and success.

        Example:
            client.delete_folder("Acme New")
        """
        data = self._api_post("folders/delete", {"input": {"name": name}})
        return data.get("data", {}).get("deleteFolder") or {}

    # --- POST: Tags (organizing locations) ---

    def add_location_tag(self, location_id: str | int, tag: str) -> dict[str, Any]:
        """Add a tag to a location. Tag is created if it does not exist.

        Args:
            location_id: Location ID — numeric or base64.
            tag: Tag name to add (e.g. "vip", "new").

        Returns:
            Dict with add result and success.

        Example:
            client.add_location_tag(16808, "New")
        """
        data = self._api_post(
            "locations/tags",
            {"input": {"locationId": _encode_location_id(location_id), "tag": tag}},
        )
        return data.get("data", {}).get("addTag") or {}

    def remove_location_tag(self, location_id: str | int, tag: str) -> dict[str, Any]:
        """Remove a tag from a location.

        Args:
            location_id: Location ID — numeric or base64.
            tag: Tag name to remove.

        Returns:
            Dict with result and success.

        Example:
            client.remove_location_tag(16808, "Old")
        """
        data = self._api_post(
            "locations/tags/remove",
            {"input": {"locationId": _encode_location_id(location_id), "tag": tag}},
        )
        return data.get("data", {}).get("removeTag") or {}

    # --- POST: Listings (mark duplicate) ---

    def mark_listings_as_duplicate(
        self, location_id: str | int, listing_item_ids: list[str]
    ) -> dict[str, Any]:
        """Mark one or more listing items as duplicate for a location. Pass base64 listing item IDs.

        Args:
            location_id: Location ID — numeric or base64.
            listing_item_ids: List of base64 listing item IDs to mark as duplicate.

        Returns:
            Dict with result and success.

        Example:
            client.mark_listings_as_duplicate(16808, ["TGlzdGluZ0l0ZW06MzMzMjkzOA=="])
        """
        data = self._api_post(
            "locations/listings/mark-as-duplicate",
            {"input": {"locationId": _encode_location_id(location_id), "listingItemIds": listing_item_ids}},
        )
        return data.get("data", {}).get("markAsDuplicate") or {}

    def mark_listings_as_not_duplicate(
        self, location_id: str | int, listing_item_ids: list[str]
    ) -> dict[str, Any]:
        """Clear duplicate status for listing items. Pass base64 listing item IDs.

        Args:
            location_id: Location ID — numeric or base64.
            listing_item_ids: List of base64 listing item IDs to mark as not duplicate.

        Returns:
            Dict with result and success.

        Example:
            client.mark_listings_as_not_duplicate(16808, ["TGlzdGluZ0l0ZW06MzMzMjkzOA=="])
        """
        data = self._api_post(
            "locations/listings/mark-as-not-duplicate",
            {"input": {"locationId": _encode_location_id(location_id), "listingItemIds": listing_item_ids}},
        )
        return data.get("data", {}).get("markAsNotDuplicate") or {}

    # --- POST: Reviews (interactions) respond / settings ---

    def respond_to_review(
        self, interaction_id: str, response_content: str
    ) -> dict[str, Any]:
        """Post a reply to a review or interaction. Use the interaction ID from fetch_interactions.

        Args:
            interaction_id: UUID of the interaction (review) to respond to.
            response_content: Text of your reply (shown publicly where applicable).

        Returns:
            Dict with respond result and success.

        Example:
            client.respond_to_review(interaction_id="2090753a-ece6-4837-8336-8494ad308523", response_content="Thank you!")
        """
        data = self._api_post(
            "locations/reviews/respond",
            {"interactionId": interaction_id, "responseContent": response_content},
        )
        return data.get("data", {}).get("respondToInteraction") or {}

    def edit_review_response(
        self, review_id: str, response_id: str, response_content: str
    ) -> dict[str, Any]:
        """Edit an existing reply to a review. Pass review ID, response ID, and new text.

        Args:
            review_id: ID of the review (interaction).
            response_id: ID of the response to edit.
            response_content: New reply text.

        Returns:
            Dict with edit result and success.

        Example:
            client.edit_review_response(review_id="...", response_id="...", response_content="Updated reply")
        """
        data = self._api_post(
            "locations/reviews/respond/edit",
            {"reviewId": review_id, "responseId": response_id, "responseContent": response_content},
        )
        return data.get("data", {}).get("editResponse") or {}

    def archive_review_response(self, response_id: str) -> dict[str, Any]:
        """Archive (hide) a reply to a review. Pass the response ID.

        Args:
            response_id: ID of the response to archive.

        Returns:
            Dict with archive result and success.

        Example:
            client.archive_review_response(response_id="...")
        """
        data = self._api_post(
            "locations/reviews/respond/archive",
            {"responseId": response_id},
        )
        return data.get("data", {}).get("archiveResponse") or {}

    def edit_review_settings(
        self, location_id: str | int, site_urls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Set or update review source URLs for a location. Each item is a dict with name and url.

        Args:
            location_id: Location ID — numeric or base64.
            site_urls: List of dicts with "name" and "url" (e.g. {"name": "trulia.com", "url": "https://..."}).

        Returns:
            Dict with edit result and success.

        Example:
            client.edit_review_settings(16808, [{"name": "trulia.com", "url": "https://trulia.com/biz/..."}])
        """
        data = self._api_post(
            "locations/reviews/settings/edit",
            {"locationId": _encode_location_id(location_id), "siteUrls": site_urls},
        )
        return data.get("data", {}).get("editInteractionsSetting") or {}

    # --- POST: Review campaigns ---

    def create_review_campaign(
        self,
        location_id: str | int,
        name: str,
        location_customers: list[dict[str, Any]],
        screening: bool | None = None,
        landing_page_template: dict[str, Any] | None = None,
        opening_email_template: dict[str, Any] | None = None,
        sms_template: dict[str, Any] | None = None,
        email_details: dict[str, Any] | None = None,
        sms_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a review campaign for a location and optionally add customers and templates.

        Args:
            location_id: Location ID — numeric or base64.
            name: Campaign name.
            location_customers: List of dicts with name; optional email and phone (e.g. [{"name": "John", "email": "j@example.com"}]).
            screening, landing_page_template, opening_email_template, sms_template: Optional campaign config.
            email_details, sms_details: Optional dicts for email/SMS (e.g. subject, content).

        Returns:
            Dict with reviewCampaign, success, and errors. Branch on success.

        Example:
            result = client.create_review_campaign(16808, "Holiday Feedback", [{"name": "John", "email": "j@example.com"}], screening=False)
        """
        payload = {
            "locationId": _encode_location_id(location_id),
            "name": name,
            "locationCustomers": location_customers,
        }
        if screening is not None:
            payload["screening"] = screening
        if landing_page_template is not None:
            payload["landingPageTemplate"] = landing_page_template
        if opening_email_template is not None:
            payload["openingEmailTemplate"] = opening_email_template
        if sms_template is not None:
            payload["smsTemplate"] = sms_template
        if email_details is not None:
            payload["emailDetails"] = email_details
        if sms_details is not None:
            payload["smsDetails"] = sms_details
        data = self._api_post("locations/review-campaigns", {"input": payload})
        return data.get("data", {}).get("createReviewCampaign") or {}

    def add_review_campaign_customers(
        self,
        review_campaign_id: str,
        location_customers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Add customers to an existing review campaign. Pass campaign ID and list of customer dicts.

        Args:
            review_campaign_id: UUID of the review campaign.
            location_customers: List of dicts with at least name; optional email, phone.

        Returns:
            Dict with add result and success.

        Example:
            client.add_review_campaign_customers("794be682-a321-4eac-953c-37dcac0a55a2", [{"name": "Jane", "email": "jane@example.com"}])
        """
        data = self._api_post(
            "locations/review-campaigns/customers",
            {
                "input": {
                    "reviewCampaignId": review_campaign_id,
                    "locationCustomers": location_customers,
                }
            },
        )
        return data.get("data", {}).get("addCustomersToReviewCampaign") or {}

    # --- POST: Keywords (rankings) ---

    def add_keywords(
        self, location_id: str | int, keywords: list[str]
    ) -> list[dict[str, Any]]:
        """Add keywords to a location for ranking tracking. Returns the created keyword objects.

        Args:
            location_id: Location ID — numeric or base64.
            keywords: List of keyword strings (e.g. ["plumber", "plumbing near me"]).

        Returns:
            List of created keyword dicts (id, name, etc.).

        Example:
            created = client.add_keywords(16808, ["plumber", "plumbing near me"])
        """
        data = self._api_post(
            "locations/keywords",
            {
                "locationId": _encode_location_id(location_id),
                "inputKeywords": keywords,
            },
        )
        add_result = data.get("data", {}).get("addKeywords") or {}
        return add_result.get("keywords") or []

    def archive_keyword(self, keyword_id: str) -> dict[str, Any]:
        """Archive a keyword so it is no longer tracked. Pass the keyword's base64 ID.

        Args:
            keyword_id: Base64-encoded keyword ID (from fetch_keywords or add_keywords).

        Returns:
            Dict with archived keyword and success.

        Example:
            client.archive_keyword("S2V5d29yZDo3NjQzMTE=")
        """
        data = self._api_post("locations/keywords/archive", {"id": keyword_id})
        archive_result = data.get("data", {}).get("archiveKeyword") or {}
        return archive_result.get("keyword") or {}

    def fetch_ranking_analytics_timeline(
        self,
        location_ids: list[str],
        from_date: str,
        to_date: str,
        source: list[str],
    ) -> list[dict[str, Any]]:
        """Get ranking analytics timeline (positions over time) for locations and a source (e.g. Google).

        Args:
            location_ids: List of base64-encoded location IDs.
            from_date, to_date: Date range in YYYY-MM-DD.
            source: List of source names (e.g. ["Google"]).

        Returns:
            List of timeline/rollup dicts by date.

        Example:
            timeline = client.fetch_ranking_analytics_timeline(["TG9jYXRpb246NzkwODQ="], "2023-03-11", "2023-03-15", ["Google"])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "locations/ranking-analytics-timeline",
            {"fromDate": from_date, "toDate": to_date, "locationIds": encoded_ids, "source": source},
        )
        return data.get("data", {}).get("rankingsRollupByDate") or []

    def fetch_ranking_sitewise_histogram(
        self,
        location_ids: list[str],
        from_date: str,
        to_date: str,
        source: list[str],
    ) -> list[dict[str, Any]]:
        """Get ranking histogram by keyword count for locations and a source (e.g. Google).

        Args:
            location_ids: List of base64-encoded location IDs.
            from_date, to_date: Date range in YYYY-MM-DD.
            source: List of source names (e.g. ["Google"]).

        Returns:
            List of histogram/rollup dicts.

        Example:
            histogram = client.fetch_ranking_sitewise_histogram(["TG9jYXRpb246NzkwODQ="], "2023-03-11", "2023-03-15", ["Google"])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "locations/ranking-sitewise-histogram",
            {"fromDate": from_date, "toDate": to_date, "locationIds": encoded_ids, "source": source},
        )
        return data.get("data", {}).get("rankingsRollupByKeywordCount") or []

    # --- User management ---

    def fetch_users(self) -> list[dict[str, Any]]:
        """Get all users in the account.

        Returns:
            List of user dicts (id, email, firstName, lastName, role, etc.).
        """
        data = self._api_get("users")
        return data.get("data", {}).get("users") or data.get("users") or []

    def create_user(
        self,
        email: str,
        role_id: str,
        first_name: str,
        last_name: str | None = None,
        direct_customer: bool | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create a user in the account with the given role. Pass email, role ID, and first name.

        Args:
            email: User's email address.
            role_id: Base64 role ID (from your account's roles).
            first_name: User's first name.
            last_name: Optional. User's last name.
            direct_customer: Optional. Whether user is a direct customer.
            **extra: Optional. Additional fields passed to the API.

        Returns:
            Dict with user, success, and errors. Branch on success.

        Example:
            result = client.create_user("user@example.com", "Q3VzdG9tUm9sZToyMDgzMQ==", "Jane", last_name="Doe")
        """
        payload: dict[str, Any] = {
            "email": email,
            "roleId": role_id,
            "firstName": first_name,
        }
        if last_name is not None:
            payload["lastName"] = last_name
        if direct_customer is not None:
            payload["directCustomer"] = direct_customer
        payload.update(extra)
        data = self._api_post("users/create", {"input": payload})
        return data.get("data", {}).get("addUser") or {}

    def update_user(
        self,
        user_id: str,
        email: str | None = None,
        role_id: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        archived: bool | None = None,
        direct_customer: bool | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Update a user. Pass user ID and any fields to change (email, role, name, phone, etc.).

        Args:
            user_id: Base64 user ID to update.
            email, role_id, first_name, last_name, phone, archived, direct_customer: Optional. Only include what you want to change.
            **extra: Optional. Additional fields for the API.

        Returns:
            Dict with user, success, and errors.

        Example:
            client.update_user("VXNlcjo5OTY0", first_name="Jane Updated")
        """
        payload: dict[str, Any] = {"id": user_id}
        if email is not None:
            payload["email"] = email
        if role_id is not None:
            payload["roleId"] = role_id
        if first_name is not None:
            payload["firstName"] = first_name
        if last_name is not None:
            payload["lastName"] = last_name
        if phone is not None:
            payload["phone"] = phone
        if archived is not None:
            payload["archived"] = archived
        if direct_customer is not None:
            payload["directCustomer"] = direct_customer
        payload.update(extra)
        data = self._api_post("users/update", {"input": payload})
        return data.get("data", {}).get("updateUser") or {}

    def add_user_locations(
        self, user_id: str, location_ids: list[str]
    ) -> dict[str, Any]:
        """Assign locations to a user. Pass user ID and list of base64 location IDs.

        Args:
            user_id: Base64 user ID.
            location_ids: List of base64 location IDs to assign.

        Returns:
            Dict with status list and success.

        Example:
            client.add_user_locations("VXNlcjoxMDAyOA==", ["TG9jYXRpb246NDA5ODE="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "users/locations/add",
            {"input": {"userId": user_id, "locationIds": encoded_ids}},
        )
        return data.get("data", {}).get("addLocationsForUser") or {}

    def remove_user_locations(
        self, user_id: str, location_ids: list[str]
    ) -> dict[str, Any]:
        """Remove location assignments from a user. Pass user ID and location IDs to remove.

        Args:
            user_id: Base64 user ID.
            location_ids: List of location IDs (numeric or base64-encoded).

        Returns:
            Dict with result and success.

        Example:
            client.remove_user_locations("VXNlcjoxMDAyOA==", ["TG9jYXRpb246NTE1MzA="])
        """
        encoded_ids = [_encode_location_id(lid) for lid in location_ids]
        data = self._api_post(
            "users/locations/remove",
            {"input": {"userId": user_id, "locationIds": encoded_ids}},
        )
        return data.get("data", {}).get("removeLocationsForUser") or {}

    def add_user_folders(
        self, user_id: str, folder_ids: list[str]
    ) -> dict[str, Any]:
        """Assign folders to a user. Pass user ID and list of folder IDs (UUIDs).

        Args:
            user_id: Base64 user ID.
            folder_ids: List of folder UUIDs to assign.

        Returns:
            Dict with status list and success.

        Example:
            client.add_user_folders("VXNlcjoxMDAyOA==", ["folder-uuid-1"])
        """
        data = self._api_post(
            "users/folders/add",
            {"input": {"userId": user_id, "folderIds": folder_ids}},
        )
        return data.get("data", {}).get("addFoldersForUser") or {}

    def remove_user_folders(
        self, user_id: str, folder_ids: list[str]
    ) -> dict[str, Any]:
        """Remove folder assignments from a user. Pass user ID and folder IDs to remove.

        Args:
            user_id: Base64 user ID.
            folder_ids: List of folder UUIDs to remove.

        Returns:
            Dict with result and success.

        Example:
            client.remove_user_folders("VXNlcjoxMDAyOA==", ["folder-uuid-1"])
        """
        data = self._api_post(
            "users/folders/remove",
            {"input": {"userId": user_id, "folderIds": folder_ids}},
        )
        return data.get("data", {}).get("removeFoldersForUser") or {}

    def add_user_and_folder(self, input: dict[str, Any]) -> dict[str, Any]:
        """Create a user and a folder, then assign the folder to the user in one call. Convenience for onboarding.

        Args:
            input: Dict with roleId, firstName, email, name (folder name), locationIds; optional lastName, etc.

        Returns:
            Dict with addUserAndFolder result; check success and errors.

        Example:
            client.add_user_and_folder({"roleId": "...", "firstName": "Jane", "email": "j@example.com", "name": "folder_name", "locationIds": ["..."]})
        """
        data = self._api_post("users/add_user_and_folder", {"input": input})
        return data.get("data", {}).get("addUserAndFolder") or {}

    # --- POST: Automations ---

    def create_temporary_close_automation(
        self,
        name: str,
        start_date: str,
        start_time: str,
        end_date: str,
        location_id: str | int,
    ) -> dict[str, Any]:
        """Create an automation that temporarily closes a location and reopens on a set date (Google/Facebook).

        Args:
            name: Name for the automation.
            start_date: Close date in YYYY-MM-DD.
            start_time: Close time (e.g. "10:00:00").
            end_date: Reopen date in YYYY-MM-DD.
            location_id: Location ID — numeric or base64.

        Returns:
            Dict with flow, success. Branch on success.

        Example:
            result = client.create_temporary_close_automation("Holiday closure", "2025-02-25", "10:00:00", "2025-02-28", 85006)
        """
        data = self._api_post(
            "automations/temporary-close-location-with-reopening-date",
            {
                "input": {
                    "name": name,
                    "startDate": start_date,
                    "startTime": start_time,
                    "endDate": end_date,
                    "locationId": _encode_location_id(location_id),
                }
            },
        )
        return data.get("data", {}).get("createFlowFromRecipe") or {}

    # --- POST: OAuth connect (profile connect) ---

    def get_oauth_connect_url(
        self,
        location_id: str | int,
        site: str,
        success_url: str,
        error_url: str,
    ) -> dict[str, Any]:
        """Get a URL to connect a Google or Facebook profile to a location. Link is valid 24 hours. Redirect the user to the returned URL.

        Args:
            location_id: Location ID — numeric or base64.
            site: "GOOGLE" or "FACEBOOK".
            success_url: Where to redirect after successful connection (your app URL).
            error_url: Where to redirect after error (your app URL).

        Returns:
            Dict with url (redirect the user here). Check for presence of url.

        Example:
            result = client.get_oauth_connect_url(16808, "GOOGLE", "https://yoursite.com/success", "https://yoursite.com/error")
            redirect_user_to(result["url"])
        """
        data = self._api_post(
            "locations/oauth_connect_url",
            {
                "input": {
                    "locationId": _encode_location_id(location_id),
                    "site": site.upper(),
                    "successUrl": success_url,
                    "errorUrl": error_url,
                }
            },
        )
        return data.get("data", {}).get("connectUrl") or {}

    def oauth_disconnect(self, location_id: str | int, site: str) -> dict[str, Any]:
        """Disconnect a Google or Facebook profile from a location. Use for a single location.

        Args:
            location_id: Location ID — numeric or base64.
            site: "GOOGLE" or "FACEBOOK".

        Returns:
            Dict with disconnect result and success.

        Example:
            client.oauth_disconnect(16808, "FACEBOOK")
        """
        data = self._api_post(
            "locations/oauth-disconnect",
            {
                "input": {
                    "locationId": _encode_location_id(location_id),
                    "site": site.upper(),
                }
            },
        )
        return data.get("data", {}).get("disconnectConnectedAccountsLocations") or {}

    # --- POST: Connected accounts (bulk connect) ---

    def connect_google_account(
        self, success_url: str, error_url: str
    ) -> dict[str, Any]:
        """Get a URL to connect a Google account for bulk use across locations. Valid 24 hours. Redirect the user to the returned URL.

        Args:
            success_url: Your app URL for successful connection redirect.
            error_url: Your app URL for error redirect.

        Returns:
            Dict with url. Redirect user to url to start connection.

        Example:
            result = client.connect_google_account("https://ok.com", "https://err.com")
        """
        data = self._api_post(
            "connected-accounts/connect-google",
            {"input": {"successUrl": success_url, "errorUrl": error_url}},
        )
        return data.get("data", {}).get("bulkConnectLinkForGoogle") or {}

    def connect_facebook_account(
        self, success_url: str, error_url: str
    ) -> dict[str, Any]:
        """Get a URL to connect a Facebook account for bulk use across locations. Valid 24 hours. Redirect the user to the returned URL.

        Args:
            success_url: Your app URL for successful connection redirect.
            error_url: Your app URL for error redirect.

        Returns:
            Dict with url. Redirect user to url to start connection.

        Example:
            result = client.connect_facebook_account("https://ok.com", "https://err.com")
        """
        data = self._api_post(
            "connected-accounts/connect-facebook",
            {"input": {"successUrl": success_url, "errorUrl": error_url}},
        )
        return data.get("data", {}).get("bulkConnectLinkForFacebook") or {}

    def disconnect_google_account(
        self, connected_account_id: str
    ) -> dict[str, Any]:
        """Disconnect a Google connected account (bulk). Pass the connected account ID.

        Args:
            connected_account_id: ID of the Google connected account to disconnect.

        Returns:
            Dict with success. Branch on success.

        Example:
            client.disconnect_google_account(connected_account_id="...")
        """
        data = self._api_post(
            "connected-accounts/disconnect-google",
            {"input": {"connectedAccountId": connected_account_id}},
        )
        return data.get("data", {}).get("gmbBulkDisconnect") or {}

    def disconnect_facebook_account(
        self, connected_account_id: str
    ) -> dict[str, Any]:
        """Disconnect a Facebook connected account (bulk). Pass the connected account ID.

        Args:
            connected_account_id: ID of the Facebook connected account to disconnect.

        Returns:
            Dict with success. Branch on success.

        Example:
            client.disconnect_facebook_account(connected_account_id="...")
        """
        data = self._api_post(
            "connected-accounts/disconnect-facebook",
            {"input": {"connectedAccountId": connected_account_id}},
        )
        return data.get("data", {}).get("fbBulkDisconnect") or {}

    def trigger_connected_account_matches(
        self, connected_account_ids: list[str]
    ) -> dict[str, Any]:
        """Trigger matching of Google/Facebook profile locations to Synup locations. Pass connected account IDs.

        Args:
            connected_account_ids: List of connected account IDs to run matching for.

        Returns:
            Dict with success and failedIds (if any). Branch on success.

        Example:
            client.trigger_connected_account_matches(["6eb312f7-df32-4d76-ad8a-26bcfeab601e"])
        """
        data = self._api_post(
            "connected-accounts/trigger-matches",
            {"input": {"connectedAccountIds": connected_account_ids}},
        )
        return data.get("data", {}).get("connectedAccountsTriggerMatches") or {}

    def fetch_connected_account_listings(
        self,
        connected_account_id: str,
        location_info: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        """Get listings (locations) the connected Google/Facebook account has access to. Optional filter and pagination.

        Args:
            connected_account_id: ID of the connected account.
            location_info: Optional. Filter by substring in street, city, phone, or name.
            page, per_page: Optional. Pagination; max 500 per page.

        Returns:
            Dict with pageInfo and records (list of listing dicts with id, locationName, address, etc.).

        Example:
            listings = client.fetch_connected_account_listings("3db66afa-...", location_info="123 William", page=1, per_page=100)
        """
        payload: dict[str, Any] = {"connectedAccountId": connected_account_id}
        if location_info is not None:
            payload["locationInfo"] = location_info
        if page is not None:
            payload["page"] = page
        if per_page is not None:
            payload["perPage"] = per_page
        data = self._api_post("connected-accounts/connected-account-listings", payload)
        return data.get("data", {}).get("connectedAccountListings") or {}

    def confirm_connected_account_matches(
        self, match_record_ids: list[str]
    ) -> dict[str, Any]:
        """Confirm suggested matches between connected account listings and Synup locations. Pass match record IDs (base64).

        Args:
            match_record_ids: List of base64 match record IDs from connection suggestions.

        Returns:
            Dict with success and failedIds. Branch on success.

        Example:
            client.confirm_connected_account_matches(["R21iTG9jYXRpb25NYXRjaGVkRGF0YTplNGZh..."])
        """
        data = self._api_post(
            "connected-accounts/confirm-matches",
            {"input": {"matchRecordIds": match_record_ids}},
        )
        return data.get("data", {}).get("confirmConnectMatches") or {}

    def connect_listing(
        self,
        location_id: str | int,
        connected_account_listing_id: str,
        connected_account_id: str,
    ) -> dict[str, Any]:
        """Link a Synup location to a listing from a connected Google/Facebook account. Use IDs from fetch_connected_account_listings.

        Args:
            location_id: Synup location ID — numeric or base64.
            connected_account_listing_id: Listing ID from fetch_connected_account_listings (e.g. records[].id).
            connected_account_id: Connected account ID.

        Returns:
            Dict with success and message. Branch on success.

        Example:
            client.connect_listing(73933, "R21iQnVsa0...", "3db66afa-...")
        """
        data = self._api_post(
            "connected-accounts/connect-listing",
            {
                "input": {
                    "locationId": _encode_location_id(location_id),
                    "connectedAccountListingId": connected_account_listing_id,
                    "connectedAccountId": connected_account_id,
                }
            },
        )
        return data.get("data", {}).get("connectListing") or {}

    def disconnect_listing(self, location_id: str | int, site: str) -> dict[str, Any]:
        """Unlink a location from its Google or Facebook listing. Use for a single location.

        Args:
            location_id: Location ID — numeric or base64.
            site: "GOOGLE" or "FACEBOOK".

        Returns:
            Dict with disconnect result and success.

        Example:
            client.disconnect_listing(16808, "GOOGLE")
        """
        data = self._api_post(
            "connected-accounts/disconnect-listing",
            {
                "input": {
                    "locationId": _encode_location_id(location_id),
                    "site": site.upper(),
                }
            },
        )
        return data.get("data", {}).get("disconnectConnectedAccountsLocations") or {}

    def create_gmb_listing(
        self,
        location_id: str | int,
        connected_account_id: str,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a Google Business Profile listing for an existing Synup location. Process is asynchronous; check success and errors.

        Args:
            location_id: Location ID — numeric or base64.
            connected_account_id: Google connected account ID.
            folder_id: Optional. GMB folder/group ID.

        Returns:
            Dict with success and errors. Branch on success; creation may complete in the background.

        Example:
            client.create_gmb_listing(14055, "bc818dc7-...", folder_id="accounts/1154433325552997863009")
        """
        payload: dict[str, Any] = {
            "locationId": _encode_location_id(location_id),
            "connectedAccountId": connected_account_id,
        }
        if folder_id is not None:
            payload["folderId"] = folder_id
        data = self._api_post("locations/create/gmb-listing", {"input": payload})
        return data.get("data", {}).get("createGmbListingForLocation") or {}

    # --- Grid rank ---

    def create_grid_report(
        self,
        location_id: str | int,
        keywords: list[str],
        business_name: str,
        business_street: str,
        business_city: str,
        business_state: str,
        business_country: str,
        latitude: float,
        longitude: float,
        distance: int,
        distance_unit: str,
        grid_size: int,
    ) -> dict[str, Any]:
        """Create a Local Rank Grid report (ranking positions across a geographic grid). Max 25 keywords.

        Args:
            location_id: Location ID — numeric or base64.
            keywords: List of keywords (max 25).
            business_name, business_street, business_city, business_state, business_country: Business address fields.
            latitude, longitude: Center of the grid (decimal degrees).
            distance: Grid radius (number).
            distance_unit: "mi" or "km".
            grid_size: 3, 5, or 7 (grid dimension).

        Returns:
            Dict with data.reportIds and errors. Branch on presence of errors.

        Example:
            result = client.create_grid_report(16808, ["italian restaurant"], "Chianti", "No 12, 5th Block", "Bengaluru", "Karnataka", "India", 12.935216, 77.619961, 20, "km", 3)
        """
        body = {
            "locationId": _encode_location_id(location_id),
            "keywords": keywords,
            "businessName": business_name,
            "businessStreet": business_street,
            "businessCity": business_city,
            "businessState": business_state,
            "businessCountry": business_country,
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance,
            "distanceUnit": distance_unit,
            "gridSize": grid_size,
        }
        data = self._api_post("create-grid-report", body)
        return data.get("data", {}).get("createGridrankReport") or {}

    def fetch_grid_report(self, report_id: str) -> dict[str, Any]:
        """Get a Local Rank Grid report by its ID. Use IDs from create_grid_report or fetch_location_grid_reports.

        Args:
            report_id: Grid report UUID.

        Returns:
            Dict with full report data.

        Example:
            report = client.fetch_grid_report("report-uuid")
        """
        data = self._api_get(f"grid-report/{report_id}")
        return data.get("data", {}).get("gridrankReportById") or {}

    def fetch_location_grid_reports(
        self,
        location_id: str | int,
        search_string: str | None = None,
        grid_size: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        sort_field: str | None = None,
        sort_order: str | None = None,
        page_size: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Get all Local Rank Grid reports for a location. Optional filters and pagination.

        Args:
            location_id: Location ID — numeric or base64.
            search_string, grid_size, from_date, to_date, sort_field, sort_order, page_size, page: Optional filters and pagination.

        Returns:
            Dict with reports (list) and total. Branch on reports for list; check total for count.

        Example:
            data = client.fetch_location_grid_reports(16808, page_size=20, page=1)
        """
        params: dict[str, str | int] = {}
        if search_string is not None:
            params["searchString"] = search_string
        if grid_size is not None:
            params["gridSize"] = grid_size
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        if sort_field is not None:
            params["sortField"] = sort_field
        if sort_order is not None:
            params["sortOrder"] = sort_order
        if page_size is not None:
            params["pageSize"] = page_size
        if page is not None:
            params["page"] = page
        data = self._listings_get(location_id, "grid-reports", params=params)
        list_data = data.get("data", {}).get("allGridrankReports") or {}
        return {"reports": list_data.get("reports") or [], "total": list_data.get("total")}

    # --- Photo Upload Status ---

    def fetch_photo_upload_status(self, request_id: str) -> dict[str, Any]:
        """Get the processing status for a bulk photo upload request.

        Args:
            request_id: The request ID returned when the bulk photo upload was initiated.

        Returns:
            Dict with bulk image processing status (e.g. status, counts, errors).

        Example:
            status = client.fetch_photo_upload_status("req-abc123")
        """
        data = self._api_get(f"locations/photos/requests/{request_id}")
        return data.get("data", {}).get("bulkImageProcessingStatus") or {}

    # --- Subscriptions ---

    def fetch_subscriptions(self) -> list[dict[str, Any]]:
        """Get active subscriptions for the account.

        Returns:
            List of active subscription dicts.

        Example:
            subs = client.fetch_subscriptions()
        """
        data = self._api_get("subscriptions")
        return data.get("data", {}).get("activeSubscriptions") or []

    # --- Folders ---

    def fetch_folders_flat(self) -> list[dict[str, Any]]:
        """Get all folders for the account as a flat list.

        Returns:
            List of folder dicts (id, name, parentId, etc.).

        Example:
            folders = client.fetch_folders_flat()
        """
        data = self._api_get("folders/flat")
        return data.get("data", {}).get("getUserFolders") or []

    def fetch_folders_tree(self) -> list[dict[str, Any]]:
        """Get all folders for the account as a nested tree structure.

        Returns:
            List of folder dicts with nested children.

        Example:
            tree = client.fetch_folders_tree()
        """
        data = self._api_get("folders/tree")
        return data.get("data", {}).get("getFolderTree") or []

    def fetch_folder_details(
        self,
        folder_id: str | None = None,
        folder_name: str | None = None,
    ) -> dict[str, Any]:
        """Get details for a specific folder by ID or name. At least one parameter is required.

        Args:
            folder_id: Folder UUID from your account.
            folder_name: Human-readable folder name (e.g. "franchise"). Either this or folder_id is required.

        Returns:
            Dict with folder details (id, name, locationCount, etc.).

        Example:
            details = client.fetch_folder_details(folder_name="franchise")
        """
        if not folder_id and not folder_name:
            raise ValueError("Provide either folder_id or folder_name")
        params: dict[str, str] = {}
        if folder_id:
            params["folderId"] = folder_id
        if folder_name:
            params["folderName"] = folder_name
        data = self._api_get("folder-details", params=params)
        return data.get("data", {}).get("getFolderDetails") or {}

    # --- Tags ---

    def fetch_tags(self) -> list[dict[str, Any]]:
        """Get all tags defined in the account.

        Returns:
            List of tag dicts (id, name, etc.).

        Example:
            tags = client.fetch_tags()
        """
        data = self._api_get("tags")
        return data.get("data", {}).get("listAllTags") or []

    # --- AI Listings ---

    def fetch_ai_listings(self, location_id: str | int) -> dict[str, Any]:
        """Get AI-generated listing suggestions for a location.

        Args:
            location_id: Location ID — numeric (e.g. 16808) or base64-encoded string.

        Returns:
            Dict with AI listing suggestions and metadata.

        Example:
            ai = client.fetch_ai_listings(16808)
        """
        data = self._listings_get(location_id, "ai-listings")
        return data.get("data", {}).get("fetchAiListings") or {}

    # --- Additional & Duplicate Listings ---

    def fetch_additional_listings(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get additional (non-premium) listings for a location.

        Args:
            location_id: Location ID — numeric (e.g. 16808) or base64-encoded string.

        Returns:
            List of additional listing dicts.

        Example:
            additional = client.fetch_additional_listings(16808)
        """
        data = self._listings_get(location_id, "listings/additional")
        return data.get("data", {}).get("listingsForLocation") or []

    def fetch_duplicate_listings(self, location_id: str | int) -> list[dict[str, Any]]:
        """Get duplicate listings detected for a location.

        Args:
            location_id: Location ID — numeric (e.g. 16808) or base64-encoded string.

        Returns:
            List of duplicate listing dicts.

        Example:
            dupes = client.fetch_duplicate_listings(16808)
        """
        data = self._listings_get(location_id, "listings/duplicates")
        return data.get("data", {}).get("duplicateListingsForLocation") or []

    def fetch_all_duplicate_listings(
        self,
        tag: str | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Get a rollup of duplicate listings across all locations, with optional tag filter and pagination.

        Args:
            tag: Optional. Filter by tag name.
            page: Optional. Page number for pagination.

        Returns:
            Dict with duplicate listings rollup data (locations, counts, etc.).

        Example:
            dupes = client.fetch_all_duplicate_listings(tag="recent", page=1)
        """
        params: dict[str, str | int] = {}
        if tag is not None:
            params["tag"] = tag
        if page is not None:
            params["page"] = page
        data = self._api_get("locations/listings/duplicates", params=params)
        return data.get("data", {}).get("duplicateListingsRollup") or {}

    # --- Review Details & Phrases ---

    def fetch_review_details(self, interaction_ids: list[str]) -> dict[str, Any]:
        """Get detailed information for specific reviews by their interaction IDs.

        Args:
            interaction_ids: List of interaction (review) IDs to look up.

        Returns:
            Dict with interaction details keyed by ID.

        Example:
            details = client.fetch_review_details(["id1", "id2"])
        """
        if not interaction_ids:
            return {}
        params = {"interactionIds": json.dumps(interaction_ids)}
        data = self._api_get("reviewDetails", params=params)
        return data.get("data", {}).get("interactionDetails") or {}

    def fetch_review_phrases(
        self,
        location_ids: list[str],
        site_urls: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get review phrase analysis (commonly mentioned phrases) for given locations.

        Args:
            location_ids: List of location IDs (base64-encoded) to analyze.
            site_urls: Optional. Restrict analysis to specific review sites (e.g. ["maps.google.com"]).
            start_date: Optional. Start date in YYYY-MM-DD format.
            end_date: Optional. End date in YYYY-MM-DD format.

        Returns:
            List of review phrase dicts (phrase, count, sentiment, etc.).

        Example:
            phrases = client.fetch_review_phrases(["TG9jYXRpb246MTY4MDg="], start_date="2024-01-01", end_date="2024-06-30")
        """
        if not location_ids:
            return []
        params: dict[str, str] = {"locationIds": json.dumps(location_ids)}
        if site_urls is not None:
            params["siteUrls"] = json.dumps(site_urls)
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        data = self._api_get("review-phrases", params=params)
        return data.get("data", {}).get("newReviewPhrases") or []

    # --- Review Campaign Customers ---

    def fetch_review_campaign_customers(self, review_campaign_id: str) -> dict[str, Any]:
        """Get customer details for a specific review campaign.

        Args:
            review_campaign_id: ID of the review campaign.

        Returns:
            Dict with review campaign info and customer records.

        Example:
            info = client.fetch_review_campaign_customers("campaign-uuid")
        """
        data = self._api_get(f"locations/review-campaigns/{review_campaign_id}/customers")
        return data.get("data", {}).get("reviewCampaignInfo") or {}

    # --- Connected Accounts ---

    def fetch_connected_accounts(
        self,
        publisher: str | None = None,
        status: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        """Get connected third-party accounts (Google, Facebook, etc.) with optional filters.

        Args:
            publisher: Optional. Filter by publisher (e.g. "google", "facebook").
            status: Optional. Filter by connection status (e.g. "active", "expired").
            page: Optional. Page number for pagination.
            per_page: Optional. Number of results per page.

        Returns:
            Dict with connected accounts info (accounts list, pagination, etc.).

        Example:
            accounts = client.fetch_connected_accounts(publisher="google", page=1, per_page=50)
        """
        params: dict[str, str | int] = {}
        if publisher is not None:
            params["publisher"] = publisher
        if status is not None:
            params["status"] = status
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["perPage"] = per_page
        data = self._api_get("connected-accounts", params=params)
        return data.get("data", {}).get("connectedAccountsInfo") or {}

    def fetch_connected_account_folders(
        self,
        connected_account_id: str,
        folder_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get folders (business groups) under a connected Google account.

        Args:
            connected_account_id: ID of the connected account.
            folder_name: Optional. Filter by folder name substring.

        Returns:
            List of folder dicts under the connected account.

        Example:
            folders = client.fetch_connected_account_folders("3db66afa-...", folder_name="Downtown")
        """
        params: dict[str, str] = {}
        if folder_name is not None:
            params["folderName"] = folder_name
        data = self._api_get(
            f"connected-accounts/{connected_account_id}/folders", params=params
        )
        return data.get("data", {}).get("getFoldersUnderGoogleAccount") or []

    def fetch_connected_account_details(self, connected_account_id: str) -> dict[str, Any]:
        """Get detailed information about a specific connected account.

        Args:
            connected_account_id: ID of the connected account.

        Returns:
            Dict with connected account details (email, publisher, status, etc.).

        Example:
            details = client.fetch_connected_account_details("3db66afa-...")
        """
        data = self._api_get(f"connected-accounts/{connected_account_id}/details")
        return data.get("data", {}).get("connectedAccountDetails") or {}

    def fetch_connection_suggestions(
        self,
        connected_account_id: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        """Get suggested matches between a connected account's listings and Synup locations.

        Args:
            connected_account_id: ID of the connected account.
            page: Optional. Page number for pagination.
            per_page: Optional. Number of results per page.

        Returns:
            Dict with connection suggestions (matched records, pagination, etc.).

        Example:
            suggestions = client.fetch_connection_suggestions("3db66afa-...", page=1, per_page=50)
        """
        params: dict[str, str | int] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["perPage"] = per_page
        data = self._api_get(
            f"connected-accounts/{connected_account_id}/connection-suggestions",
            params=params,
        )
        return data.get("data", {}).get("connectionSuggestionsForAccount") or {}

    # --- Roles ---

    def fetch_roles(self) -> list[dict[str, Any]]:
        """Get all roles defined in the account.

        Returns:
            List of role dicts (id, name, permissions, etc.).

        Example:
            roles = client.fetch_roles()
        """
        data = self._api_get("roles")
        return data.get("data", {}).get("fetchAccountRoles") or []

    # --- User Resources & Lookup ---

    def fetch_user_resources(self, user_id: str) -> list[dict[str, Any]]:
        """Get resources (locations, folders, etc.) assigned to a specific user.

        Args:
            user_id: Base64-encoded user ID.

        Returns:
            List of resource dicts assigned to the user.

        Example:
            resources = client.fetch_user_resources("VXNlcjoxMjM0")
        """
        data = self._api_get(f"users/{user_id}/resources")
        return data.get("data", {}).get("listUserResources") or []

    def fetch_users_by_ids(self, user_ids: list[str]) -> list[dict[str, Any]]:
        """Get users by a list of user IDs.

        Args:
            user_ids: List of user IDs (base64-encoded).

        Returns:
            List of user dicts (id, email, firstName, lastName, role, etc.).

        Example:
            users = client.fetch_users_by_ids(["VXNlcjoxMjM0", "VXNlcjo1Njc4"])
        """
        if not user_ids:
            return []
        params = {"userIds": json.dumps(user_ids)}
        data = self._api_get("users-by-ids", params=params)
        return data.get("data", {}).get("usersByIds") or []
