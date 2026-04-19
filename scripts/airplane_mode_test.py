"""Airplane-mode test — the cache layer's real load-bearing claim.

The pitch says: "when Amina has no internet, ClimaSense serves cached
data with a 'last updated' label." This exercises that end-to-end:

1. Clear cache and populate it via live API calls (Amina's location).
2. Monkey-patch requests so any outbound HTTP raises ConnectionError.
3. Re-run the same tool calls — each must return a cached payload with
   _cache_meta.freshness == "offline_fallback".

We skip the LLM layer because the agent's offline behavior is entirely
delegated to the tool decorator. This is what we actually need to
validate before shipping the "offline-first" claim in the writeup.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests

from climasense.cache.store import get_default_cache
from climasense.tools import TOOL_REGISTRY

AMINA_LAT, AMINA_LON = -0.0917, 34.7680


def _kill_network():
    """Raise ConnectionError on any outbound HTTP call. Also clear in-process
    LRU caches so we actually exercise the persistent-cache path."""
    def blocked(*_a, **_kw):
        raise requests.exceptions.ConnectionError("airplane mode")

    requests.get = blocked
    requests.post = blocked
    requests.Session.get = blocked
    requests.Session.post = blocked
    requests.Session.request = blocked

    # market.py memoizes WFP data via lru_cache — clear so the offline pass
    # goes through the persistent cache, mirroring a phone reboot.
    from climasense.tools import market as _market
    try:
        _market._fetch_price_data.cache_clear()
    except AttributeError:
        pass


def _summary_line(name: str, result: dict) -> str:
    meta = result.get("_cache_meta", {})
    source = "ERROR" if "error" in result and "offline" not in result else (
        "cache" if meta.get("cached") else "live_api"
    )
    freshness = meta.get("freshness", "-")
    age = meta.get("age_human", "-")
    return f"  {name:<30} source={source:<10} freshness={freshness:<18} age={age}"


def run_pass(label: str) -> list[tuple[str, dict]]:
    calls = [
        ("weather", lambda: TOOL_REGISTRY["get_weather_forecast"](
            latitude=AMINA_LAT, longitude=AMINA_LON)),
        ("soil", lambda: TOOL_REGISTRY["get_soil_analysis"](
            latitude=AMINA_LAT, longitude=AMINA_LON)),
        ("market", lambda: TOOL_REGISTRY["get_commodity_prices"](
            crop="maize", country="kenya")),
        ("advisory", lambda: TOOL_REGISTRY["get_planting_advisory"](
            crop="maize", latitude=AMINA_LAT, longitude=AMINA_LON)),
    ]
    print(f"\n=== {label} ===")
    results = []
    for name, fn in calls:
        result = fn()
        print(_summary_line(name, result))
        results.append((name, result))
    return results


def main():
    cache = get_default_cache()
    print(f"Cache dir: {cache.cache_dir}")

    print("\nStep 1: clearing cache to force a cold state")
    removed = cache.clear()
    print(f"  removed {removed} cache files")

    print("\nStep 2: ONLINE — populate the cache from live APIs")
    online_results = run_pass("ONLINE PASS")
    for name, r in online_results:
        assert "_cache_meta" in r, f"{name} missing _cache_meta on online path"
        assert r["_cache_meta"].get("source") == "live_api" or r["_cache_meta"].get("cached") is False, \
            f"{name} online pass cached flag wrong: {r['_cache_meta']}"

    print("\nStep 3: cutting the network (raising ConnectionError on requests.*)")
    _kill_network()

    print("\nStep 4: OFFLINE — same calls must come from cache")
    offline_results = run_pass("OFFLINE PASS")

    failures = []
    for name, r in offline_results:
        meta = r.get("_cache_meta", {})
        if not meta.get("cached"):
            failures.append(f"{name}: not served from cache ({r.get('error', 'no error msg')})")
            continue
        if meta.get("freshness") != "offline_fallback":
            failures.append(f"{name}: freshness is {meta.get('freshness')!r}, expected offline_fallback")

    print("\n=== RESULT ===")
    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS: every tool served cached data with offline_fallback freshness label.")

    print("\nSample offline payload (weather):")
    weather = next(r for n, r in offline_results if n == "weather")
    meta = weather["_cache_meta"]
    print(f"  cached_at: {meta.get('cached_at')}")
    print(f"  age:       {meta.get('age_human')}")
    print(f"  warning:   {meta.get('warning')}")
    print(f"  first forecast date: {weather['forecasts'][0]['date']} ({weather['forecasts'][0]['temp_max_c']}°C max)")


if __name__ == "__main__":
    main()
