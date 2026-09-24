#!/usr/bin/env python3
"""Fetch water purification / garrafón refill stations for ZMM via Places API (New).

Same pattern as fetch_places_prestamos_zmm.py — Text Search tiles over colonias bbox.
Soft budget ~600–1000 requests (default 800). Does not invent stations.

Usage:
  python3 scripts/fetch_places_purificadoras_zmm.py
  python3 scripts/fetch_places_purificadoras_zmm.py --dry-run
  python3 scripts/fetch_places_purificadoras_zmm.py --cap 700

Writes:
  data/places_purificadoras_zmm.geojson

Kind: purificadora_places · fuente places_api · dedupe by place_id
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLONIAS = os.path.join(ROOT, "data", "colonias.geojson")
OUT = os.path.join(ROOT, "data", "places_purificadoras_zmm.geojson")
MAPS_KEY_JS = os.path.join(ROOT, "config", "maps-key.js")
ENV_FILE = os.path.join(ROOT, ".env")

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.primaryType",
        "nextPageToken",
    ]
)

PAGE_SIZE = 20
MAX_PAGES_PER_TILE = 3
REQUEST_SOFT_CAP = 800
PAD = 0.02
GRID_COLS = 3
GRID_ROWS = 3
SLEEP_SEC = 0.08
PAGE_TOKEN_SLEEP = 2.05

KIND = "purificadora_places"

# (kind, text_query) — Spanish MX / Monterrey
QUERIES: list[tuple[str, str]] = [
    (KIND, "purificadora de agua"),
    (KIND, "recarga de garrafón"),
    (KIND, "agua purificada"),
    (KIND, "llenado de garrafón"),
    (KIND, "purificadora"),
    (KIND, "Bonafont recarga"),
    (KIND, "Ciel purificadora"),
]

OK_TOKENS = (
    "purificadora",
    "purificada",
    "purificado",
    "garrafon",
    "garrafón",
    "recarga de agua",
    "recarga agua",
    "llenado",
    "agua pura",
    "agua ultra",
    "ultra pura",
    "ultrapura",
    "agua crystal",
    "agua cristal",
    "agua acuario",
    "agua viva",
    "agua life",
    "water refill",
    "refill water",
    "water station",
    "estación de agua",
    "estacion de agua",
    "bonafont",
    "ciel",
)

REJECT_TOKENS = (
    "parque acuatico",
    "parque acuático",
    "waterpark",
    "water park",
    "alberca",
    "piscina",
    "natacion",
    "natación",
    "spa ",
    " spa",
    "laboratorio",
    "laboratorio de",
    "analisis de agua",
    "análisis de agua",
    "tratamiento de aguas",
    "planta de tratamiento",
    "aguas residuales",
    "drenaje",
    "sadm",
    "conagua",
    "hotel",
    "motel",
    "restaurante",
    "taqueria",
    "taquería",
    "oxxo",
    "farmacia",
    "hospital",
    "clinica",
    "clínica",
    "escuela",
    "iglesia",
    "gimnasio",
    "gym ",
    "lavanderia",
    "lavandería",
    "autolavado",
    "car wash",
    "tinaco",
    "bombas de agua",
    "bomba de agua",
    "pozo profundo",
    "perforacion",
    "perforación",
    "plomeria",
    "plomería",
    "fontaneria",
    "fontanería",
    "hielo",
    "ice factory",
    "embotelladora",
    "distribuidora de agua",
    "pipa de agua",
    "pipas de agua",
)


def load_key() -> str:
    for env_name in ("GOOGLE_MAPS_API_KEY", "MAPS_API_KEY", "PLACES_API_KEY"):
        v = os.environ.get(env_name, "").strip()
        if v:
            return v
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, val = line.partition("=")
                if k.strip() in ("GOOGLE_MAPS_API_KEY", "MAPS_API_KEY", "PLACES_API_KEY"):
                    val = val.strip().strip('"').strip("'")
                    if val:
                        return val
    if os.path.isfile(MAPS_KEY_JS):
        text = open(MAPS_KEY_JS, encoding="utf-8").read()
        m = re.search(r"PURIF_MAPS_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
        if m:
            return m.group(1).strip()
    raise SystemExit(
        "No API key. Set GOOGLE_MAPS_API_KEY, add .env, or keep config/maps-key.js."
    )


def norm(s: str) -> str:
    s = (s or "").lower().strip()
    for a, b in (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ü", "u"),
        ("ñ", "n"),
    ):
        s = s.replace(a, b)
    return s


def geom_bbox(geom: dict) -> tuple[float, float, float, float]:
    minx = miny = 1e9
    maxx = maxy = -1e9
    stack = [geom["coordinates"]]
    while stack:
        c = stack.pop()
        if not c:
            continue
        if isinstance(c[0], (int, float)):
            minx = min(minx, c[0])
            maxx = max(maxx, c[0])
            miny = min(miny, c[1])
            maxy = max(maxy, c[1])
        else:
            stack.extend(c)
    return minx, miny, maxx, maxy


def colonias_bbox(path: str) -> tuple[float, float, float, float]:
    with open(path, encoding="utf-8") as f:
        fc = json.load(f)
    minx = miny = 1e9
    maxx = maxy = -1e9
    for ft in fc["features"]:
        bx = geom_bbox(ft["geometry"])
        minx = min(minx, bx[0])
        miny = min(miny, bx[1])
        maxx = max(maxx, bx[2])
        maxy = max(maxy, bx[3])
    return (minx - PAD, miny - PAD, maxx + PAD, maxy + PAD)


def grid_tiles(
    rect: tuple[float, float, float, float], cols: int, rows: int
) -> list[tuple[float, float, float, float]]:
    west, south, east, north = rect
    tiles = []
    for r in range(rows):
        for c in range(cols):
            w = west + (east - west) * c / cols
            e = west + (east - west) * (c + 1) / cols
            s = south + (north - south) * r / rows
            n = south + (north - south) * (r + 1) / rows
            tiles.append((w, s, e, n))
    return tiles


def split_rect(
    rect: tuple[float, float, float, float], rows: int = 2, cols: int = 2
) -> list[tuple[float, float, float, float]]:
    return grid_tiles(rect, cols, rows)


def name_ok(query: str, name: str, types: list[str]) -> bool:
    n = (name or "").strip()
    if not n:
        return False
    n_low = n.lower()
    n_norm = norm(n)
    q = norm(query)
    tset = set(types or [])

    if any(tok in n_norm for tok in REJECT_TOKENS):
        return False
    # reject swimming / sports water
    if "swim" in n_norm or "aquatics" in n_norm:
        return False
    # reject pure delivery/distributor unless also purificadora/recarga
    if ("distribuidora" in n_norm or "distribucion" in n_norm) and not any(
        t in n_norm for t in ("purificadora", "recarga", "garrafon", "llenado")
    ):
        return False

    # Brand-focused queries
    if "bonafont" in q:
        return "bonafont" in n_norm
    if "ciel" in q:
        # Ciel brand refill / purificadora — avoid "cielo" noise already partially via brand
        if "ciel" in n_norm and "cielo" not in n_norm.replace("ciel", ""):
            return True
        return "ciel" in n_norm and any(
            t in n_norm for t in ("agua", "purific", "garrafon", "recarga")
        )

    # Generic: require water-refill-ish name tokens
    if any(tok in n_low or tok in n_norm for tok in OK_TOKENS):
        return True

    # Typed water store without clear name — rare; keep only if primary looks retail water
    if tset & {"store", "point_of_interest", "establishment"} and (
        "agua" in n_norm and ("pura" in n_norm or "cristal" in n_norm)
    ):
        return True

    return False


def place_to_feature(place: dict, fetched_at: str) -> dict | None:
    loc = place.get("location") or {}
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    if lat is None or lon is None:
        return None
    pid = place.get("id") or ""
    if pid.startswith("places/"):
        pid = pid[len("places/") :]
    dn = place.get("displayName") or {}
    name = dn.get("text") if isinstance(dn, dict) else (dn or "")
    types = list(place.get("types") or [])
    if place.get("primaryType") and place["primaryType"] not in types:
        types = [place["primaryType"]] + types
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
        "properties": {
            "name": name,
            "kind": KIND,
            "place_id": pid,
            "address": place.get("formattedAddress") or "",
            "types": types,
            "fuente": "places_api",
            "fetched_at": fetched_at,
        },
    }


class Budget:
    def __init__(self, cap: int):
        self.cap = cap
        self.n = 0

    def hit(self) -> bool:
        return self.n >= self.cap

    def inc(self) -> None:
        self.n += 1


def search_text(
    key: str,
    text_query: str,
    rect: tuple[float, float, float, float],
    page_token: str | None,
    budget: Budget,
) -> dict[str, Any]:
    if budget.hit():
        raise RuntimeError("request soft cap reached")
    west, south, east, north = rect
    body: dict[str, Any] = {
        "textQuery": text_query,
        "languageCode": "es",
        "regionCode": "MX",
        "pageSize": PAGE_SIZE,
        "locationRestriction": {
            "rectangle": {
                "low": {"latitude": south, "longitude": west},
                "high": {"latitude": north, "longitude": east},
            }
        },
    }
    if page_token:
        body["pageToken"] = page_token
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )
    budget.inc()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {err_body[:500]}") from e


def in_bbox(lon: float, lat: float, rect: tuple[float, float, float, float]) -> bool:
    west, south, east, north = rect
    return west <= lon <= east and south <= lat <= north


def fetch_tile(
    key: str,
    query: str,
    rect: tuple[float, float, float, float],
    clip: tuple[float, float, float, float],
    budget: Budget,
    by_id: dict[str, dict],
    fetched_at: str,
    stats: dict,
) -> bool:
    """Returns True if tile looked saturated."""
    token = None
    pages = 0
    last_count = 0
    had_next = False
    while pages < MAX_PAGES_PER_TILE:
        if budget.hit():
            break
        time.sleep(PAGE_TOKEN_SLEEP if token else SLEEP_SEC)
        try:
            resp = search_text(key, query, rect, token, budget)
        except RuntimeError as e:
            if "soft cap" in str(e):
                break
            stats["errors"].append(f"{query}: {e}")
            print(f"  ERROR {query}: {e}", file=sys.stderr)
            break
        places = resp.get("places") or []
        last_count = len(places)
        pages += 1
        stats["pages"] += 1
        for pl in places:
            dn = pl.get("displayName") or {}
            name = dn.get("text") if isinstance(dn, dict) else (dn or "")
            types = list(pl.get("types") or [])
            if pl.get("primaryType"):
                types = [pl["primaryType"]] + [t for t in types if t != pl["primaryType"]]
            if not name_ok(query, name, types):
                stats["filtered"] += 1
                continue
            feat = place_to_feature(pl, fetched_at)
            if not feat:
                continue
            lon, lat = feat["geometry"]["coordinates"]
            if not in_bbox(lon, lat, clip):
                stats["outside_clip"] += 1
                continue
            pid = feat["properties"]["place_id"]
            if not pid:
                continue
            if pid in by_id:
                stats["dupes"] += 1
                continue
            by_id[pid] = feat
            stats["kept"] += 1
        token = resp.get("nextPageToken")
        had_next = bool(token)
        if not token:
            break
    return pages >= MAX_PAGES_PER_TILE and last_count >= PAGE_SIZE and had_next


def fetch_query_tiles(
    key: str,
    query: str,
    tiles: list[tuple[float, float, float, float]],
    clip: tuple[float, float, float, float],
    budget: Budget,
    by_id: dict[str, dict],
    fetched_at: str,
    stats: dict,
    allow_split: bool,
) -> None:
    for tile in tiles:
        if budget.hit():
            return
        saturated = fetch_tile(
            key, query, tile, clip, budget, by_id, fetched_at, stats
        )
        if saturated and allow_split:
            for sub in split_rect(tile, 2, 2):
                if budget.hit():
                    return
                fetch_tile(key, query, sub, clip, budget, by_id, fetched_at, stats)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cap", type=int, default=REQUEST_SOFT_CAP)
    ap.add_argument("--cols", type=int, default=GRID_COLS)
    ap.add_argument("--rows", type=int, default=GRID_ROWS)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    clip = colonias_bbox(COLONIAS)
    tiles = grid_tiles(clip, args.cols, args.rows)
    queries = list(QUERIES)

    print(
        f"ZMM clip bbox: lon[{clip[0]:.4f},{clip[2]:.4f}] "
        f"lat[{clip[1]:.4f},{clip[3]:.4f}]"
    )
    print(f"Tiles: {len(tiles)} ({args.cols}×{args.rows})")
    print(f"Queries ({len(queries)}):")
    for _, q in queries:
        print(f"  {q}")

    if args.dry_run:
        est = len(tiles) * len(queries)
        print(
            f"Dry-run OK. Base requests ≥{est}; with pages/splits typically {est*2}–{est*4}."
        )
        print(f"Soft cap: {args.cap}")
        return 0

    key = load_key()
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    budget = Budget(args.cap)
    by_id: dict[str, dict] = {}
    stats = {
        "pages": 0,
        "kept": 0,
        "dupes": 0,
        "filtered": 0,
        "outside_clip": 0,
        "errors": [],
    }

    # Generic dense queries get one split pass; brand queries usually sparse
    dense_q = {
        "purificadora de agua",
        "recarga de garrafón",
        "agua purificada",
        "llenado de garrafón",
        "purificadora",
    }

    for kind, query in queries:
        if budget.hit():
            print("Soft cap reached — stopping.", file=sys.stderr)
            break
        before = budget.n
        before_kept = stats["kept"]
        print(f"→ {query} ({len(tiles)} tiles) …", flush=True)
        fetch_query_tiles(
            key,
            query,
            tiles,
            clip,
            budget,
            by_id,
            fetched_at,
            stats,
            allow_split=(query in dense_q),
        )
        print(
            f"  req +{budget.n - before} (total {budget.n}) · "
            f"new +{stats['kept'] - before_kept} · unique {len(by_id)}",
            flush=True,
        )

    features = list(by_id.values())
    features.sort(
        key=lambda f: (
            f["properties"]["name"] or "",
            f["properties"]["place_id"],
        )
    )
    by_kind = Counter(f["properties"]["kind"] for f in features)
    fc = {
        "type": "FeatureCollection",
        "name": "places_purificadoras_zmm",
        "metadata": {
            "fuente": "places_api",
            "endpoint": ENDPOINT,
            "fetched_at": fetched_at,
            "request_count": budget.n,
            "unique_places": len(features),
            "counts_by_kind": dict(sorted(by_kind.items())),
            "filtered_out": stats["filtered"],
            "dupes_skipped": stats["dupes"],
            "outside_clip": stats["outside_clip"],
            "errors": stats["errors"][:20],
            "clip_bbox": list(clip),
            "grid": [args.cols, args.rows],
            "queries": [q for _, q in queries],
            "note": "Water purification / garrafón refill — Places API Text Search; not invented",
        },
        "features": features,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")

    print("---")
    print(f"Wrote {args.out}")
    print(f"Requests: {budget.n}")
    print(f"Features: {len(features)}")
    for k, n in sorted(by_kind.items()):
        print(f"  {k}: {n}")
    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
