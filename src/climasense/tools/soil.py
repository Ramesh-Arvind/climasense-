"""Soil analysis tools using ISRIC SoilGrids API with realistic fallback."""

import logging
import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# Realistic fallback soil data by region (used when ISRIC API is unavailable)
_FALLBACK_SOILS = {
    "east_africa": {
        "clay": {"value": 350, "unit": "g/kg"},
        "sand": {"value": 380, "unit": "g/kg"},
        "silt": {"value": 270, "unit": "g/kg"},
        "phh2o": {"value": 58, "unit": "pH*10"},
        "soc": {"value": 180, "unit": "dg/kg"},
        "nitrogen": {"value": 15, "unit": "cg/kg"},
        "cec": {"value": 220, "unit": "mmol(c)/kg"},
    },
    "west_africa": {
        "clay": {"value": 200, "unit": "g/kg"},
        "sand": {"value": 550, "unit": "g/kg"},
        "silt": {"value": 250, "unit": "g/kg"},
        "phh2o": {"value": 55, "unit": "pH*10"},
        "soc": {"value": 120, "unit": "dg/kg"},
        "nitrogen": {"value": 10, "unit": "cg/kg"},
        "cec": {"value": 150, "unit": "mmol(c)/kg"},
    },
    "south_asia": {
        "clay": {"value": 300, "unit": "g/kg"},
        "sand": {"value": 420, "unit": "g/kg"},
        "silt": {"value": 280, "unit": "g/kg"},
        "phh2o": {"value": 65, "unit": "pH*10"},
        "soc": {"value": 90, "unit": "dg/kg"},
        "nitrogen": {"value": 8, "unit": "cg/kg"},
        "cec": {"value": 180, "unit": "mmol(c)/kg"},
    },
    "default": {
        "clay": {"value": 280, "unit": "g/kg"},
        "sand": {"value": 450, "unit": "g/kg"},
        "silt": {"value": 270, "unit": "g/kg"},
        "phh2o": {"value": 60, "unit": "pH*10"},
        "soc": {"value": 140, "unit": "dg/kg"},
        "nitrogen": {"value": 12, "unit": "cg/kg"},
        "cec": {"value": 190, "unit": "mmol(c)/kg"},
    },
}


def _get_region_key(lat: float, lon: float) -> str:
    """Determine approximate region from coordinates."""
    if -12 < lat < 15 and 25 < lon < 55:
        return "east_africa"
    if -5 < lat < 20 and -20 < lon < 25:
        return "west_africa"
    if 5 < lat < 40 and 60 < lon < 100:
        return "south_asia"
    return "default"


@cached_tool("soil")
def get_soil_analysis(
    latitude: float,
    longitude: float,
    depth_cm: int = 30,
) -> dict:
    """Get soil properties for a location using ISRIC SoilGrids.

    Args:
        latitude: Latitude of the farm location.
        longitude: Longitude of the farm location.
        depth_cm: Soil depth in cm (5, 15, 30, 60, 100, 200).

    Returns:
        Dictionary with soil properties and crop suitability assessment.
    """
    # Map depth to SoilGrids depth label
    depth_map = {5: "0-5cm", 15: "5-15cm", 30: "15-30cm", 60: "30-60cm", 100: "60-100cm", 200: "100-200cm"}
    depth_label = depth_map.get(depth_cm, "15-30cm")

    properties = ["clay", "sand", "silt", "phh2o", "soc", "nitrogen", "cec"]
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": longitude,
        "lat": latitude,
        "property": properties,
        "depth": depth_label,
        "value": "mean",
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        soil = {}
        for layer in data.get("properties", {}).get("layers", []):
            prop_name = layer["name"]
            depths = layer.get("depths", [])
            if depths:
                value = depths[0].get("values", {}).get("mean")
                unit = layer.get("unit_measure", {}).get("mapped_units", "")
                soil[prop_name] = {"value": value, "unit": unit}

        # Interpret soil for agriculture
        assessment = _assess_soil_quality(soil)

        return {
            "location": {"lat": latitude, "lon": longitude},
            "depth": depth_label,
            "properties": soil,
            "assessment": assessment,
            "data_source": "ISRIC SoilGrids v2.0",
        }

    except requests.RequestException as e:
        logger.warning("ISRIC API unavailable (%s), using regional fallback data", e)
        region = _get_region_key(latitude, longitude)
        soil = _FALLBACK_SOILS[region]
        assessment = _assess_soil_quality(soil)
        return {
            "location": {"lat": latitude, "lon": longitude},
            "depth": depth_label,
            "properties": soil,
            "assessment": assessment,
            "data_source": f"Regional estimate (ISRIC API unavailable) — region: {region}",
            "note": "For precise results, take a soil sample to your local agricultural extension office.",
        }


def _assess_soil_quality(soil: dict) -> dict:
    """Interpret soil properties for agricultural suitability."""
    assessment = {"suitable_crops": [], "concerns": [], "recommendations": []}

    ph_val = soil.get("phh2o", {}).get("value")
    if ph_val is not None:
        ph = ph_val / 10  # SoilGrids returns pH * 10
        if 5.5 <= ph <= 7.5:
            assessment["ph_status"] = "optimal"
        elif ph < 5.5:
            assessment["ph_status"] = "acidic"
            assessment["concerns"].append(f"Soil pH {ph:.1f} is acidic")
            assessment["recommendations"].append("Apply agricultural lime to raise pH")
        else:
            assessment["ph_status"] = "alkaline"
            assessment["concerns"].append(f"Soil pH {ph:.1f} is alkaline")
            assessment["recommendations"].append("Apply sulfur or organic matter to lower pH")

    clay = soil.get("clay", {}).get("value")
    sand = soil.get("sand", {}).get("value")
    if clay is not None and sand is not None:
        clay_pct = clay / 10  # g/kg -> %
        sand_pct = sand / 10
        if clay_pct > 40:
            assessment["texture"] = "heavy clay"
            assessment["suitable_crops"].extend(["rice", "wheat"])
            assessment["recommendations"].append("Add organic matter to improve drainage")
        elif sand_pct > 70:
            assessment["texture"] = "sandy"
            assessment["suitable_crops"].extend(["cassava", "groundnut", "sweet potato"])
            assessment["recommendations"].append("Add compost to improve water retention")
        else:
            assessment["texture"] = "loam"
            assessment["suitable_crops"].extend(["maize", "tomato", "potato", "beans"])

    soc = soil.get("soc", {}).get("value")
    if soc is not None:
        soc_pct = soc / 100  # dg/kg -> %
        if soc_pct < 1:
            assessment["concerns"].append("Low organic carbon - soil fertility is poor")
            assessment["recommendations"].append("Apply compost, manure, or practice cover cropping")
        elif soc_pct > 3:
            assessment["recommendations"].append("Good organic matter content - maintain with crop residue retention")

    return assessment
