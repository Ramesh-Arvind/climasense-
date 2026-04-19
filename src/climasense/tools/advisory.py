"""Agricultural advisory tools using NASA POWER API for data-driven planting guidance.

Uses NASA POWER (Prediction Of Worldwide Energy Resources) agroclimatology data
to generate location-specific planting calendars and climate risk alerts.
"""

import logging
from datetime import datetime

import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# Crop temperature and moisture requirements
CROP_REQUIREMENTS = {
    "maize": {
        "temp_min": 18, "temp_max": 35, "temp_opt": (25, 30),
        "water_need": "high", "gwet_min": 0.55, "precip_min": 2.5,
        "cycle_days": 120, "frost_sensitive": True,
    },
    "rice": {
        "temp_min": 20, "temp_max": 38, "temp_opt": (28, 32),
        "water_need": "very_high", "gwet_min": 0.65, "precip_min": 4.0,
        "cycle_days": 130, "frost_sensitive": True,
    },
    "wheat": {
        "temp_min": 10, "temp_max": 30, "temp_opt": (15, 22),
        "water_need": "moderate", "gwet_min": 0.45, "precip_min": 1.5,
        "cycle_days": 150, "frost_sensitive": False,
    },
    "cassava": {
        "temp_min": 20, "temp_max": 35, "temp_opt": (25, 29),
        "water_need": "moderate", "gwet_min": 0.45, "precip_min": 2.0,
        "cycle_days": 270, "frost_sensitive": True,
    },
    "sorghum": {
        "temp_min": 18, "temp_max": 40, "temp_opt": (25, 35),
        "water_need": "low", "gwet_min": 0.35, "precip_min": 1.5,
        "cycle_days": 120, "frost_sensitive": True,
    },
    "tomato": {
        "temp_min": 15, "temp_max": 35, "temp_opt": (21, 27),
        "water_need": "high", "gwet_min": 0.50, "precip_min": 2.0,
        "cycle_days": 80, "frost_sensitive": True,
    },
    "potato": {
        "temp_min": 10, "temp_max": 28, "temp_opt": (15, 20),
        "water_need": "high", "gwet_min": 0.55, "precip_min": 2.5,
        "cycle_days": 100, "frost_sensitive": True,
    },
    "beans": {
        "temp_min": 15, "temp_max": 30, "temp_opt": (18, 25),
        "water_need": "moderate", "gwet_min": 0.45, "precip_min": 2.0,
        "cycle_days": 90, "frost_sensitive": True,
    },
    "groundnut": {
        "temp_min": 20, "temp_max": 35, "temp_opt": (25, 30),
        "water_need": "moderate", "gwet_min": 0.40, "precip_min": 2.0,
        "cycle_days": 110, "frost_sensitive": True,
    },
    "millet": {
        "temp_min": 20, "temp_max": 40, "temp_opt": (28, 32),
        "water_need": "low", "gwet_min": 0.30, "precip_min": 1.0,
        "cycle_days": 90, "frost_sensitive": True,
    },
}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _fetch_climatology(latitude: float, longitude: float) -> dict | None:
    """Fetch NASA POWER monthly climatology data."""
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {
        "latitude": round(latitude, 2),
        "longitude": round(longitude, 2),
        "community": "ag",
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT",
        "format": "json",
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("properties", {}).get("parameter", {})
    except requests.RequestException as e:
        logger.error("NASA POWER API failed: %s", e)
        return None


@cached_tool("advisory")
def get_planting_advisory(
    crop: str,
    latitude: float,
    longitude: float,
    current_month: int | None = None,
) -> dict:
    """Get data-driven planting advisory based on NASA climate data.

    Args:
        crop: Crop name (e.g., 'maize', 'rice', 'cassava').
        latitude: Farm latitude.
        longitude: Farm longitude.
        current_month: Current month (1-12). Defaults to actual current month.

    Returns:
        Dictionary with optimal planting windows, harvest estimate, and management tips.
    """
    if current_month is None:
        current_month = datetime.now().month

    crop_lower = crop.lower().strip()
    if crop_lower not in CROP_REQUIREMENTS:
        return {
            "crop": crop,
            "error": f"Crop not supported. Available: {', '.join(sorted(CROP_REQUIREMENTS.keys()))}",
        }

    req = CROP_REQUIREMENTS[crop_lower]
    climate = _fetch_climatology(latitude, longitude)
    if not climate:
        return {
            "crop": crop,
            "location": {"lat": latitude, "lon": longitude},
            "error": "Could not fetch climate data from NASA POWER.",
        }

    # Analyze each month for suitability
    monthly_scores = {}
    planting_windows = []
    temp_data = climate.get("T2M", {})
    temp_max_data = climate.get("T2M_MAX", {})
    temp_min_data = climate.get("T2M_MIN", {})
    precip_data = climate.get("PRECTOTCORR", {})
    gwet_data = climate.get("GWETROOT", {})

    for i, mk in enumerate(MONTH_KEYS):
        month_num = i + 1
        t = temp_data.get(mk, 0)
        t_max = temp_max_data.get(mk, 0)
        t_min = temp_min_data.get(mk, 0)
        precip = precip_data.get(mk, 0)
        gwet = gwet_data.get(mk, 0)

        # Score: temperature suitability
        temp_ok = req["temp_min"] <= t <= req["temp_max"]
        temp_optimal = req["temp_opt"][0] <= t <= req["temp_opt"][1]

        # Score: moisture suitability
        moisture_ok = gwet >= req["gwet_min"] and precip >= req["precip_min"]

        # Frost check
        frost_risk = req["frost_sensitive"] and t_min < 5

        score = 0
        if temp_ok:
            score += 30
        if temp_optimal:
            score += 20
        if moisture_ok:
            score += 40
        if not frost_risk:
            score += 10

        monthly_scores[month_num] = {
            "month": MONTH_NAMES[month_num],
            "score": score,
            "temp_c": round(t, 1),
            "temp_max_c": round(t_max, 1),
            "temp_min_c": round(t_min, 1),
            "precip_mm_day": round(precip, 2),
            "soil_wetness": round(gwet, 3),
            "suitable": score >= 70,
            "frost_risk": frost_risk,
        }

        if score >= 70:
            planting_windows.append(month_num)

    # Find best planting month
    best_month = max(monthly_scores, key=lambda m: monthly_scores[m]["score"])

    # Find next planting window from current month
    future_windows = [m for m in planting_windows if m >= current_month]
    if not future_windows:
        future_windows = planting_windows  # wrap around
    next_plant = future_windows[0] if future_windows else best_month

    # Estimate harvest
    harvest_month = ((next_plant - 1 + (req["cycle_days"] // 30)) % 12) + 1

    in_window = current_month in planting_windows

    advisory = {
        "crop": crop,
        "location": {"lat": latitude, "lon": longitude},
        "planting_windows": [MONTH_NAMES[m] for m in planting_windows],
        "best_planting_month": MONTH_NAMES[best_month],
        "best_month_details": monthly_scores[best_month],
        "next_planting_window": MONTH_NAMES[next_plant],
        "estimated_harvest": MONTH_NAMES[harvest_month],
        "crop_cycle_days": req["cycle_days"],
        "currently_in_planting_window": in_window,
        "monthly_analysis": monthly_scores,
        "data_source": "NASA POWER Agroclimatology",
    }

    if in_window:
        details = monthly_scores[current_month]
        advisory["action"] = (
            f"NOW is a good time to plant {crop}. "
            f"Current conditions: {details['temp_c']}°C avg, {details['precip_mm_day']}mm/day rain, "
            f"soil wetness {details['soil_wetness']}. Prepare soil and sow within 2-3 weeks."
        )
    else:
        advisory["action"] = (
            f"Next planting window for {crop}: {MONTH_NAMES[next_plant]}. "
            f"Use this time to prepare soil, source seeds, and plan irrigation."
        )

    return advisory


@cached_tool("advisory")
def get_climate_risk_alert(
    latitude: float,
    longitude: float,
    crop: str,
    growth_stage: str = "vegetative",
) -> dict:
    """Generate climate risk alerts based on real NASA climate data.

    Args:
        latitude: Farm latitude.
        longitude: Farm longitude.
        crop: Current crop being grown.
        growth_stage: One of 'germination', 'vegetative', 'flowering', 'fruiting', 'maturation'.

    Returns:
        Dictionary with risk assessment and recommended actions.
    """
    crop_lower = crop.lower().strip()

    # Growth stage vulnerability mapping
    stage_vulnerabilities = {
        "germination": {
            "critical_risks": ["drought", "frost", "waterlogging"],
            "temp_range": (15, 35),
            "water_need": "moderate",
        },
        "vegetative": {
            "critical_risks": ["drought", "pest_outbreak", "nutrient_deficiency"],
            "temp_range": (18, 38),
            "water_need": "high",
        },
        "flowering": {
            "critical_risks": ["heat_stress", "drought", "heavy_rain"],
            "temp_range": (20, 35),
            "water_need": "high",
        },
        "fruiting": {
            "critical_risks": ["pest_outbreak", "disease", "hail"],
            "temp_range": (18, 36),
            "water_need": "high",
        },
        "maturation": {
            "critical_risks": ["heavy_rain", "wind_damage", "pest_outbreak"],
            "temp_range": (15, 40),
            "water_need": "low",
        },
    }

    vuln = stage_vulnerabilities.get(growth_stage, stage_vulnerabilities["vegetative"])

    # Fetch real climate data for current conditions
    climate = _fetch_climatology(latitude, longitude)
    current_month = datetime.now().month
    mk = MONTH_KEYS[current_month - 1]

    climate_context = {}
    active_risks = []
    if climate:
        t = climate.get("T2M", {}).get(mk, 0)
        t_max = climate.get("T2M_MAX", {}).get(mk, 0)
        t_min = climate.get("T2M_MIN", {}).get(mk, 0)
        precip = climate.get("PRECTOTCORR", {}).get(mk, 0)
        gwet = climate.get("GWETROOT", {}).get(mk, 0)

        climate_context = {
            "avg_temp_c": round(t, 1),
            "max_temp_c": round(t_max, 1),
            "min_temp_c": round(t_min, 1),
            "precip_mm_day": round(precip, 2),
            "soil_wetness": round(gwet, 3),
        }

        # Check actual risks
        if t_max > vuln["temp_range"][1]:
            active_risks.append(f"HEAT_STRESS: Max temp {t_max:.1f}°C exceeds {vuln['temp_range'][1]}°C limit for {growth_stage}")
        if t_min < 5 and crop_lower in CROP_REQUIREMENTS and CROP_REQUIREMENTS[crop_lower].get("frost_sensitive"):
            active_risks.append(f"FROST_RISK: Min temp {t_min:.1f}°C")
        if precip < 1.0 and vuln["water_need"] in ("high", "very_high"):
            active_risks.append(f"DROUGHT_RISK: Only {precip:.1f}mm/day rainfall, crop needs high water during {growth_stage}")
        if precip > 8.0:
            active_risks.append(f"FLOOD_RISK: Heavy rainfall {precip:.1f}mm/day may cause waterlogging")
        if gwet < 0.4 and vuln["water_need"] in ("high", "very_high"):
            active_risks.append(f"LOW_SOIL_MOISTURE: Root zone wetness {gwet:.2f} is below optimal")

    return {
        "location": {"lat": latitude, "lon": longitude},
        "crop": crop,
        "growth_stage": growth_stage,
        "current_climate": climate_context,
        "active_risks": active_risks if active_risks else ["No critical risks detected for current conditions"],
        "potential_risks_at_stage": vuln["critical_risks"],
        "optimal_temp_range_c": vuln["temp_range"],
        "water_requirement": vuln["water_need"],
        "general_advice": [
            f"Monitor {crop} closely during {growth_stage} stage",
            "Check weather forecast daily for the next 7 days",
            "Inspect plants for early signs of disease or pest damage",
            f"Ensure {'adequate irrigation' if vuln['water_need'] in ('high', 'very_high') else 'soil is not waterlogged'}",
        ],
        "data_source": "NASA POWER Agroclimatology + growth stage models",
    }
