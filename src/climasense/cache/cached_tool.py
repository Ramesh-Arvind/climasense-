"""Decorator to add offline caching to any ClimaSense tool."""

import functools
import logging

from climasense.cache.store import get_default_cache

logger = logging.getLogger(__name__)


def cached_tool(tool_type: str):
    """Decorator that adds offline caching to a tool function.

    Usage:
        @cached_tool("weather")
        def get_weather_forecast(latitude, longitude, days=7):
            ...

    Behavior:
        1. Try calling the real function (live API)
        2. On success: cache the result, return it
        3. On failure: serve cached data if available, with freshness label
        4. If no cache exists either: return the error
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(**kwargs):
            cache = get_default_cache()

            # Try live API first
            try:
                result = func(**kwargs)

                # Check if the result itself is an error response
                if isinstance(result, dict) and "error" in result:
                    # Tool returned an error (e.g., API 503) — try cache
                    cached = cache.get_or_stale(tool_type, **kwargs)
                    if cached:
                        logger.info("Serving cached %s data (API returned error)", tool_type)
                        return cached
                    return result

                # Success — cache it and return
                cache.put(tool_type, result, **kwargs)
                result["_cache_meta"] = {"cached": False, "source": "live_api"}
                return result

            except Exception as e:
                # API call failed — try cache
                logger.warning("%s API failed: %s — checking cache", tool_type, e)
                cached = cache.get_or_stale(tool_type, **kwargs)
                if cached:
                    logger.info("Serving cached %s data (offline fallback)", tool_type)
                    return cached

                # No cache either — return error
                return {
                    "error": f"API unavailable and no cached data: {e}",
                    "offline": True,
                }

        # Also allow calling with positional args (tools are called with **kwargs from agent)
        @functools.wraps(func)
        def flexible_wrapper(*args, **kwargs):
            # If called with positional args, convert to kwargs
            if args:
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(param_names):
                        kwargs[param_names[i]] = arg
                return wrapper(**kwargs)
            return wrapper(**kwargs)

        return flexible_wrapper

    return decorator
