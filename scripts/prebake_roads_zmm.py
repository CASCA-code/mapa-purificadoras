#!/usr/bin/env python3
"""Prebake OSM highway GeoJSON for scout trayecto (all colonias in data/colonias.geojson).

Usage:
  python3 scripts/prebake_roads_zmm.py
  python3 scripts/prebake_roads_zmm.py --muni Monterrey
  python3 scripts/prebake_roads_zmm.py --merge   # keep existing osm_ids, add missing

Writes data/roads_zmm.geojson. Prefer this over live Overpass in the userscript.
Fetches per-municipio bbox (tiled) so Overpass stays under timeout.
"""
from __future__ import annotations

import argparse
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
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HIGHWAY_RE = r"^(primary|secondary|tertiary|residential|unclassified|living_street|service)$"
PAD_DEG = 0.004  # ~400 m
MAX_TILE_SPAN = 0.08  # split large muni bboxes


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
        print("  try", url, f"bbox=({south:.4f},{west:.4f},{north:.4f},{east:.4f})", flush=True)
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "PurificadorasScout-prebake/1.3 (CASCA-code)",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
            data = json.loads(raw)
            print("  elements", len(data.get("elements") or []), flush=True)
            return data
        except Exception as e:
            last_err = e
            print("  fail", e, flush=True)
            time.sleep(2)
    raise RuntimeError(f"Overpass failed: {last_err}")


def tiles_for_bbox(minx, miny, maxx, maxy):
    """Yield (south, west, north, east) tiles, padded."""
    west = minx - PAD_DEG
    south = miny - PAD_DEG
    east = maxx + PAD_DEG
    north = maxy + PAD_DEG
    span_x = east - west
    span_y = north - south
    nx = max(1, int(span_x / MAX_TILE_SPAN) + (1 if span_x % MAX_TILE_SPAN > 1e-9 else 0))
    ny = max(1, int(span_y / MAX_TILE_SPAN) + (1 if span_y % MAX_TILE_SPAN > 1e-9 else 0))
    dx = span_x / nx
    dy = span_y / ny
    for iy in range(ny):
        for ix in range(nx):
            yield (
                south + iy * dy,
                west + ix * dx,
                south + (iy + 1) * dy,
                west + (ix + 1) * dx,
            )


def way_to_feature(el):
    if el.get("type") != "way" or not el.get("geometry") or len(el["geometry"]) < 2:
        return None
    tags = el.get("tags") or {}
    hw = tags.get("highway") or ""
    svc = (tags.get("service") or "").lower()
    if hw == "service" and any(x in svc for x in ("parking", "driveway")):
        return None
    coords = [[round(g["lon"], 6), round(g["lat"], 6)] for g in el["geometry"]]
    return {
        "type": "Feature",
        "properties": {
            "highway": hw,
            "osm_id": el.get("id"),
            "oneway": tags.get("oneway") or "",
            "service": tags.get("service") or "",
        },
        "geometry": {"type": "LineString", "coordinates": coords},
    }


def way_hits_colonias(coords, col_meta):
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    rminx, rmaxx = min(xs), max(xs)
    rminy, rmaxy = min(ys), max(ys)
    mid = coords[len(coords) // 2]
    samples = (coords[0], coords[-1], mid)
    for a, b, c, d, geom in col_meta:
        if rmaxx < a or rminx > c or rmaxy < b or rminy > d:
            continue
        if any(point_in_poly(lon, lat, geom) for lon, lat in samples):
            return True
        # edge midpoint near border: any vertex
        if any(point_in_poly(lon, lat, geom) for lon, lat in coords[:: max(1, len(coords) // 8)]):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muni", action="append", default=[], help="Limit to municipio name(s)")
    ap.add_argument("--merge", action="store_true", help="Keep existing features; add new osm_ids")
    args = ap.parse_args()

    with open(COLONIAS) as f:
        cols = json.load(f)

    features = cols["features"]
    if args.muni:
        want = {m.lower() for m in args.muni}
        features = [
            ft
            for ft in features
            if ((ft.get("properties") or {}).get("municipio") or "").lower() in want
            or any(
                w in ((ft.get("properties") or {}).get("municipio") or "").lower() for w in want
            )
        ]
        if not features:
            print("No colonias matched --muni", args.muni, file=sys.stderr)
            sys.exit(1)

    by_muni: dict[str, list] = {}
    for ft in features:
        m = (ft.get("properties") or {}).get("municipio") or "Unknown"
        by_muni.setdefault(m, []).append(ft)

    existing_feats = []
    existing_ids: set = set()
    if args.merge and os.path.exists(OUT):
        with open(OUT) as f:
            prev = json.load(f)
        existing_feats = list(prev.get("features") or [])
        for f in existing_feats:
            oid = (f.get("properties") or {}).get("osm_id")
            if oid is not None:
                existing_ids.add(oid)
        print("merge: keeping", len(existing_feats), "existing features", flush=True)

    # Build colonia meta for hit-test (scoped to selected features)
    col_meta = []
    for ft in features:
        geom = ft["geometry"]
        a, b, c, d = geom_bbox(geom)
        col_meta.append((a, b, c, d, geom))

    new_feats = []
    seen = set(existing_ids)

    for muni, fts in sorted(by_muni.items()):
        minx = miny = 1e9
        maxx = maxy = -1e9
        for ft in fts:
            a, b, c, d = geom_bbox(ft["geometry"])
            minx, miny, maxx, maxy = min(minx, a), min(miny, b), max(maxx, c), max(maxy, d)
        print(f"\n=== {muni} ({len(fts)} colonias) bbox {miny:.4f},{minx:.4f} → {maxy:.4f},{maxx:.4f}", flush=True)
        for south, west, north, east in tiles_for_bbox(minx, miny, maxx, maxy):
            try:
                data = overpass_fetch(south, west, north, east)
            except RuntimeError as e:
                print("  SKIP tile:", e, flush=True)
                continue
            for el in data.get("elements") or []:
                oid = el.get("id")
                if oid in seen:
                    continue
                feat = way_to_feature(el)
                if not feat:
                    continue
                coords = feat["geometry"]["coordinates"]
                if not way_hits_colonias(coords, col_meta):
                    continue
                seen.add(oid)
                new_feats.append(feat)
            time.sleep(1.2)

    all_feats = existing_feats + new_feats
    # Global bbox of kept features
    if all_feats:
        xs, ys = [], []
        for f in all_feats:
            for c in f["geometry"]["coordinates"]:
                xs.append(c[0])
                ys.append(c[1])
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    else:
        bbox = []

    scope = (
        "municipios: " + ", ".join(sorted(by_muni.keys()))
        if by_muni
        else "all colonias"
    )
    out = {
        "type": "FeatureCollection",
        "properties": {
            "source": "OSM Overpass",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": f"Highways clipped to colonia polygons ({scope})",
            "bbox": bbox,
            "n": len(all_feats),
            "note": "Prebaked for scout trayecto; live Overpass optional refresh",
        },
        "features": all_feats,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(
        "\nwrote",
        OUT,
        "features",
        len(all_feats),
        "(+" + str(len(new_feats)) + " new)",
        "MB",
        round(os.path.getsize(OUT) / 1e6, 2),
        flush=True,
    )


if __name__ == "__main__":
    main()
