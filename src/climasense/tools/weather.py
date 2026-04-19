"""Weather tools using Open-Meteo API (free, no API key required)."""

import requests
from datetime import datetime, timedelta

from climasense.cache.cached_tool import cached_tool


@cached_tool("weather")
def get_weather_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
) -> dict:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the farm location.
        longitude: Longitude of the farm location.
        days: Number of forecast days (1-16).

    Returns:
        Dictionary with daily forecast including temperature, precipitation,
        wind speed, and agricultural risk indicators.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "et0_fao_evapotranspiration",
        ],
        "forecast_days": min(days, 16),
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    forecasts = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        t_max = daily["temperature_2m_max"][i]
        t_min = daily["temperature_2m_min"][i]
        precip = daily["precipitation_sum"][i]
        wind = daily["wind_speed_10m_max"][i]

        # Compute agricultural risk flags
        risks = []
        if t_min is not None and t_min <= 2:
            risks.append("FROST_RISK")
        if t_max is not None and t_max >= 40:
            risks.append("HEAT_STRESS")
        if precip is not None and precip > 50:
            risks.append("FLOOD_RISK")
        if wind is not None and wind > 60:
            risks.append("WIND_DAMAGE")
        if precip is not None and precip < 1 and i >= 4:
            risks.append("DROUGHT_CONCERN")

        forecasts.append({
            "date": date,
            "temp_max_c": t_max,
            "temp_min_c": t_min,
            "precipitation_mm": precip,
            "wind_max_kmh": wind,
            "et0_mm": daily.get("et0_fao_evapotranspiration", [None])[i],
            "risks": risks,
        })

    return {
        "location": {"lat": latitude, "lon": longitude},
        "timezone": data.get("timezone"),
        "forecasts": forecasts,
    }


@cached_tool("historical_weather")
def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Get historical weather data for climate analysis.

    Args:
        latitude: Latitude of the farm location.
        longitude: Longitude of the farm location.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Dictionary with historical daily weather data and computed statistics.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    temps_max = [t for t in daily.get("temperature_2m_max", []) if t is not None]
    temps_min = [t for t in daily.get("temperature_2m_min", []) if t is not None]
    precips = [p for p in daily.get("precipitation_sum", []) if p is not None]

    stats = {}
    if temps_max:
        stats["avg_temp_max"] = round(sum(temps_max) / len(temps_max), 1)
        stats["max_temp_recorded"] = max(temps_max)
    if temps_min:
        stats["avg_temp_min"] = round(sum(temps_min) / len(temps_min), 1)
        stats["min_temp_recorded"] = min(temps_min)
        stats["frost_days"] = sum(1 for t in temps_min if t <= 2)
    if precips:
        stats["total_precipitation_mm"] = round(sum(precips), 1)
        stats["avg_daily_precip_mm"] = round(sum(precips) / len(precips), 1)
        stats["dry_days"] = sum(1 for p in precips if p < 1)
        stats["heavy_rain_days"] = sum(1 for p in precips if p > 50)

    return {
        "location": {"lat": latitude, "lon": longitude},
        "period": {"start": start_date, "end": end_date},
        "statistics": stats,
        "daily_count": len(daily.get("time", [])),
    }
