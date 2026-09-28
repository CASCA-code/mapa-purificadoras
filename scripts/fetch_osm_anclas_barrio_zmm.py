#!/usr/bin/env python3
"""Fetch barrio anchors for ZMM from OSM Overpass (free, no key).

Usage:
  python3 scripts/fetch_osm_anclas_barrio_zmm.py

Writes:
  data/osm_anclas_barrio_zmm.geojson  (raw OSM source, one feature per node/way-center)

kinds:
  tortilleria  shop=tortilla | craft=tortilla | name~tortiller | cuisine~tortilla (shop/amenity)
  abarrotes    shop=convenience | shop=general | shop=kiosk | shop=supermarket (small, not big chains)
  deposito     shop=alcohol | shop=beverages (depósitos)
  parada       highway=bus_stop | public_transport=platform (bus) | public_transport=stop_position (bus)
  farmacia     amenity=pharmacy
  banco_prestamo amenity=bank|atm / shop with name~Azteca|Bienestar|Elektra

BBox = same clip as data/places_anclas_zmm.geojson. Consumed by
scripts/build_anclas_barrio_zmm.py (merge + dedupe → layer files).
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _anclas_common import DATA, in_clip, now_utc, point, write_fc, zmm_clip  # noqa: E402

import os

OUT = os.path.join(DATA, "osm_anclas_barrio_zmm.geojson")
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
# Big chains → not "small" supermarket / abarrotes (Oxxo etc. live in places_anclas)
BIG_CHAINS = re.compile(
    r"oxxo|7.?eleven|seven|circle ?k|six\b|modelorama|extra\b|soriana|walmart|aurrera|"
    r"heb|h-e-b|chedraui|la comer|costco|sam'?s|smart|city ?market|fresko|alsuper|"
    r"calimax|merco|mi tienda del ahorro|bodega",
    re.I,
)
BANK_RE = re.compile(r"azteca|bienestar|elektra|bansefi", re.I)


def query(clip) -> str:
    w, s, e, n = clip
    bb = f"{s},{w},{n},{e}"
    return f"""[out:json][timeout:170];
(
  nwr["shop"="tortilla"]({bb});
  nwr["craft"="tortilla"]({bb});
  nwr["name"~"tortiller|tortilla",i]["shop"]({bb});
  nwr["name"~"tortiller",i]["amenity"]({bb});
  nwr["shop"~"^(convenience|general|kiosk|supermarket|alcohol|beverages)$"]({bb});
  node["highway"="bus_stop"]({bb});
  nwr["public_transport"="platform"]({bb});
  node["public_transport"="stop_position"]["bus"="yes"]({bb});
  nwr["amenity"="pharmacy"]({bb});
  nwr["amenity"~"^(bank|atm)$"]["name"~"azteca|bienestar|bansefi",i]({bb});
  nwr["amenity"~"^(bank|atm)$"]["brand"~"azteca|bienestar",i]({bb});
  nwr["shop"]["name"~"elektra",i]({bb});
);
out center tags;"""


def fetch(q: str) -> dict:
    body = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for attempt in range(2):
        for url in MIRRORS:
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": "mapa-purificadoras/1.0"})
                with urllib.request.urlopen(req, timeout=200) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                last = e
                print(f"  mirror fail {url}: {e}", file=sys.stderr)
                time.sleep(5)
    raise SystemExit(f"Overpass failed: {last}")


def classify(t: dict) -> str | None:
    name = t.get("name", "") or ""
    brand = t.get("brand", "") or ""
    shop = t.get("shop", "")
    amen = t.get("amenity", "")
    nm = f"{name} {brand}"
    if amen in ("bank", "atm") or (shop and re.search(r"elektra", nm, re.I)):
        if BANK_RE.search(nm):
            return "banco_prestamo"
    if shop == "tortilla" or t.get("craft") == "tortilla" or re.search(r"tortiller", nm, re.I):
        return "tortilleria"
    if shop in ("tortilla",) or (shop and re.search(r"tortilla", name, re.I)):
        return "tortilleria"
    if amen == "pharmacy":
        return "farmacia"
    if t.get("highway") == "bus_stop" or t.get("public_transport") in ("platform", "stop_position"):
        # skip rail/metro platforms (Metrorrey) unless bus
        if t.get("railway") or t.get("train") == "yes" or t.get("subway") == "yes" or t.get("light_rail") == "yes":
            return None
        return "parada"
    if shop in ("alcohol", "beverages"):
        return "deposito"
    if shop in ("convenience", "general", "kiosk", "supermarket"):
        if BIG_CHAINS.search(nm):
            return None
        return "abarrotes"
    return None


def main() -> int:
    clip = zmm_clip()
    print("clip", clip)
    data = fetch(query(clip))
    els = data.get("elements") or []
    print("elements", len(els))
    feats, seen = [], set()
    from collections import Counter

    c = Counter()
    for el in els:
        key = f"{el['type']}/{el['id']}"
        if key in seen:
            continue
        seen.add(key)
        t = el.get("tags") or {}
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        if not in_clip(lon, lat, clip):
            continue
        kind = classify(t)
        if not kind:
            continue
        c[kind] += 1
        props = {"kind": kind, "name": t.get("name") or "", "fuente": "osm", "osm_id": key}
        for k in ("shop", "amenity", "highway", "public_transport", "brand", "route_ref"):
            if t.get(k):
                props[k] = t[k]
        feats.append(point(lon, lat, props))
    feats.sort(key=lambda f: (f["properties"]["kind"], f["properties"]["osm_id"]))
    write_fc(
        OUT,
        feats,
        "osm_anclas_barrio_zmm",
        {"fuente": "OSM Overpass", "fetched_at": now_utc(), "clip_bbox": list(clip), "counts_by_kind": dict(c)},
    )
    print(dict(c), "→", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
