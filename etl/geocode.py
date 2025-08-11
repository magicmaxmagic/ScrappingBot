from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "geocache.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

USER_AGENT = "ai-scraper/0.1 (contact: ops@example.com)"


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache))


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    if not address:
        return None
    cache = _load_cache()
    if address in cache:
        lat, lon = cache[address]
        return float(lat), float(lon)

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                lat = float(data[0]["lat"])  # type: ignore[index]
                lon = float(data[0]["lon"])  # type: ignore[index]
                cache[address] = [lat, lon]
                _save_cache(cache)
                time.sleep(1)  # polite rate limiting
                return lat, lon
    except Exception:
        return None
    return None


# Simple point-in-polygon using ray casting

def point_in_polygon(lat: float, lon: float, polygon: list[list[float]]) -> bool:
    x, y = lon, lat
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i][0], polygon[i][1]
        x2, y2 = polygon[(i + 1) % n][0], polygon[(i + 1) % n][1]
        cond = (y1 > y) != (y2 > y)
        if cond:
            x_intersect = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1
            if x < x_intersect:
                inside = not inside
    return inside


def neighborhood_from_geojson(lat: float, lon: float, geojson_path: str) -> Optional[str]:
    try:
        gj = json.loads(Path(geojson_path).read_text())
    except Exception:
        return None
    for feat in gj.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") == "Polygon":
            for ring in geom.get("coordinates", []):
                if point_in_polygon(lat, lon, [[pt[0], pt[1]] for pt in ring]):
                    return feat.get("properties", {}).get("name")
        elif geom.get("type") == "MultiPolygon":
            for poly in geom.get("coordinates", []):
                for ring in poly:
                    if point_in_polygon(lat, lon, [[pt[0], pt[1]] for pt in ring]):
                        return feat.get("properties", {}).get("name")
    return None
