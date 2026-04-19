"""Commodity market price tools using WFP Food Prices via HDX CKAN API.

Real food price data from the World Food Programme, covering 47+ countries
including Sub-Saharan Africa and South Asia.
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from functools import lru_cache

import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# WFP HDX dataset IDs for target countries
_COUNTRY_DATASETS = {
    "kenya": "wfp-food-prices-for-kenya",
    "nigeria": "wfp-food-prices-for-nigeria",
    "ethiopia": "wfp-food-prices-for-ethiopia",
    "tanzania": "wfp-food-prices-for-tanzania",
    "uganda": "wfp-food-prices-for-uganda",
    "malawi": "wfp-food-prices-for-malawi",
    "mozambique": "wfp-food-prices-for-mozambique",
    "india": "wfp-food-prices-for-india",
    "bangladesh": "wfp-food-prices-for-bangladesh",
    "nepal": "wfp-food-prices-for-nepal",
    "pakistan": "wfp-food-prices-for-pakistan",
    "ghana": "wfp-food-prices-for-ghana",
    "senegal": "wfp-food-prices-for-senegal",
    "mali": "wfp-food-prices-for-mali",
    "niger": "wfp-food-prices-for-niger",
    "burkina faso": "wfp-food-prices-for-burkina-faso",
    "cameroon": "wfp-food-prices-for-cameroon",
    "democratic republic of congo": "wfp-food-prices-for-democratic-republic-of-congo",
    "south sudan": "wfp-food-prices-for-south-sudan",
    "somalia": "wfp-food-prices-for-somalia",
    "madagascar": "wfp-food-prices-for-madagascar",
    "zambia": "wfp-food-prices-for-zambia",
    "zimbabwe": "wfp-food-prices-for-zimbabwe",
    "rwanda": "wfp-food-prices-for-rwanda",
}

# Map common crop names to WFP commodity names
_CROP_ALIASES = {
    "maize": ["Maize", "Maize (white)", "Maize (yellow)"],
    "rice": ["Rice", "Rice (local)", "Rice (imported)"],
    "wheat": ["Wheat", "Wheat flour"],
    "sorghum": ["Sorghum", "Sorghum (white)", "Sorghum (red)"],
    "cassava": ["Cassava", "Cassava flour"],
    "beans": ["Beans", "Beans (white)", "Beans (red)"],
    "millet": ["Millet", "Millet (pearl)"],
    "cowpea": ["Cowpeas"],
    "groundnut": ["Groundnuts (shelled)"],
    "potato": ["Potatoes (Irish)"],
    "tomato": ["Tomatoes"],
}


def _get_csv_url(country: str) -> str | None:
    """Get the CSV download URL for a country's WFP food price data."""
    country_lower = country.lower().strip()
    dataset_id = _COUNTRY_DATASETS.get(country_lower)
    if not dataset_id:
        return None

    url = f"https://data.humdata.org/api/3/action/package_show?id={dataset_id}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("success"):
        resources = data["result"]["resources"]
        for r in resources:
            if r.get("format", "").upper() == "CSV":
                return r["url"]
        if resources:
            return resources[0]["url"]
    return None


@lru_cache(maxsize=8)
def _fetch_price_data(country: str) -> list[dict]:
    """Fetch and parse WFP price data for a country (cached)."""
    csv_url = _get_csv_url(country)
    if not csv_url:
        return []

    resp = requests.get(csv_url, timeout=60)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = []
    for row in reader:
        if row.get("usdprice") and row["usdprice"].strip():
            try:
                row["usdprice"] = float(row["usdprice"])
                rows.append(row)
            except (ValueError, TypeError):
                pass
    return rows


