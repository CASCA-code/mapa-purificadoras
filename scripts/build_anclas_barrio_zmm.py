#!/usr/bin/env python3
"""Merge + dedupe barrio anchors (DENUE + Places + OSM) → one static GeoJSON per map layer.

Usage (after the three fetchers):
  python3 scripts/fetch_denue_anclas_barrio_zmm.py
  python3 scripts/fetch_osm_anclas_barrio_zmm.py
  python3 scripts/fetch_places_anclas_barrio_zmm.py
  python3 scripts/build_anclas_barrio_zmm.py

Inputs (data/):
  denue_anclas_barrio_zmm.geojson   (gitignored — regenerate, free)
  osm_anclas_barrio_zmm.geojson
  places_anclas_barrio_zmm.geojson
  places_anclas_zmm.geojson  (existing: farmacia + banco Azteca — painted by the map already)
  retail.geojson             (existing OSM retail: banco_azteca / banco_bienestar)

Outputs (data/, read by index.html — no live API calls):
  anclas_tortillerias_zmm.geojson     DENUE 311830 > Places "tortillería" > OSM     dedupe 30 m
  anclas_abarrotes_zmm.geojson        DENUE 461110/462112 + 461211/461212 > OSM       dedupe 30 m
  anclas_paradas_zmm.geojson          OSM bus_stop/platform > Places bus_stop         dedupe 20 m
  anclas_farmacias_barrio_zmm.geojson EXTRAS only: DENUE 464111 > OSM pharmacy not within 30 m of
                                      an existing places_anclas farmacia (map merges both under one toggle)
  anclas_bancos_prestamo_zmm.geojson  EXTRAS only: Places Bienestar/Elektra > DENUE > OSM (Azteca/
                                      Bienestar/Elektra) not within 30 m of existing places banco /
                                      retail banco_* (map merges both under one toggle)

Dedupe rule: CROSS-source only. A lower-priority source point within R of a kept point from a
different source is absorbed (its source is appended to `s`). Two points from the SAME source are
never merged (two DENUE tienditas 25 m apart = two real shops).

Compact props: n=name, s=sources ("denue,places"), t=subtype.
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from _anclas_common import DATA, haversine_m, load_fc, now_utc, write_fc, zmm_clip  # noqa: E402

SRC = {
    "denue": os.path.join(DATA, "denue_anclas_barrio_zmm.geojson"),
    "osm": os.path.join(DATA, "osm_anclas_barrio_zmm.geojson"),
    "places": os.path.join(DATA, "places_anclas_barrio_zmm.geojson"),
}


class Grid:
    def __init__(self, r_m: float):
        self.r = r_m
        self.cell = r_m / 111_000.0
        self.g: dict[tuple[int, int], list[dict]] = defaultdict(list)

    def _k(self, lon, lat):
        return (int(math.floor(lon / self.cell)), int(math.floor(lat / self.cell)))

    def near(self, lon, lat, other_than: str | None = None):
        kx, ky = self._k(lon, lat)
        best, bd = None, 1e18
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for it in self.g.get((kx + dx, ky + dy), ()):
                    if other_than is not None and it["src0"] == other_than:
                        continue
                    d = haversine_m(lon, lat, it["lon"], it["lat"])
                    if d <= self.r and d < bd:
                        best, bd = it, d
        return best

    def add(self, it):
        self.g[self._k(it["lon"], it["lat"])].append(it)


def feats(src: str, kinds: set[str]):
    fc = load_fc(SRC[src])
    for f in fc["features"]:
        p = f["properties"]
        if p.get("kind") in kinds:
            lon, lat = f["geometry"]["coordinates"]
            yield lon, lat, p


def sub_of(src, p):
    if src == "denue":
        return {"311830": "tortilleria", "461110": "abarrotes", "462112": "minisuper",
                "461211": "vinos_licores", "461212": "deposito_cerveza", "464111": "farmacia"}.get(
            p.get("scian"), p.get("sub", ""))
    if src == "osm":
        return p.get("shop") or p.get("amenity") or p.get("highway") or p.get("public_transport") or ""
    return p.get("primary_type") or p.get("q") or ""


def bank_sub(name: str) -> str:
    n = name.lower()
    if "bienestar" in n or "bansefi" in n:
        return "bienestar"
    if "elektra" in n:
        return "elektra"
    return "azteca"


def build(layer, spec, radius, seeds=None):
    """spec: list of (src, kinds). seeds: points that absorb but aren't emitted."""
    grid = Grid(radius)
    raw, absorbed_by_seed = Counter(), 0
    out = []
    for lon, lat, label in seeds or []:
        grid.add({"lon": lon, "lat": lat, "src0": "seed", "seed": True, "s": [label]})
    for src, kinds in spec:
        for lon, lat, p in feats(src, kinds):
            raw[src] += 1
            hit = grid.near(lon, lat, other_than=src)
            if hit:
                if hit.get("seed"):
                    absorbed_by_seed += 1
                elif src not in hit["s"]:
                    hit["s"].append(src)
                continue
            name = (p.get("name") or "").strip()[:70]
            t = sub_of(src, p)
            if layer == "bancos_prestamo":
                t = bank_sub(name + " " + (p.get("sub") or ""))
            it = {"lon": lon, "lat": lat, "src0": src, "s": [src], "n": name, "t": t}
            grid.add(it)
            out.append(it)
    features = []
    for it in out:
        props = {"n": it["n"], "s": ",".join(it["s"]), "t": it["t"]}
        features.append({"type": "Feature", "geometry": {"type": "Point",
                         "coordinates": [round(it["lon"], 6), round(it["lat"], 6)]}, "properties": props})
    kept_by_src = Counter(it["src0"] for it in out)
    multi = sum(1 for it in out if len(it["s"]) > 1)
    md = {
        "layer": layer,
        "built_at": now_utc(),
        "clip_bbox": list(zmm_clip()),
        "dedupe_m": radius,
        "dedupe_rule": "cross-source only; priority = order of sources",
        "sources_priority": [s for s, _ in spec],
        "raw_by_source": dict(raw),
        "kept_by_primary_source": dict(kept_by_src),
        "confirmed_by_2plus_sources": multi,
        "absorbed_by_existing_layer": absorbed_by_seed,
        "n": len(features),
        "by_subtype": dict(Counter(it["t"] for it in out).most_common()),
    }
    path = os.path.join(DATA, f"anclas_{layer}_zmm.geojson")
    write_fc(path, features, f"anclas_{layer}_zmm", md)
    print(f"{layer}: n={len(features)} raw={dict(raw)} kept={dict(kept_by_src)} 2+src={multi} seed_absorbed={absorbed_by_seed}")
    return md


