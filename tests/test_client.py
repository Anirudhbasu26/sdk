"""Tests for SynupClient."""

import pytest
import requests_mock

from synup import SynupAPIError, SynupClient


@pytest.fixture
def client():
    return SynupClient(api_key="test-api-key")


@pytest.fixture
def locations_response():
    return {
        "data": {
            "allLocations": {
                "edges": [
                    {
                        "cursor": "TG9jYXRpb246MTQwMjQ=",
                        "node": {
                            "id": "TG9jYXRpb246MTQwMjQ=",
                            "accountId": 100,
                            "name": "Stumptown",
                            "city": "New York",
                            "countryIso": "US",
                        },
                    },
                    {
                        "cursor": "TG9jYXRpb246MTQwMjM=",
                        "node": {
                            "id": "TG9jYXRpb246MTQwMjM=",
                            "accountId": 100,
                            "name": "S2nicetestinky",
                            "city": "Miami",
                            "countryIso": "US",
                        },
                    },
                ],
                "pageInfo": {
                    "hasNextPage": True,
                    "hasPreviousPage": False,
                },
            }
        }
    }


@pytest.fixture
def locations_response_last_page():
    return {
        "data": {
            "allLocations": {
                "edges": [
                    {
                        "cursor": "TG9jYXRpb246MTQwMjI=",
                        "node": {
                            "id": "TG9jYXRpb246MTQwMjI=",
                            "accountId": 100,
                            "name": "Last Location",
                            "city": "Boston",
                            "countryIso": "US",
                        },
                    },
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "hasPreviousPage": True,
                },
            }
        }
    }


def test_client_uses_default_base_url():
    client = SynupClient(api_key="key")
    assert client._base_url == "https://api.synup.com"


def test_client_uses_custom_base_url():
    client = SynupClient(api_key="key", base_url="https://custom.synup.com")
    assert client._base_url == "https://custom.synup.com"


def test_client_strips_trailing_slash_from_base_url():
    client = SynupClient(api_key="key", base_url="https://api.synup.com/")
    assert client._base_url == "https://api.synup.com"


def test_client_sets_auth_headers():
    client = SynupClient(api_key="my-key")
    assert client._session.headers["Authorization"] == "API my-key"
    assert client._session.headers["Content-Type"] == "application/json"


def test_fetch_all_locations_single_page(client, locations_response):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations",
            json=locations_response,
        )
        result = client.fetch_all_locations(first=2)

    assert isinstance(result, dict)
    assert "locations" in result
    assert "page_info" in result
    assert "raw" in result
    assert len(result["locations"]) == 2
    assert result["locations"][0]["name"] == "Stumptown"
    assert result["locations"][1]["name"] == "S2nicetestinky"
    assert result["page_info"]["has_next_page"] is True
    assert result["page_info"]["has_previous_page"] is False
    assert result["page_info"]["start_cursor"] == "TG9jYXRpb246MTQwMjQ="
    assert result["page_info"]["end_cursor"] == "TG9jYXRpb246MTQwMjM="
    assert m.call_count == 1
    assert m.last_request.query == "first=2"


def test_fetch_all_locations_with_after(client, locations_response):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations",
            json=locations_response,
        )
        client.fetch_all_locations(first=2, after="TG9jYXRpb246MTQwMjQ=")

    query = m.last_request.query
    assert "first=2" in query
    assert "after=" in query
    assert "TG9jYXRpb246MTQwMjQ" in query or "tg9jyxrpb246mtqwmjq" in query.lower()


def test_fetch_all_locations_raises_on_error(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations",
            status_code=401,
            text="Unauthorized",
        )
        with pytest.raises(SynupAPIError) as exc_info:
            client.fetch_all_locations()

    assert exc_info.value.status_code == 401
    assert exc_info.value.response_body == "Unauthorized"


def test_fetch_all_locations_fetch_all_true(
    client, locations_response, locations_response_last_page
):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations",
            [
                {"json": locations_response},
                {"json": locations_response_last_page},
            ],
        )
        result = client.fetch_all_locations(fetch_all=True, page_size=2)

    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["name"] == "Stumptown"
    assert result[1]["name"] == "S2nicetestinky"
    assert result[2]["name"] == "Last Location"
    assert m.call_count == 2
    # First call: first=2 only
    assert "first=2" in m.request_history[0].query
    assert "after" not in m.request_history[0].query
    # Second call: first=2&after=<cursor>
    assert "first=2" in m.request_history[1].query
    assert "after=" in m.request_history[1].query


