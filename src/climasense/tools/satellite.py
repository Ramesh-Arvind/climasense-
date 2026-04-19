"""Sentinel-2 NDVI tool — satellite vegetation stress detection for farms.

Uses Microsoft Planetary Computer STAC (free, no API key, no registration)
to query recent Sentinel-2 L2A tiles. Computes NDVI over a small buffer
around the farm GPS, compares against an observation from ~3 months prior,
and classifies the current stress level.

NDVI (Normalized Difference Vegetation Index) = (NIR - Red) / (NIR + Red).
Range: -1 to 1. Dense healthy vegetation sits in 0.6–0.9; bare soil or
severely stressed crops fall below 0.2.

This tool gives ClimaSense a remote-sensing view of the farm that complements
the farmer's own photo, detecting stress that may not yet be visible to them.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import planetary_computer as pc
import rioxarray  # noqa: F401  — registers .rio accessor on xarray
from pyproj import Transformer
from pystac_client import Client

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_COLLECTION = "sentinel-2-l2a"


def _search_items(lat: float, lon: float, start: date, end: date, cloud_max: int):
    catalog = Client.open(_STAC_URL, modifier=pc.sign_inplace)
    search = catalog.search(
        collections=[_COLLECTION],
        intersects={"type": "Point", "coordinates": [lon, lat]},
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": cloud_max}},
    )
    return list(search.items())


def _ndvi_over_buffer(item, lat: float, lon: float, buffer_m: int):
    import xarray as xr  # noqa: F401 — pulled in via rioxarray

    b04 = rioxarray.open_rasterio(item.assets["B04"].href).squeeze()
    b08 = rioxarray.open_rasterio(item.assets["B08"].href).squeeze()

    crs = b04.rio.crs
    tf = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = tf.transform(lon, lat)

    half = buffer_m
    b04_clip = b04.rio.clip_box(x - half, y - half, x + half, y + half)
    b08_clip = b08.rio.clip_box(x - half, y - half, x + half, y + half)

    red = b04_clip.astype("float32") / 10000.0
    nir = b08_clip.astype("float32") / 10000.0
    ndvi = (nir - red) / (nir + red + 1e-9)
    ndvi = ndvi.where((ndvi >= -1) & (ndvi <= 1))

    return float(ndvi.mean().values), ndvi


def _classify(ndvi_value: float):
    if ndvi_value >= 0.6:
        return "healthy", "Dense, vigorous vegetation — crops in good condition"
    if ndvi_value >= 0.4:
        return "mild_stress", "Vegetation present but below optimal — monitor closely"
    if ndvi_value >= 0.2:
        return "moderate_stress", "Sparse or stressed vegetation — significant concern"
    return "severe_stress", "Bare soil or severe stress — drought, disease, or failed crop likely"


def _trend(now: float, prior: float | None):
    if prior is None:
        return "unknown", None
    delta = now - prior
    if delta > 0.08:
        return "improving", round(delta, 3)
    if delta < -0.08:
        return "declining", round(delta, 3)
    return "stable", round(delta, 3)


def _save_ndvi_png(ndvi_arr, path: Path, title_suffix: str = ""):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arr = ndvi_arr.values if hasattr(ndvi_arr, "values") else np.asarray(ndvi_arr)
    fig, ax = plt.subplots(figsize=(4, 4), dpi=120)
    im = ax.imshow(arr, cmap="RdYlGn", vmin=-0.2, vmax=1.0)
    ax.set_title(f"Sentinel-2 NDVI{title_suffix}  mean={np.nanmean(arr):.2f}")
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="NDVI")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


@cached_tool("ndvi")
def get_vegetation_health(
    latitude: float,
    longitude: float,
    buffer_m: int = 60,
    save_image: bool = False,
    output_dir: str | None = None,
):
    """Sentinel-2 NDVI-based vegetation health for a smallholder farm.

    Finds the most recent low-cloud Sentinel-2 L2A tile covering the farm,
    computes mean NDVI over a buffer around the GPS point, and compares
    against a prior observation from ~3 months earlier. Returns a
    stress-level classification, a trend flag, and optionally saves a
    colour NDVI PNG for demo/video use.

    Args:
        latitude: Farm latitude (decimal degrees, WGS84).
        longitude: Farm longitude (decimal degrees, WGS84).
        buffer_m: Half-width of the square patch in metres.
            60 m ≈ 1.4 ha (smallholder-scale; Sentinel-2 is 10 m/pixel).
        save_image: If True, save an NDVI colour map PNG.
        output_dir: Directory for saved images (required if save_image).
    """
    today = date.today()

    recent_items = _search_items(latitude, longitude, today - timedelta(days=45), today, cloud_max=20)
    if not recent_items:
        recent_items = _search_items(latitude, longitude, today - timedelta(days=90), today, cloud_max=40)
    if not recent_items:
        return {
            "error": "No recent low-cloud Sentinel-2 imagery for this location",
            "location": {"latitude": latitude, "longitude": longitude},
        }

    best = min(recent_items, key=lambda it: it.properties.get("eo:cloud_cover", 100))
    ndvi_now, ndvi_arr = _ndvi_over_buffer(best, latitude, longitude, buffer_m)

    prior_items = _search_items(
        latitude,
        longitude,
        today - timedelta(days=120),
        today - timedelta(days=80),
        cloud_max=30,
    )
    ndvi_prior, prior_date, prior_arr = None, None, None
    if prior_items:
        prior_best = min(prior_items, key=lambda it: it.properties.get("eo:cloud_cover", 100))
        try:
            ndvi_prior, prior_arr = _ndvi_over_buffer(prior_best, latitude, longitude, buffer_m)
            prior_date = str(prior_best.datetime.date())
        except Exception as e:
            logger.warning("Prior NDVI computation failed: %s", e)

    stress_level, interpretation = _classify(ndvi_now)
    trend, delta = _trend(ndvi_now, ndvi_prior)

    result = {
        "location": {"latitude": latitude, "longitude": longitude},
        "current_ndvi": round(ndvi_now, 3),
        "current_observation_date": str(best.datetime.date()),
        "cloud_cover_pct": round(best.properties.get("eo:cloud_cover", 0), 1),
        "prior_ndvi": round(ndvi_prior, 3) if ndvi_prior is not None else None,
        "prior_observation_date": prior_date,
        "ndvi_delta": delta,
        "trend": trend,
        "stress_level": stress_level,
        "interpretation": interpretation,
        "buffer_meters": buffer_m,
        "patch_hectares": round((2 * buffer_m) ** 2 / 10_000, 2),
        "source": "Sentinel-2 L2A via Microsoft Planetary Computer",
    }

    if save_image and output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        img = out / f"ndvi_{latitude:.4f}_{longitude:.4f}_now.png"
        _save_ndvi_png(ndvi_arr, img, title_suffix=f"  {result['current_observation_date']}")
        result["ndvi_image_now"] = str(img)
        if prior_arr is not None:
            img_prior = out / f"ndvi_{latitude:.4f}_{longitude:.4f}_prior.png"
            _save_ndvi_png(prior_arr, img_prior, title_suffix=f"  {prior_date}")
            result["ndvi_image_prior"] = str(img_prior)

    return result
