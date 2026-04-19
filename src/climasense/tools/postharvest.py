"""Post-harvest drying + aflatoxin risk advisor.

Combines Open-Meteo hourly forecast with published safe-storage moisture
thresholds (FAO, CIMMYT, APHLIS) and Aspergillus flavus growth conditions.
Smallholders in SSA lose 20–40 % of grain post-harvest to mould, rodents,
and mycotoxins — often more than total in-field disease loss. No public
AI advisor addresses this.

References:
- FAO X5036E — aflatoxin control in grains
- CIMMYT — affordable grain drying and aflatoxin mitigation
- APHLIS — African Postharvest Losses Information System
- IITA — Aflasafe biocontrol registered in 12 SSA countries
"""

from __future__ import annotations

from datetime import date, datetime
import logging
import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# Crop-specific safe-storage moisture thresholds (% wet basis).
# Sources: FAO X5036E, CIMMYT post-harvest guide, APHLIS methodology.
_SAFE_MOISTURE_PCT = {
    "maize": 13.0,
    "rice": 13.0,
    "wheat": 13.0,
    "sorghum": 12.0,
    "millet": 12.0,
    "groundnut": 7.0,       # stricter — oil content + A. flavus susceptibility
    "peanut": 7.0,
    "beans": 14.0,
    "cowpea": 14.0,
    "soybean": 12.0,
    "cassava": 13.0,        # for dried chips
}

# Typical harvest moisture (% wet basis) — starting point when farmer doesn't measure.
_HARVEST_MOISTURE_PCT = {
    "maize": 23.0, "rice": 22.0, "wheat": 20.0, "sorghum": 22.0,
    "millet": 20.0, "groundnut": 35.0, "peanut": 35.0,
    "beans": 18.0, "cowpea": 18.0, "soybean": 18.0, "cassava": 60.0,
}

# Countries where Aflasafe biocontrol is registered for maize / groundnut.
# Source: IITA 2025, https://www.iita.org/news-item/scaling-aflasafe-...
_AFLASAFE_COUNTRIES = {
    "nigeria", "kenya", "senegal", "burkina faso", "ghana", "malawi",
    "mozambique", "tanzania", "zambia", "rwanda", "gambia", "uganda",
}