def test_fetch_all_locations_fetch_all_single_page(client, locations_response_last_page):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations",
            json=locations_response_last_page,
        )
        result = client.fetch_all_locations(fetch_all=True, page_size=10)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Last Location"
    assert m.call_count == 1


def test_fetch_all_locations_empty_response(client):
    empty_response = {
        "data": {
            "allLocations": {
                "edges": [],
                "pageInfo": {"hasNextPage": False, "hasPreviousPage": False},
            }
        }
    }
    with requests_mock.Mocker() as m:
        m.get("https://api.synup.com/api/v4/locations", json=empty_response)
        result = client.fetch_all_locations()

    assert result["locations"] == []
    assert result["page_info"]["has_next_page"] is False
    assert result["page_info"]["start_cursor"] is None
    assert result["page_info"]["end_cursor"] is None


def test_fetch_locations_by_ids_empty(client):
    assert client.fetch_locations_by_ids([]) == []


def test_fetch_locations_by_ids(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations-by-ids",
            json={
                "data": {
                    "getLocationsByIds": [
                        {"id": "TG9jYXRpb246MTY4MDg=", "name": "Loc One"},
                        {"id": "TG9jYXRpb246MTY3NDk=", "name": "Loc Two"},
                    ]
                }
            },
        )
        result = client.fetch_locations_by_ids(["TG9jYXRpb246MTY4MDg=", "TG9jYXRpb246MTY3NDk="])
    assert len(result) == 2
    assert result[0]["name"] == "Loc One"
    assert result[1]["name"] == "Loc Two"


def test_fetch_locations_by_ids_numeric_encoded(client):
    """Numeric IDs (e.g. 16808) are base64-encoded as Location:16808 before the API call."""
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations-by-ids",
            json={"data": {"getLocationsByIds": [{"id": "TG9jYXRpb246MTY4MDg=", "name": "Loc 16808"}]}},
        )
        result = client.fetch_locations_by_ids([16808])
    assert len(result) == 1
    assert result[0]["name"] == "Loc 16808"
    # Request should contain base64-encoded "Location:16808" (TG9jYXRpb246MTY4MDg=)
    assert "TG9jYXRpb246MTY4MDg=" in m.last_request.query or "tg9jyxrpb246mty4mdg" in m.last_request.query.lower()


def test_fetch_locations_by_store_codes_empty(client):
    assert client.fetch_locations_by_store_codes([]) == []


def test_fetch_locations_by_store_codes(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations-by-store-codes",
            json={
                "data": {
                    "getLocationsByStoreCodes": [
                        {"storeId": "STORE01", "name": "Store One"},
                    ]
                }
            },
        )
        result = client.fetch_locations_by_store_codes(["STORE01"])
    assert len(result) == 1
    assert result[0]["storeId"] == "STORE01"
    assert result[0]["name"] == "Store One"


def test_search_locations(client, locations_response):
    search_response = {"data": {"searchLocations": locations_response["data"]["allLocations"]}}
    with requests_mock.Mocker() as m:
        m.get("https://api.synup.com/api/v4/locations/search", json=search_response)
        result = client.search_locations("cafe", first=2)
    assert "locations" in result
    assert "page_info" in result
    assert len(result["locations"]) == 2
    assert result["locations"][0]["name"] == "Stumptown"


def test_fetch_locations_by_folder_raises_without_args(client):
    with pytest.raises(ValueError, match="folder_id or folder_name"):
        client.fetch_locations_by_folder()


def test_fetch_locations_by_folder_by_name(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/folder-locations",
            json={
                "data": {
                    "getLocationsForFolder": [
                        {"id": "1", "name": "Folder Loc"},
                    ]
                }
            },
        )
        result = client.fetch_locations_by_folder(folder_name="franchise")
    assert len(result) == 1
    assert result[0]["name"] == "Folder Loc"
    assert "franchise" in m.last_request.query


def test_fetch_locations_by_folder_by_id(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/folder-locations",
            json={"data": {"getLocationsForFolder": []}},
        )
        client.fetch_locations_by_folder(folder_id="67049f29-3bc6-4e82-875b-02159b4b1fea")
    assert "folderId=67049f29" in m.last_request.query or "folderId=67049f29" in m.last_request.url


