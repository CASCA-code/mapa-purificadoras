#!/usr/bin/env python3
"""Prebake OSM highway GeoJSON for scout trayecto (Escobedo / ZMM).

Usage:
  python3 scripts/prebake_roads_zmm.py

Writes data/roads_zmm.geojson. Prefer this over live Overpass in the userscript.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLONIAS = os.path.join(ROOT, "data", "colonias.geojson")
OUT = os.path.join(ROOT, "data", "roads_zmm.geojson")

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

HIGHWAY_RE = r"^(primary|secondary|tertiary|residential|unclassified|living_street|service)$"


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def point_in_poly(x, y, geom):
    if not geom:
        return False
    t = geom["type"]
    coords = geom["coordinates"]
    polys = [coords] if t == "Polygon" else (coords if t == "MultiPolygon" else [])
    for poly in polys:
        if not poly:
            continue
        if not point_in_ring(x, y, poly[0]):
            continue
        if any(point_in_ring(x, y, h) for h in poly[1:]):
            continue
        return True
    return False


def geom_bbox(geom):
    minx = miny = 1e9
    maxx = maxy = -1e9
    stack = [geom["coordinates"]]
    while stack:
        c = stack.pop()
        if isinstance(c[0], (int, float)):
            minx = min(minx, c[0])
            maxx = max(maxx, c[0])
            miny = min(miny, c[1])
            maxy = max(maxy, c[1])
        else:
            stack.extend(c)
    return minx, miny, maxx, maxy


def overpass_fetch(south, west, north, east):
    q = (
        f"[out:json][timeout:90][maxsize:67108864];\n"
        f'way["highway"~"{HIGHWAY_RE}"]({south},{west},{north},{east});\n'
        f"out geom;"
    )
    body = urllib.parse.urlencode({"data": q}).encode()
    last_err = None
    for url in MIRRORS:
        print("try", url, flush=True)
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "PurificadorasScout-prebake/1.2 (CASCA-code)",
                },
            )
            with urllib.request.urlopen(req, timeout=100) as resp:
                raw = resp.read()
            data = json.loads(raw)
            print("elements", len(data.get("elements") or []), flush=True)
            return data
        except Exception as e:
            last_err = e
            print("fail", e, flush=True)
            time.sleep(2)
    raise RuntimeError(f"Overpass failed: {last_err}")


def main():
    with open(COLONIAS) as f:
        cols = json.load(f)

    # Escobedo bbox (+ pad) — priority municipalities for Nicolás
    esc = [
        ft
        for ft in cols["features"]
        if (ft.get("properties") or {}).get("municipio") == "General Escobedo"
    ]
    if not esc:
        print("No Escobedo colonias", file=sys.stderr)
        sys.exit(1)

    minx = miny = 1e9
    maxx = maxy = -1e9
    for ft in esc:
        a, b, c, d = geom_bbox(ft["geometry"])
        minx, miny, maxx, maxy = min(minx, a), min(miny, b), max(maxx, c), max(maxy, d)
    pad = 0.01
    south, west, north, east = miny - pad, minx - pad, maxy + pad, maxx + pad
    print("bbox", south, west, north, east)

    data = overpass_fetch(south, west, north, east)

    col_meta = []
    for ft in esc:
        geom = ft["geometry"]
        a, b, c, d = geom_bbox(geom)
        col_meta.append((a, b, c, d, geom, (ft.get("properties") or {}).get("cve_col")))

    feats = []
    for el in data.get("elements") or []:
        if el.get("type") != "way" or not el.get("geometry") or len(el["geometry"]) < 2:
            continue
        tags = el.get("tags") or {}
        hw = tags.get("highway") or ""
        svc = (tags.get("service") or "").lower()
        if hw == "service" and any(x in svc for x in ("parking", "driveway")):
            continue
        coords = [[round(g["lon"], 6), round(g["lat"], 6)] for g in el["geometry"]]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        rminx, rmaxx = min(xs), max(xs)
        rminy, rmaxy = min(ys), max(ys)
        hit = False
        for a, b, c, d, geom, _cve in col_meta:
            if rmaxx < a or rminx > c or rmaxy < b or rminy > d:
                continue
            mid = coords[len(coords) // 2]
            if any(point_in_poly(lon, lat, geom) for lon, lat in (coords[0], coords[-1], mid)):
                hit = True
                break
        if not hit:
            continue
        feats.append(
            {
                "type": "Feature",
                "properties": {
                    "highway": hw,
                    "osm_id": el.get("id"),
                    "oneway": tags.get("oneway") or "",
                    "service": tags.get("service") or "",
                },
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )

    out = {
        "type": "FeatureCollection",
        "properties": {
            "source": "OSM Overpass",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": "General Escobedo highways clipped to colonia polygons",
            "bbox": [west, south, east, north],
            "n": len(feats),
            "note": "Prebaked for scout trayecto; live Overpass optional refresh",
        },
        "features": feats,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", OUT, "features", len(feats), "MB", round(os.path.getsize(OUT) / 1e6, 2))


if __name__ == "__main__":
    main()