def main() -> int:
    pa = load_fc(os.path.join(DATA, "places_anclas_zmm.geojson"))["features"]
    retail = load_fc(os.path.join(DATA, "retail.geojson"))["features"]
    farm_seed = [(*f["geometry"]["coordinates"], "places_anclas") for f in pa if f["properties"].get("kind") == "farmacia"]
    bank_seed = [(*f["geometry"]["coordinates"], "places_anclas") for f in pa if f["properties"].get("kind") == "banco"]
    bank_seed += [(*f["geometry"]["coordinates"], "osm_retail") for f in retail
                  if (f["properties"].get("subtipo") or "").startswith("banco_")]

    mani = {}
    mani["tortillerias"] = build("tortillerias", [("denue", {"tortilleria"}), ("places", {"tortilleria"}), ("osm", {"tortilleria"})], 30)
    mani["abarrotes"] = build("abarrotes", [("denue", {"abarrotes", "deposito"}), ("osm", {"abarrotes", "deposito"})], 30)
    mani["paradas"] = build("paradas", [("osm", {"parada"}), ("places", {"parada"})], 20)
    md_f = md = build("farmacias_barrio", [("denue", {"farmacia"}), ("osm", {"farmacia"})], 30, seeds=farm_seed)
    print("  + existing places_anclas farmacia (painted by map):", len(farm_seed), "→ layer total ≈", len(farm_seed) + md["n"])
    md = build("bancos_prestamo", [("places", {"banco_prestamo"}), ("denue", {"banco_prestamo"}), ("osm", {"banco_prestamo"})], 30, seeds=bank_seed)
    print("  + existing banco seeds (places Azteca + OSM retail):", len(bank_seed), "→ layer total ≈", len(bank_seed) + md["n"])
    mani["farmacias_barrio"] = md_f
    mani["bancos_prestamo"] = md
    small = {k: {"n": v["n"], "raw_by_source": v["raw_by_source"], "dedupe_m": v["dedupe_m"],
                 "file": f"data/anclas_{k}_zmm.geojson"} for k, v in mani.items()}
    import json
    with open(os.path.join(DATA, "anclas_barrio_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"built_at": now_utc(), "layers": small}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
