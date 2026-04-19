"""Offline caching layer for ClimaSense tools.

Enables "works offline, updates when connected" behavior:
- Caches API responses locally as JSON with timestamps
- Serves cached data when APIs are unreachable
- Labels cached data with freshness ("Last updated: 2 days ago")
"""

from climasense.cache.store import CacheStore, get_default_cache

__all__ = ["CacheStore", "get_default_cache"]