def test_fetch_locations_by_tags_empty(client):
    result = client.fetch_locations_by_tags([], fetch_all=False)
    assert result["locations"] == []
    assert result["page_info"] == {}
    assert client.fetch_locations_by_tags([], fetch_all=True) == []


def test_fetch_locations_by_tags(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/tags/locations",
            json={
                "data": {
                    "searchLocationsByTag": {
                        "edges": [
                            {"cursor": "c1", "node": {"id": "id1", "name": "Tagged Loc"}},
                        ],
                        "pageInfo": {"hasNextPage": False, "hasPreviousPage": False, "total": 1},
                    }
                }
            },
        )
        result = client.fetch_locations_by_tags(["recent"])
    assert len(result["locations"]) == 1
    assert result["locations"][0]["name"] == "Tagged Loc"
    assert result["page_info"]["total"] == 1


# --- Listings for a location ---


def test_fetch_premium_listings(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/listings/premium",
            json={
                "data": {
                    "listingsForLocation": [
                        {"id": "L1", "site": "Google", "syncStatus": "SYNCED", "listingUrl": "https://..."},
                    ]
                }
            },
        )
        result = client.fetch_premium_listings(16808)
    assert len(result) == 1
    assert result[0]["id"] == "L1"
    assert result[0]["site"] == "Google"
    assert "listings/premium" in m.last_request.path


def test_fetch_premium_listings_empty(client):
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json={"data": {}})
        result = client.fetch_premium_listings(16808)
    assert result == []


def test_fetch_voice_listings(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/voice-assistants",
            json={
                "data": {
                    "voiceAssistantsForLocation": [
                        {"name": "Google Assistant", "voiceIdentifier": "google", "syncStatus": "SYNCED"},
                    ]
                }
            },
        )
        result = client.fetch_voice_listings(16808)
    assert len(result) == 1
    assert result[0]["name"] == "Google Assistant"
    assert "voice-assistants" in m.last_request.path


def test_listings_use_numeric_location_id_encoding(client):
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, json={"data": {"listingsForLocation": []}})
        client.fetch_premium_listings(16808)
    assert "TG9jYXRpb246MTY4MDg=" in m.last_request.url


def test_listings_raise_on_api_error(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/listings/premium",
            status_code=404,
            text="Not found",
        )
        with pytest.raises(SynupAPIError) as exc_info:
            client.fetch_premium_listings(16808)
    assert exc_info.value.status_code == 404
    assert "404" in str(exc_info.value)


# --- Interactions ---


def test_fetch_interactions(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/reviews",
            json={
                "data": {
                    "interactions": {
                        "edges": [
                            {"node": {"id": "r1", "content": "Great!", "rating": 5}, "cursor": "c1"},
                        ],
                        "pageInfo": {"hasNextPage": False, "hasPreviousPage": False},
                        "totalCount": 1,
                    }
                }
            },
        )
        result = client.fetch_interactions(16808, first=10)
    assert "interactions" in result
    assert len(result["interactions"]) == 1
    assert result["interactions"][0]["id"] == "r1"
    assert result["total_count"] == 1
    assert "reviews" in m.last_request.path