def _fetch_hourly_forecast(lat: float, lon: float, days: int = 7) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    resp = requests.get(url, params={
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "forecast_days": days, "timezone": "auto",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()["hourly"]


def _classify_hours(hourly: dict) -> dict:
    """Bin each forecast hour into drying / risky / neutral buckets.

    Rules from FAO post-harvest guidance and A. flavus lab studies:
    - Good drying: RH < 70%, no rain, T > 20°C, wind > 1 m/s (accelerates evaporation)
    - Aflatoxin-critical: RH > 85% AND T between 25–40°C (optimal for A. flavus toxin production)
    - Rainy: precipitation > 0.1 mm/hour (stops open-air drying)
    """
    good, critical, rainy = 0, 0, 0
    for t, rh, p, w in zip(
        hourly["temperature_2m"],
        hourly["relative_humidity_2m"],
        hourly["precipitation"],
        hourly["wind_speed_10m"],
    ):
        if p is None or t is None or rh is None:
            continue
        if p > 0.1:
            rainy += 1
            continue
        if rh < 70 and t > 20 and (w or 0) > 0.5:
            good += 1
        if rh > 85 and 25 <= t <= 40:
            critical += 1
    return {"good_drying_hours": good, "aflatoxin_critical_hours": critical, "rainy_hours": rainy}


def _days_to_safe_moisture(
    start_pct: float, target_pct: float, good_drying_hours: int
) -> int | None:
    """Rough estimate of days-to-dry assuming 0.4 %/hour under good conditions.

    This rate is an ensemble from CIMMYT sun-dried maize trials and IRRI
    rice drying curves. It is an *order-of-magnitude* estimate, not precision
    engineering — farmers should verify with a moisture meter before storing.
    """
    if start_pct <= target_pct or good_drying_hours == 0:
        return 0
    pct_to_lose = start_pct - target_pct
    hours_needed = pct_to_lose / 0.4
    days_needed = hours_needed / max(good_drying_hours / 7, 1)  # good hours per day avg
    return max(1, int(round(days_needed)))


def _risk_tier(critical_hrs: int, rainy_hrs: int, good_hrs: int) -> str:
    if critical_hrs > 40 and good_hrs < 20:
        return "critical"
    if critical_hrs > 20 or rainy_hrs > 40:
        return "high"
    if critical_hrs > 10 or rainy_hrs > 20:
        return "medium"
    return "low"


def _mitigation_advice(
    crop: str, tier: str, storage_type: str, country: str | None,
    days_to_dry: int | None, critical_hrs: int,
) -> list[str]:
    advice: list[str] = []

    if tier in ("high", "critical"):
        advice.append(
            "Do NOT store grain at current moisture — mould and aflatoxin risk is high "
            f"({critical_hrs} hours of A. flavus-friendly conditions forecast this week)."
        )

    if days_to_dry and days_to_dry > 0:
        advice.append(
            f"Expect ~{days_to_dry} day(s) of active sun-drying needed before safe storage. "
            "Spread grain on tarpaulin or raised platform, turn every 2 hours during drying."
        )

    if storage_type.lower() not in ("pics", "pics_bag", "pics bag", "hermetic"):
        advice.append(
            "Use PICS hermetic triple-layer bags — suppresses O2, blocks weevils, prevents mould. "
            "Cheaper and more effective than traditional sacks or granary for >3-month storage."
        )

    if crop.lower() in ("maize", "groundnut", "peanut") and country:
        if country.lower() in _AFLASAFE_COUNTRIES:
            advice.append(
                f"Aflasafe biocontrol is registered in {country.title()}. "
                "Apply at flowering next season to displace toxic A. flavus strains in soil — "
                "reduces aflatoxin contamination by 80–90 %."
            )

    if tier == "critical":
        advice.append(
            "If drying weather does not improve in 3 days, consider selling at local "
            "wet-grain price to a licensed aggregator rather than risk total loss."
        )

    if not advice:
        advice.append("Weather window is favourable for open-air drying. Proceed as planned.")

    return advice


@cached_tool("postharvest")
def get_postharvest_risk(
    latitude: float,
    longitude: float,
    crop: str,
    harvest_date: str | None = None,
    storage_type: str = "traditional",
    current_moisture_pct: float | None = None,
    country: str | None = None,
) -> dict:
    """Assess post-harvest drying window, aflatoxin risk, and storage advice.

    Args:
        latitude: Farm latitude.
        longitude: Farm longitude.
        crop: Crop name (maize, rice, sorghum, groundnut, etc.).
        harvest_date: ISO date of harvest. Defaults to today.
        storage_type: 'traditional', 'sack', 'granary', 'pics_bag'.
        current_moisture_pct: Measured grain moisture %. If None, uses crop typical.
        country: Country for Aflasafe eligibility (optional).

    Returns:
        Risk assessment with drying plan and storage recommendations.
    """
    crop_key = crop.lower().strip()
    if crop_key not in _SAFE_MOISTURE_PCT:
        return {
            "error": f"Unknown crop: {crop}. Supported: {sorted(_SAFE_MOISTURE_PCT)}",
        }

    try:
        hourly = _fetch_hourly_forecast(latitude, longitude, days=7)
    except requests.RequestException as e:
        return {"error": f"Weather forecast unavailable: {e}"}

    bins = _classify_hours(hourly)
    tier = _risk_tier(bins["aflatoxin_critical_hours"], bins["rainy_hours"], bins["good_drying_hours"])

    target_pct = _SAFE_MOISTURE_PCT[crop_key]
    start_pct = current_moisture_pct if current_moisture_pct is not None else _HARVEST_MOISTURE_PCT.get(crop_key, 20.0)
    days_to_dry = _days_to_safe_moisture(start_pct, target_pct, bins["good_drying_hours"])

    advice = _mitigation_advice(
        crop_key, tier, storage_type, country, days_to_dry, bins["aflatoxin_critical_hours"],
    )

    return {
        "location": {"lat": latitude, "lon": longitude},
        "crop": crop_key,
        "harvest_date": harvest_date or date.today().isoformat(),
        "storage_type": storage_type,
        "target_moisture_pct": target_pct,
        "assumed_start_moisture_pct": start_pct,
        "measured_moisture_provided": current_moisture_pct is not None,
        "weather_window_7d": bins,
        "risk_tier": tier,
        "days_to_safe_storage": days_to_dry,
        "recommendations": advice,
        "data_source": "Open-Meteo hourly forecast + FAO/CIMMYT post-harvest thresholds + IITA Aflasafe registry",
    }
