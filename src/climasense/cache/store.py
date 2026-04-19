"""JSON-based cache store for offline API data."""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = Path(os.environ.get(
    "CLIMASENSE_CACHE_DIR",
    Path.home() / ".climasense" / "cache",
))

# Default max age per data type (seconds)
DEFAULT_TTL = {
    "weather": 6 * 3600,       # 6 hours
    "historical_weather": 7 * 86400,  # 7 days
    "market": 24 * 3600,       # 24 hours
    "soil": 30 * 86400,        # 30 days (soil doesn't change fast)
    "advisory": 7 * 86400,     # 7 days (climatology is stable)
    "disease": 30 * 86400,     # 30 days
}


def _cache_key(tool_name: str, **kwargs) -> str:
    """Generate a deterministic cache key from tool name and arguments."""
    args_str = json.dumps(kwargs, sort_keys=True, default=str)
    h = hashlib.md5(f"{tool_name}:{args_str}".encode()).hexdigest()[:12]
    return f"{tool_name}_{h}"


def _human_age(seconds: float) -> str:
    """Convert seconds to human-readable age string."""
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    days = int(seconds / 86400)
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


class CacheStore:
    """File-based cache for API responses."""

    def __init__(self, cache_dir: Path | str | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, tool_name: str, max_age: int | None = None, **kwargs) -> dict | None:
        """Retrieve cached data if fresh enough.

        Args:
            tool_name: Name of the tool (e.g., 'weather', 'market').
            max_age: Max age in seconds. If None, uses DEFAULT_TTL for tool_name.
            **kwargs: Tool arguments used to generate the cache key.

        Returns:
            Cached data dict with '_cache_meta' added, or None if no valid cache.
        """
        key = _cache_key(tool_name, **kwargs)
        path = self.cache_dir / f"{key}.json"

        if not path.exists():
            return None

        try:
            with open(path) as f:
                entry = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        cached_at = entry.get("_cached_at", 0)
        age = time.time() - cached_at

        if max_age is None:
            max_age = DEFAULT_TTL.get(tool_name, 86400)

        if age > max_age:
            logger.debug("Cache expired for %s (age: %.0fs, max: %ds)", key, age, max_age)
            return None

        data = entry.get("data", {})
        data["_cache_meta"] = {
            "cached": True,
            "cached_at": datetime.fromtimestamp(cached_at).isoformat(),
            "age_human": _human_age(age),
            "freshness": "fresh" if age < max_age / 2 else "stale",
        }
        return data

    def put(self, tool_name: str, data: dict, **kwargs) -> None:
        """Store data in cache.

        Args:
            tool_name: Name of the tool.
            data: The API response data to cache.
            **kwargs: Tool arguments used to generate the cache key.
        """
        key = _cache_key(tool_name, **kwargs)
        path = self.cache_dir / f"{key}.json"

        entry = {
            "_cached_at": time.time(),
            "_tool": tool_name,
            "_args": kwargs,
            "data": data,
        }

        try:
            with open(path, "w") as f:
                json.dump(entry, f, default=str)
            logger.debug("Cached %s -> %s", key, path)
        except OSError as e:
            logger.warning("Failed to write cache %s: %s", path, e)

    def get_or_stale(self, tool_name: str, **kwargs) -> dict | None:
        """Get cached data regardless of age (for offline fallback).

        Returns cached data even if expired, with appropriate metadata.
        """
        key = _cache_key(tool_name, **kwargs)
        path = self.cache_dir / f"{key}.json"

        if not path.exists():
            return None

        try:
            with open(path) as f:
                entry = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        cached_at = entry.get("_cached_at", 0)
        age = time.time() - cached_at
        data = entry.get("data", {})
        data["_cache_meta"] = {
            "cached": True,
            "cached_at": datetime.fromtimestamp(cached_at).isoformat(),
            "age_human": _human_age(age),
            "freshness": "offline_fallback",
            "warning": f"Data may be outdated (last updated {_human_age(age)})",
        }
        return data

    def clear(self, tool_name: str | None = None) -> int:
        """Clear cache entries. If tool_name given, only clear that tool's cache."""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            if tool_name is None or path.name.startswith(f"{tool_name}_"):
                path.unlink()
                count += 1
        return count


# Singleton
_default_cache: CacheStore | None = None


def get_default_cache() -> CacheStore:
    """Get or create the default cache store."""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheStore()
    return _default_cache
