"""Soil analysis tools using ISRIC SoilGrids API with realistic fallback."""

import logging
import time
import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# ISRIC SoilGrids is a 250 m raster. Individual pixels sometimes return null
# due to grid/tile misalignment even when neighbouring pixels have data. The
# query function retries on a spiral of nearby pixels before falling back to
# the regional estimate. 0.0025° ≈ 280 m, just past one grid cell.
_NEIGHBOUR_OFFSETS_DEG = [
    (0.0025, 0.0), (-0.0025, 0.0), (0.0, 0.0025), (0.0, -0.0025),
    (0.0025, 0.0025), (0.0025, -0.0025), (-0.0025, 0.0025), (-0.0025, -0.0025),
    (0.005, 0.0), (-0.005, 0.0), (0.0, 0.005), (0.0, -0.005),
    (0.005, 0.005), (0.005, -0.005), (-0.005, 0.005), (-0.005, -0.005),
]

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


def _query_isric(lat: float, lon: float, depth_label: str, properties: list[str]) -> dict | None:
    """One call to the ISRIC SoilGrids API. Returns the parsed soil dict or None if all-null.

    Retries on HTTP 429 with exponential backoff (ISRIC rate-limits free users).
    """
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": properties,
        "depth": depth_label,
        "value": "mean",
    }
    for attempt in range(3):
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 429:
            wait = 2 ** attempt + 1  # 2, 3, 5 seconds
            logger.info("ISRIC rate-limited (429), waiting %ss", wait)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        resp.raise_for_status()  # final attempt failed — raise
    data = resp.json()

    soil: dict = {}
    for layer in data.get("properties", {}).get("layers", []):
        prop_name = layer["name"]
        depths = layer.get("depths", [])
        if depths:
            value = depths[0].get("values", {}).get("mean")
            unit = layer.get("unit_measure", {}).get("mapped_units", "")
            soil[prop_name] = {"value": value, "unit": unit}

    if not soil or all(v.get("value") is None for v in soil.values()):
        return None
    return soil


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
    depth_map = {5: "0-5cm", 15: "5-15cm", 30: "15-30cm", 60: "30-60cm", 100: "60-100cm", 200: "100-200cm"}
    depth_label = depth_map.get(depth_cm, "15-30cm")
    properties = ["clay", "sand", "silt", "phh2o", "soc", "nitrogen", "cec"]

    try:
        soil = _query_isric(latitude, longitude, depth_label, properties)
        used_lat, used_lon = latitude, longitude
        offset_m = 0

        # If the exact pixel is null (grid misalignment), search nearby pixels.
        # ISRIC rasters are on a 250 m grid — neighbours usually have real data.
        if soil is None:
            for dlat, dlon in _NEIGHBOUR_OFFSETS_DEG:
                near = _query_isric(latitude + dlat, longitude + dlon, depth_label, properties)
                if near is not None:
                    soil = near
                    used_lat = latitude + dlat
                    used_lon = longitude + dlon
                    offset_m = int(round(((dlat ** 2 + dlon ** 2) ** 0.5) * 111_000))
                    break

        if soil is None:
            region = _get_region_key(latitude, longitude)
            soil = _FALLBACK_SOILS[region]
            return {
                "location": {"lat": latitude, "lon": longitude},
                "depth": depth_label,
                "properties": soil,
                "assessment": _assess_soil_quality(soil),
                "data_source": f"Regional estimate (ISRIC coverage gap — no valid pixel within ~600 m) — region: {region}",
                "note": "ISRIC had no data at this point or any neighbour within ~600 m. Showing regional average.",
            }

        source = "ISRIC SoilGrids v2.0"
        if offset_m:
            source = f"ISRIC SoilGrids v2.0 (nearest valid pixel ~{offset_m} m away)"

        return {
            "location": {"lat": latitude, "lon": longitude},
            "depth": depth_label,
            "properties": soil,
            "assessment": _assess_soil_quality(soil),
            "data_source": source,
            "queried_point": {"lat": used_lat, "lon": used_lon} if offset_m else None,
        }

    except requests.RequestException as e:
        logger.warning("ISRIC API unavailable (%s) — checking persistent cache before regional fallback", e)
        from climasense.cache.store import get_default_cache
        cached = get_default_cache().get_or_stale(
            "soil", latitude=latitude, longitude=longitude, depth_cm=depth_cm
        )
        if cached:
            return cached

        region = _get_region_key(latitude, longitude)
        soil = _FALLBACK_SOILS[region]
        return {
            "location": {"lat": latitude, "lon": longitude},
            "depth": depth_label,
            "properties": soil,
            "assessment": _assess_soil_quality(soil),
            "data_source": f"Regional estimate (ISRIC API unavailable, no cache) — region: {region}",
            "note": "For precise results, take a soil sample to your local agricultural extension office.",
            "_is_fallback": True,
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
