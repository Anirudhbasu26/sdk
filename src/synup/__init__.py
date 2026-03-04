"""Synup Python SDK."""

from synup.client import SynupClient
from synup.exceptions import SynupAPIError

__version__ = "0.3.0"
__all__ = ["SynupClient", "SynupAPIError", "__version__"]
