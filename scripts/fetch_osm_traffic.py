#!/usr/bin/env python3
"""Fetch OSM traffic_signals + stop/give_way for ZMM → GeoJSON layers.

Usage:
  python3 scripts/fetch_osm_traffic.py

Writes:
  data/semaforos_zmm.geojson  (highway=traffic_signals)
  data/stops_zmm.geojson      (highway=stop + give_way)

BBox: extent of data/colonias.geojson (+ pad) — scored ZMM metro.
(Roads prebake uses Escobedo-only; this layer intentionally covers full ZMM.)

Retries Overpass mirrors; tiles stop queries on 504; hard per-request timeout.
No Google billing.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLONIAS = os.path.join(ROOT, "data", "colonias.geojson")
OUT_SEMA = os.path.join(ROOT, "data", "semaforos_zmm.geojson")
OUT_STOP = os.path.join(ROOT, "data", "stops_zmm.geojson")

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

REQUEST_TIMEOUT = 90
OVERPASS_TIMEOUT = 60
PAD = 0.015
TILE_ROWS = 3
TILE_COLS = 3
TILE_RETRIES = 3


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


def zmm_bbox():
    with open(COLONIAS) as f:
        cols = json.load(f)
    minx = miny = 1e9
    maxx = maxy = -1e9
    for ft in cols.get("features") or []:
        geom = ft.get("geometry")
        if not geom:
            continue
        a, b, c, d = geom_bbox(geom)
        minx, miny, maxx, maxy = min(minx, a), min(miny, b), max(maxx, c), max(maxy, d)
    if minx > maxx:
        raise RuntimeError("colonias.geojson has no usable geometry")
    return miny - PAD, minx - PAD, maxy + PAD, maxx + PAD


def overpass_fetch(query: str):
    body = urllib.parse.urlencode({"data": query}).encode()
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
                    "User-Agent": "PurificadorasMapa-traffic/1.0 (CASCA-code)",
                },
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()
            data = json.loads(raw)
            print("elements", len(data.get("elements") or []), flush=True)
            return data
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as e:
            last_err = e
            print("fail", e, flush=True)
            time.sleep(2)
        except Exception as e:
            last_err = e
            print("fail", e, flush=True)
            time.sleep(2)
    raise RuntimeError(f"Overpass failed after {len(MIRRORS)} mirrors: {last_err}")


def feature_from_el(el):
    if "lat" in el and "lon" in el:
        lon, lat = float(el["lon"]), float(el["lat"])
    else:
        center = el.get("center") or {}
        if "lat" not in center or "lon" not in center:
            return None
        lon, lat = float(center["lon"]), float(center["lat"])
    tags = el.get("tags") or {}
    hw = tags.get("highway") or ""
    osm_type = el.get("type") or "node"
    osm_id = el.get("id")
    props = {
        "highway": hw,
        "fuente": "osm",
        "osm_id": f"{osm_type}/{osm_id}" if osm_id is not None else None,
    }
    if tags.get("name"):
        props["name"] = tags["name"]
    return {
        "type": "Feature",
        "properties": props,
        "geometry": {
            "type": "Point",
            "coordinates": [round(lon, 6), round(lat, 6)],
        },
    }


def collect(elements, allow_hw, seen):
    feats = []
    for el in elements or []:
        ft = feature_from_el(el)
        if not ft:
            continue
        hw = ft["properties"].get("highway") or ""
        if hw not in allow_hw:
            continue
        key = ft["properties"].get("osm_id")
        if key in seen:
            continue
        seen.add(key)
        feats.append(ft)
    return feats


def write_fc(path, feats, scope, bbox_wsen):
    out = {
        "type": "FeatureCollection",
        "properties": {
            "source": "OSM Overpass",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": scope,
            "bbox": list(bbox_wsen),
            "n": len(feats),
            "note": "Capa gratuita OSM; cobertura incompleta. Scout S sigue para marcas manuales.",
        },
        "features": feats,
    }
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    kb = round(os.path.getsize(path) / 1e3, 1)
    print("wrote", path, "features", len(feats), "KB", kb)


def tile_boxes(south, west, north, east, rows, cols):
    boxes = []
    for i in range(rows):
        for j in range(cols):
            ts = south + (north - south) * i / rows
            tn = south + (north - south) * (i + 1) / rows
            tw = west + (east - west) * j / cols
            te = west + (east - west) * (j + 1) / cols
            boxes.append((ts, tw, tn, te))
    return boxes


def fetch_signals(south, west, north, east):
    q = (
        f"[out:json][timeout:{OVERPASS_TIMEOUT}];\n"
        f'node["highway"="traffic_signals"]({south},{west},{north},{east});\n'
        f"out;"
    )
    data = overpass_fetch(q)
    return collect(data.get("elements"), {"traffic_signals"}, set())


def fetch_stops_tiled(south, west, north, east):
    seen = set()
    feats = []
    boxes = tile_boxes(south, west, north, east, TILE_ROWS, TILE_COLS)
    for idx, (ts, tw, tn, te) in enumerate(boxes):
        print(f"tile {idx + 1}/{len(boxes)}", round(ts, 4), round(tw, 4), round(tn, 4), round(te, 4), flush=True)
        q = (
            f"[out:json][timeout:45];\n"
            f"(\n"
            f'  node["highway"="stop"]({ts},{tw},{tn},{te});\n'
            f'  node["highway"="give_way"]({ts},{tw},{tn},{te});\n'
            f");\nout;"
        )
        data = None
        for attempt in range(TILE_RETRIES):
            try:
                time.sleep(1.5 if attempt == 0 else 3)
                data = overpass_fetch(q)
                break
            except Exception as e:
                print("tile fail attempt", attempt + 1, e, flush=True)
        if data is None:
            print("SKIP tile", idx + 1, flush=True)
            continue
        chunk = collect(data.get("elements"), {"stop", "give_way"}, seen)
        feats.extend(chunk)
        print(" +", len(chunk), "total", len(feats), flush=True)
    return feats


def main():
    south, west, north, east = zmm_bbox()
    print("bbox", south, west, north, east, flush=True)
    bbox_wsen = [west, south, east, north]

    print("=== traffic_signals ===", flush=True)
    sema = fetch_signals(south, west, north, east)
    print("semaforos", len(sema), flush=True)

    print("=== stop / give_way (tiled) ===", flush=True)
    stops = fetch_stops_tiled(south, west, north, east)
    print("stops", len(stops), flush=True)

    write_fc(
        OUT_SEMA,
        sema,
        "ZMM highway=traffic_signals (colonias bbox + pad)",
        bbox_wsen,
    )
    write_fc(
        OUT_STOP,
        stops,
        "ZMM highway=stop|give_way (colonias bbox + pad)",
        bbox_wsen,
    )
    print("done semaforos", len(sema), "stops", len(stops))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