def test_fetch_interactions_fetch_all(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/reviews",
            json={
                "data": {
                    "interactions": {
                        "edges": [{"node": {"id": "r1"}, "cursor": "c1"}],
                        "pageInfo": {"hasNextPage": False},
                    }
                }
            },
        )
        result = client.fetch_interactions(16808, fetch_all=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == "r1"


# --- Rankings (keywords) ---


def test_fetch_keywords(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/keywords",
            json={"data": {"keywordsByLocationId": [{"id": "k1", "name": "plumber"}]}},
        )
        result = client.fetch_keywords(16808)
    assert len(result) == 1
    assert result[0]["name"] == "plumber"
    assert "keywords" in m.last_request.path


def test_fetch_keywords_performance(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/keywords-performance",
            json={"data": {"keywordsByLocationId": [{"id": "k1", "name": "law", "sites": []}]}},
        )
        result = client.fetch_keywords_performance(16808, from_date="2024-01-01", to_date="2024-01-31")
    assert len(result) == 1
    assert "fromDate=2024-01-01" in m.last_request.url or "fromDate" in m.last_request.query


# --- Review campaigns ---


def test_fetch_review_campaigns(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/review-campaigns",
            json={
                "data": {
                    "listReviewCampaigns": {
                        "reviewCampaigns": [{"id": "rc1", "name": "Holiday Feedback"}]
                    }
                }
            },
        )
        result = client.fetch_review_campaigns(16808)
    assert len(result) == 1
    assert result[0]["name"] == "Holiday Feedback"


# --- Profile analytics ---


def test_fetch_bing_analytics(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/bing-analytics",
            json={"data": {"bingInsights": {"views": [{"startTime": "2024-01-01", "value": 10}]}}},
        )
        result = client.fetch_bing_analytics(16808, from_date="2024-01-01", to_date="2024-01-31")
    assert "views" in result
    assert len(result["views"]) == 1


# --- Photos, connection, plan-sites, countries ---


def test_fetch_location_photos(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/photos",
            json={"data": {"mediaFilesOfLocation": [{"id": "p1", "url": "https://example.com/1.jpg"}]}},
        )
        result = client.fetch_location_photos(16808)
    assert len(result) == 1
    assert result[0]["id"] == "p1"


def test_fetch_connection_info(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/connection_info",
            json={"data": {"locationConnectionInfo": {"google": {"credentialsValid": True}}}},
        )
        result = client.fetch_connection_info(16808)
    assert "google" in result
    assert result["google"]["credentialsValid"] is True


def test_fetch_plan_sites(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/plan-sites",
            json={"data": {"planSites": [{"id": 12, "name": "City Squares", "url": "citysquares.com"}]}},
        )
        result = client.fetch_plan_sites()
    assert len(result) == 1
    assert result[0]["name"] == "City Squares"
    assert "plan-sites" in m.last_request.path


def test_fetch_countries(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/countries",
            json={"data": {"supportedCountries": [{"iso": "US", "name": "United States", "states": []}]}},
        )
        result = client.fetch_countries()
    assert len(result) == 1
    assert result[0]["iso"] == "US"


def test_fetch_review_settings(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/reviews/settings",
            json={"data": {"interactionsSetting": {"siteSettings": [{"name": "maps.google.com"}]}}},
        )
        result = client.fetch_review_settings(16808)
    assert "siteSettings" in result
    assert result["siteSettings"][0]["name"] == "maps.google.com"


def test_fetch_review_analytics_overview(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/review-analytics-overview",
            json={"data": {"interactionsAnalyticsStats": {"stats": [{"name": "total-reviews", "value": 100}]}}},
        )
        result = client.fetch_review_analytics_overview(16808)
    assert "stats" in result
    assert result["stats"][0]["name"] == "total-reviews"


def test_fetch_review_site_config(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/reviews/site-config",
            json={"data": {"interactionSiteConfig": [{"site": "Google", "url": "maps.google.com"}]}},
        )
        result = client.fetch_review_site_config()
    assert len(result) == 1
    assert result[0]["site"] == "Google"


# --- POST: Create location, review campaigns, keywords, users, automations, OAuth, grid ---


def test_create_location(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations",
            json={
                "data": {
                    "createLocation": {
                        "success": True,
                        "location": {
                            "id": "TG9jYXRpb246MTQwNTU=",
                            "name": "Acme Inc",
                            "storeId": "ACME01",
                            "city": "New York",
                        },
                    }
                }
            },
        )
        result = client.create_location(
            {
                "name": "Acme Inc",
                "storeId": "ACME01",
                "street": "123 Jump Street",
                "city": "New York",
                "stateIso": "NY",
                "postalCode": "33133",
                "countryIso": "US",
                "phone": "6443859313",
            }
        )
    assert result.get("success") is True
    assert result.get("location", {}).get("name") == "Acme Inc"
    assert m.last_request.json()["input"]["name"] == "Acme Inc"
    assert "locations" in m.last_request.path


def test_create_review_campaign(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/review-campaigns",
            json={
                "data": {
                    "createReviewCampaign": {
                        "success": True,
                        "reviewCampaign": {"id": "rc-1", "name": "Holiday"},
                    }
                }
            },
        )
        result = client.create_review_campaign(
            16808,
            "Holiday",
            [{"name": "John", "email": "j@example.com", "phone": "123"}],
        )
    assert result.get("success") is True
    assert result.get("reviewCampaign", {}).get("name") == "Holiday"
    body = m.last_request.json()
    assert body["input"]["locationId"] == "TG9jYXRpb246MTY4MDg="
    assert body["input"]["name"] == "Holiday"


def test_add_keywords(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/keywords",
            json={"data": {"addKeywords": {"keywords": [{"id": "k1", "name": "plumber"}]}}},
        )
        result = client.add_keywords(16808, ["plumber"])
    assert len(result) == 1
    assert result[0]["name"] == "plumber"
    assert m.last_request.json()["inputKeywords"] == ["plumber"]


def test_archive_keyword(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/keywords/archive",
            json={"data": {"archiveKeyword": {"keyword": {"id": "k1", "archived": True, "name": "old"}}}},
        )
        result = client.archive_keyword("S2V5d29yZDo3NjQzMTE=")
    assert result.get("archived") is True


def test_create_user(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/users/create",
            json={"data": {"addUser": {"success": True, "user": {"id": "u1", "email": "u@example.com"}}}},
        )
        result = client.create_user("u@example.com", "role-1", "Jane")
    assert result.get("success") is True
    assert m.last_request.json()["input"]["email"] == "u@example.com"


def test_add_user_locations(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/users/locations/add",
            json={"data": {"addLocationsForUser": {"status": [{"success": True}]}}},
        )
        result = client.add_user_locations("VXNlcjoxMDAyOA==", ["TG9jYXRpb246NDA5ODE="])
    assert "status" in result
    assert m.last_request.json()["input"]["userId"] == "VXNlcjoxMDAyOA=="


def test_create_temporary_close_automation(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/automations/temporary-close-location-with-reopening-date",
            json={"data": {"createFlowFromRecipe": {"success": True, "flow": {"id": "flow-1"}}}},
        )
        result = client.create_temporary_close_automation(
            "Close for holiday",
            "2025-02-25",
            "10:00:00",
            "2025-02-28",
            85006,
        )
    assert result.get("success") is True
    assert result.get("flow", {}).get("id") == "flow-1"
    assert "locationId" in m.last_request.json()["input"]


def test_get_oauth_connect_url(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/oauth_connect_url",
            json={"data": {"connectUrl": {"url": "https://connect.example.com/oauth"}}},
        )
        result = client.get_oauth_connect_url(
            16808, "GOOGLE", "https://success.com", "https://error.com"
        )
    assert "url" in result
    assert "oauth" in result["url"]
    assert m.last_request.json()["input"]["site"] == "GOOGLE"


def test_oauth_disconnect(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/oauth-disconnect",
            json={"data": {"disconnectConnectedAccountsLocations": {"success": True}}},
        )
        result = client.oauth_disconnect(16808, "FACEBOOK")
    assert result.get("success") is True


def test_connect_google_account(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/connect-google",
            json={"data": {"bulkConnectLinkForGoogle": {"success": True, "url": "https://connect.google"}}},
        )
        result = client.connect_google_account("https://ok.com", "https://err.com")
    assert result.get("success") is True
    assert "url" in result


def test_disconnect_google_account(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/disconnect-google",
            json={"data": {"gmbBulkDisconnect": {"success": True}}},
        )
        result = client.disconnect_google_account("acc-123")
    assert result.get("success") is True


def test_create_grid_report(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/create-grid-report",
            json={
                "data": {
                    "createGridrankReport": {
                        "data": {"reportIds": ["report-uuid-1"]},
                        "errors": None,
                    }
                }
            },
        )
        result = client.create_grid_report(
            location_id=16808,
            keywords=["italian restaurant"],
            business_name="Chianti",
            business_street="No 12",
            business_city="Bengaluru",
            business_state="Karnataka",
            business_country="India",
            latitude=12.93,
            longitude=77.61,
            distance=20,
            distance_unit="km",
            grid_size=3,
        )
    assert result.get("data", {}).get("reportIds") == ["report-uuid-1"]
    body = m.last_request.json()
    assert body["businessName"] == "Chianti"
    assert body["gridSize"] == 3


def test_fetch_grid_report(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/grid-report/report-123",
            json={"data": {"gridrankReportById": {"id": "report-123", "status": "COMPLETED"}}},
        )
        result = client.fetch_grid_report("report-123")
    assert result["id"] == "report-123"
    assert result["status"] == "COMPLETED"


def test_fetch_location_grid_reports(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.synup.com/api/v4/locations/TG9jYXRpb246MTY4MDg=/grid-reports",
            json={"data": {"allGridrankReports": {"reports": [{"id": "r1"}], "total": 1}}},
        )
        result = client.fetch_location_grid_reports(16808)
    assert result["total"] == 1
    assert len(result["reports"]) == 1
    assert result["reports"][0]["id"] == "r1"


def test_update_location(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/update",
            json={"data": {"updateLocation": {"success": True, "location": {"id": "loc1", "phone": "999"}}}},
        )
        result = client.update_location({"id": "TG9jYXRpb246MTM2OTc=", "phone": "9910991111"})
    assert result.get("success") is True
    assert m.last_request.json()["input"]["phone"] == "9910991111"


def test_archive_locations(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/archive",
            json={"data": {"archiveLocations": {"result": [{"success": True, "status": "ARCHIVED"}]}}},
        )
        result = client.archive_locations(["TG9jYXRpb246MTM5OTg="])
    assert "result" in result
    assert result["result"][0]["status"] == "ARCHIVED"


def test_create_folder(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/folders/create",
            json={"data": {"createFolder": {"success": True, "folder": {"id": "f1", "name": "franchise"}}}},
        )
        result = client.create_folder("franchise", parent_folder_name="all_franchise")
    assert result.get("success") is True
    assert result.get("folder", {}).get("name") == "franchise"


def test_add_location_tag(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/tags",
            json={"data": {"addTag": {"success": True, "tag": {"name": "New"}}}},
        )
        result = client.add_location_tag(16808, "New")
    assert result.get("success") is True
    assert m.last_request.json()["input"]["tag"] == "New"


def test_mark_listings_as_duplicate(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/listings/mark-as-duplicate",
            json={"data": {"markAsDuplicate": {"success": True}}},
        )
        result = client.mark_listings_as_duplicate(16808, ["TGlzdGluZ0l0ZW06MzMzMjkzOA=="])
    assert result.get("success") is True


def test_respond_to_review(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/reviews/respond",
            json={"data": {"respondToInteraction": {"interaction": {"interactionStatus": "Created"}}}},
        )
        result = client.respond_to_review("2090753a-ece6-4837-8336-8494ad308523", "Thank you!")
    assert "interaction" in result
    assert m.last_request.json()["responseContent"] == "Thank you!"


def test_trigger_connected_account_matches(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/trigger-matches",
            json={"data": {"connectedAccountsTriggerMatches": {"success": True}}},
        )
        result = client.trigger_connected_account_matches(["6eb312f7-df32-4d76-ad8a-26bcfeab601e"])
    assert result.get("success") is True
    assert "connectedAccountIds" in m.last_request.json()["input"]


def test_fetch_connected_account_listings(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/connected-account-listings",
            json={"data": {"connectedAccountListings": {"pageInfo": {"totalRecords": 60}, "records": [{"id": "r1", "locationName": "Trial"}]}}},
        )
        result = client.fetch_connected_account_listings("3db66afa-151d-4212-a8b7-949f9fe9aaf9", location_info="123 William")
    assert "records" in result
    assert result["records"][0]["locationName"] == "Trial"
    assert m.last_request.json()["locationInfo"] == "123 William"


def test_confirm_connected_account_matches(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/confirm-matches",
            json={"data": {"confirmConnectMatches": {"success": True}}},
        )
        result = client.confirm_connected_account_matches(["R21iTG9jYXRpb25NYXRjaGVkRGF0YTplNGZhNTFkYi04NWEwLTRjYzItYjdmMS01OWNhMzQ1NjlhZWM="])
    assert result.get("success") is True


def test_connect_listing(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/connect-listing",
            json={"data": {"connectListing": {"success": True, "message": None}}},
        )
        result = client.connect_listing(73933, "R21iQnVsa0RhdGFMYWtlOmMyMWRiOWY5LTZmYTctNDE0My1hNDU2LTQzMjZkMmZiN2UwZg==", "3db66afa-151d-4212-a8b7-949f9fe9aaf9")
    assert result.get("success") is True
    assert "locationId" in m.last_request.json()["input"]


def test_disconnect_listing(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/connected-accounts/disconnect-listing",
            json={"data": {"disconnectConnectedAccountsLocations": {"success": True}}},
        )
        result = client.disconnect_listing(16808, "GOOGLE")
    assert result.get("success") is True


def test_create_gmb_listing(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.synup.com/api/v4/locations/create/gmb-listing",
            json={"data": {"createGmbListingForLocation": {"success": True, "errors": None}}},
        )
        result = client.create_gmb_listing(14055, "bc818dc7-1576-4e50-a69d-c69d12222588", folder_id="accounts/1154433325552997863009")
    assert result.get("success") is True
    assert m.last_request.json()["input"]["folderId"] == "accounts/1154433325552997863009"
