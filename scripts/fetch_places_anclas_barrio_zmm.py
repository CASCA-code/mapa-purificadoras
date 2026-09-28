#!/usr/bin/env python3
"""Barrio anchors for ZMM via Places API (New) Text Search — small budget.

Usage:
  python3 scripts/fetch_places_anclas_barrio_zmm.py --dry-run
  python3 scripts/fetch_places_anclas_barrio_zmm.py [--cap 550] [--only tortilleria,parada,bienestar,elektra]

Key: same resolution as fetch_places_anclas_zmm.py (env → .env → config/maps-key.js).

Writes:
  data/places_anclas_barrio_zmm.geojson  (raw Places source)

Queries (kind ← text / includedType):
  tortilleria     "tortillería"              grid 6×5, ≤3 pages, 2×2 split once if saturated
  parada          "parada de autobús" includedType=bus_stop (strict)  grid 6×5
  banco_prestamo  "Banco del Bienestar", "Elektra"   grid 3×3
(Banco Azteca + farmacias are already in data/places_anclas_zmm.geojson — reused, not refetched.)

Cost: Text Search Pro ≈ US$32 / 1000 req (first 5k/month free). Hard cap default
550 req → worst case ≈ US$17.6. Consumed by scripts/build_anclas_barrio_zmm.py.
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

sys.path.insert(0, os.path.dirname(__file__))
from _anclas_common import DATA, in_clip, now_utc, point, write_fc, zmm_clip  # noqa: E402
from fetch_places_anclas_zmm import Budget, grid_tiles, load_key, split_rect  # noqa: E402

OUT = os.path.join(DATA, "places_anclas_barrio_zmm.geojson")
ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.location,places.types,places.primaryType,nextPageToken"
PAGE = 20
MAX_PAGES = 3

# key, kind, textQuery, includedType, grid(cols,rows), split_if_saturated
QUERIES = [
    ("tortilleria", "tortilleria", "tortillería", None, (6, 5), True),
    ("parada", "parada", "parada de autobús", "bus_stop", (6, 5), True),
    ("bienestar", "banco_prestamo", "Banco del Bienestar", None, (3, 3), False),
    ("elektra", "banco_prestamo", "Elektra", None, (3, 3), False),
]


def name_ok(key: str, name: str, types: list[str]) -> bool:
    n = (name or "").lower()
    if key == "tortilleria":
        return bool(re.search(r"tortill|nixtamal|molino", n)) and "restaurant" != (types[:1] or [""])[0]
    if key == "parada":
        return bool(set(types) & {"bus_stop", "bus_station", "transit_station"})
    if key == "bienestar":
        return "bienestar" in n and ("banco" in n or "bank" in types or "atm" in types)
    if key == "elektra":
        return "elektra" in n
    return True


def search(key, body, budget):
    budget.inc()
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELD_MASK},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e


def fetch_tile(apikey, q, rect, clip, budget, by_id, stats, fetched_at) -> bool:
    qkey, kind, text, itype, _, _ = q
    token, pages, last, had_next = None, 0, 0, False
    while pages < MAX_PAGES and not budget.hit():
        w, s, e, n = rect
        body = {
            "textQuery": text,
            "languageCode": "es",
            "regionCode": "MX",
            "pageSize": PAGE,
            "locationRestriction": {"rectangle": {"low": {"latitude": s, "longitude": w}, "high": {"latitude": n, "longitude": e}}},
        }
        if itype:
            body["includedType"] = itype
            body["strictTypeFiltering"] = True
        if token:
            body["pageToken"] = token
            time.sleep(2.0)
        else:
            time.sleep(0.08)
        try:
            resp = search(apikey, body, budget)
        except RuntimeError as ex:
            stats["errors"].append(f"{qkey}: {ex}")
            print("  ERR", ex, file=sys.stderr)
            break
        pl = resp.get("places") or []
        last = len(pl)
        pages += 1
        for p in pl:
            name = (p.get("displayName") or {}).get("text", "")
            types = list(p.get("types") or [])
            if p.get("primaryType"):
                types = [p["primaryType"]] + [t for t in types if t != p["primaryType"]]
            if not name_ok(qkey, name, types):
                stats["filtered"][qkey] += 1
                continue
            loc = p.get("location") or {}
            lat, lon = loc.get("latitude"), loc.get("longitude")
            if lat is None or not in_clip(lon, lat, clip):
                continue
            pid = (p.get("id") or "").replace("places/", "")
            if not pid or pid in by_id:
                continue
            by_id[pid] = point(
                lon,
                lat,
                {
                    "kind": kind,
                    "name": name,
                    "fuente": "places_api",
                    "place_id": pid,
                    "address": p.get("formattedAddress") or "",
                    "q": qkey,
                    "primary_type": types[0] if types else "",
                },
            )
            stats["kept"][qkey] += 1
        token = resp.get("nextPageToken")
        had_next = bool(token)
        if not token:
            break
    return pages >= MAX_PAGES and last >= PAGE and had_next


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cap", type=int, default=550)
    ap.add_argument("--only", default="")
    ap.add_argument("--grid", default="", help="override grid for selected queries, e.g. 12x10")
    ap.add_argument("--merge", action="store_true", help="keep features already in OUT (densify pass)")
    a = ap.parse_args()
    clip = zmm_clip()
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    qs = [q for q in QUERIES if not only or q[0] in only]
    if a.grid:
        gc, gr = (int(x) for x in a.grid.lower().split("x"))
        qs = [(q[0], q[1], q[2], q[3], (gc, gr), q[5]) for q in qs]
    base = sum(q[4][0] * q[4][1] for q in qs)
    print(f"clip {clip}; queries {[q[0] for q in qs]}; base tiles {base}; cap {a.cap}")
    if a.dry_run:
        return 0
    apikey = load_key()
    budget = Budget(a.cap)
    by_id: dict = {}
    prev_md: dict = {}
    if a.merge and os.path.isfile(OUT):
        prev = json.load(open(OUT, encoding="utf-8"))
        prev_md = prev.get("metadata") or {}
        for f in prev["features"]:
            by_id[f["properties"]["place_id"]] = f
    stats = {"kept": Counter(), "filtered": Counter(), "errors": [], "req_by_q": {}}
    fetched_at = now_utc()
    for q in qs:
        before = budget.n
        for tile in grid_tiles(clip, *q[4]):
            if budget.hit():
                break
            sat = fetch_tile(apikey, q, tile, clip, budget, by_id, stats, fetched_at)
            if sat and q[5]:
                for sub in split_rect(tile, 2, 2):
                    if budget.hit():
                        break
                    fetch_tile(apikey, q, sub, clip, budget, by_id, stats, fetched_at)
        stats["req_by_q"][q[0]] = budget.n - before
        print(f"→ {q[0]}: req {budget.n - before}, kept {stats['kept'][q[0]]}", flush=True)
    feats = sorted(by_id.values(), key=lambda f: (f["properties"]["kind"], f["properties"]["place_id"]))
    c = Counter(f["properties"]["kind"] for f in feats)
    write_fc(
        OUT,
        feats,
        "places_anclas_barrio_zmm",
        {
            "fuente": "places_api",
            "endpoint": ENDPOINT,
            "fetched_at": fetched_at,
            "clip_bbox": list(clip),
            "request_count": budget.n + int(prev_md.get("request_count") or 0),
            "est_cost_usd_list_price": round((budget.n + int(prev_md.get("request_count") or 0)) * 0.032, 2),
            "passes": (prev_md.get("passes") or []) + [{"at": fetched_at, "req": budget.n, "grid": a.grid or "default", "only": a.only or "all"}],
            "req_by_query": stats["req_by_q"],
            "kept_by_query": dict(stats["kept"]),
            "filtered_by_query": dict(stats["filtered"]),
            "counts_by_kind": dict(c),
            "errors": stats["errors"][:20],
        },
    )
    print(dict(c), "req", budget.n, "→", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
