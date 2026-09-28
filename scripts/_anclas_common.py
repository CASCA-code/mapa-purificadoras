"""Shared helpers for barrio-anchor fetch/build scripts (ZMM).

BBox = same clip as data/places_anclas_zmm.geojson metadata.clip_bbox
(colonias.geojson extent + 0.02° pad).
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PLACES_ANCLAS = os.path.join(DATA, "places_anclas_zmm.geojson")
# Fallback if places_anclas_zmm lacks metadata
DEFAULT_CLIP = (-100.6592, 25.5586, -100.0526, 25.8728)


def zmm_clip() -> tuple[float, float, float, float]:
    """(west, south, east, north)."""
    try:
        with open(PLACES_ANCLAS, encoding="utf-8") as f:
            md = json.load(f).get("metadata") or {}
        bb = md.get("clip_bbox")
        if bb and len(bb) == 4:
            return tuple(float(x) for x in bb)  # type: ignore[return-value]
    except OSError:
        pass
    return DEFAULT_CLIP


def in_clip(lon: float, lat: float, clip) -> bool:
    w, s, e, n = clip
    return w <= lon <= e and s <= lat <= n


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def haversine_m(lon1, lat1, lon2, lat2) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def point(lon: float, lat: float, props: dict) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
        "properties": props,
    }


def write_fc(path: str, features: list[dict], name: str, metadata: dict) -> None:
    fc = {"type": "FeatureCollection", "name": name, "metadata": metadata, "features": features}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def load_fc(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