@cached_tool("market")
def get_commodity_prices(
    crop: str,
    country: str = "kenya",
) -> dict:
    """Get real commodity prices from WFP Food Price Monitoring.

    Args:
        crop: The crop name (e.g., 'maize', 'rice', 'wheat', 'beans').
        country: Country name (e.g., 'kenya', 'nigeria', 'india').

    Returns:
        Dictionary with recent prices, trend, and market data.
    """
    country_lower = country.lower().strip()
    crop_lower = crop.lower().strip()

    if country_lower not in _COUNTRY_DATASETS:
        return {
            "crop": crop,
            "country": country,
            "error": f"Country not available. Supported: {', '.join(sorted(_COUNTRY_DATASETS.keys()))}",
        }

    # Get commodity name variants
    commodity_names = _CROP_ALIASES.get(crop_lower, [crop.title()])

    try:
        all_rows = _fetch_price_data(country_lower)
    except requests.RequestException as e:
        logger.error("Failed to fetch WFP data for %s: %s", country, e)
        return {"crop": crop, "country": country, "error": f"Could not fetch price data: {e}"}

    if not all_rows:
        return {"crop": crop, "country": country, "error": "No data available for this country."}

    # Filter for the crop
    crop_rows = [r for r in all_rows if r.get("commodity") in commodity_names]
    if not crop_rows:
        available = sorted(set(r.get("commodity", "") for r in all_rows))
        return {
            "crop": crop,
            "country": country,
            "error": f"No price data for '{crop}'. Available: {', '.join(available[:20])}",
        }

    # Get recent prices (last 3 months)
    crop_rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    recent = crop_rows[:50]

    # Compute stats
    recent_prices = [r["usdprice"] for r in recent if r["usdprice"] > 0]
    if not recent_prices:
        return {"crop": crop, "country": country, "error": "No valid price entries found."}

    latest_row = recent[0]
    current_price = latest_row["usdprice"]
    avg_price = sum(recent_prices) / len(recent_prices)

    # Get prices from ~30 days ago for trend
    latest_date = latest_row.get("date", "")
    older = [r for r in crop_rows if r.get("date", "") < latest_date]
    if older:
        older_prices = [r["usdprice"] for r in older[:50] if r["usdprice"] > 0]
        if older_prices:
            old_avg = sum(older_prices) / len(older_prices)
            trend_pct = round((avg_price - old_avg) / old_avg * 100, 1)
        else:
            trend_pct = 0.0
    else:
        trend_pct = 0.0

    # Get market info
    markets = sorted(set(r.get("market", "") for r in recent if r.get("market")))

    return {
        "crop": crop,
        "country": country,
        "commodity": latest_row.get("commodity"),
        "current_price": {
            "value": round(current_price, 3),
            "unit": f"USD/{latest_row.get('unit', 'KG')}",
            "date": latest_date,
            "market": latest_row.get("market", "N/A"),
        },
        "avg_recent": round(avg_price, 3),
        "trend_pct": trend_pct,
        "trend_direction": "rising" if trend_pct > 2 else "falling" if trend_pct < -2 else "stable",
        "markets_reporting": markets[:10],
        "data_points": len(recent_prices),
        "currency": latest_row.get("currency", "N/A"),
        "local_price": float(latest_row.get("price", 0)),
        "data_source": "WFP Food Price Monitoring (via HDX)",
    }


@cached_tool("market")
def get_price_forecast(
    crop: str,
    country: str = "kenya",
    months_ahead: int = 3,
) -> dict:
    """Forecast price trends based on historical seasonal patterns.

    Args:
        crop: The crop name.
        country: Country name.
        months_ahead: Number of months to forecast (1-6).

    Returns:
        Dictionary with seasonal price analysis and sell timing advice.
    """
    crop_lower = crop.lower().strip()
    country_lower = country.lower().strip()
    months_ahead = min(max(months_ahead, 1), 6)

    commodity_names = _CROP_ALIASES.get(crop_lower, [crop.title()])

    try:
        all_rows = _fetch_price_data(country_lower)
    except requests.RequestException as e:
        return {"crop": crop, "country": country, "error": f"Could not fetch data: {e}"}

    crop_rows = [r for r in all_rows if r.get("commodity") in commodity_names]
    if not crop_rows:
        return {"crop": crop, "country": country, "error": "No data for this crop."}

    # Build monthly price averages for seasonal analysis
    monthly_prices: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for row in crop_rows:
        date_str = row.get("date", "")
        if len(date_str) >= 7:
            try:
                month = int(date_str[5:7])
                monthly_prices[month].append(row["usdprice"])
            except (ValueError, IndexError):
                pass

    # Compute seasonal averages
    seasonal_avg = {}
    for month, prices in monthly_prices.items():
        if prices:
            seasonal_avg[month] = round(sum(prices) / len(prices), 3)

    if not seasonal_avg:
        return {"crop": crop, "country": country, "error": "Insufficient historical data."}

    # Find best sell months
    current_month = datetime.now().month
    forecast_months = []
    best_month = None
    best_price = 0

    month_names = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    for i in range(1, months_ahead + 1):
        m = ((current_month - 1 + i) % 12) + 1
        avg = seasonal_avg.get(m, 0)
        forecast_months.append({
            "month": month_names[m],
            "seasonal_avg_usd": avg,
            "data_years": len(monthly_prices.get(m, [])),
        })
        if avg > best_price:
            best_price = avg
            best_month = month_names[m]

    return {
        "crop": crop,
        "country": country,
        "forecasts": forecast_months,
        "recommendation": {
            "best_sell_month": best_month,
            "expected_price_usd": best_price,
            "advice": f"Historically, {crop} prices in {country.title()} tend to peak around {best_month}.",
        },
        "data_source": "WFP historical seasonal analysis",
    }
