"""Exceptions raised by the Synup SDK. All errors are descriptive and actionable."""

from __future__ import annotations


class SynupAPIError(Exception):
    """Raised when the API returns a non-2xx response. Use status_code and response_body to handle or display.

    Attributes:
        status_code: HTTP status (e.g. 401, 404, 500). Use to branch: 401 → check API key; 404 → resource missing; 5xx → retry or contact support.
        response_body: Raw response text from the API; often JSON with an error message or validation details.

    Example:
        try:
            client.fetch_all_locations()
        except SynupAPIError as e:
            if e.status_code == 401:
                print("Invalid or missing API key. Check Settings → Integrations.")
            else:
                print(f"Request failed: {e.status_code} — {e.response_body}")
    """

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)
