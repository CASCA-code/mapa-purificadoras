#!/usr/bin/env python3
"""Traffic PROXY layer for billboards (v2 map): OSM road class → 1–5 index.

  python3 scripts/build_trafico_vias_v3.py [--raw roads_raw.json]

Without --raw it queries Overpass (mirrors, offline build step; the browser never calls Overpass).
Writes v2/data/trafico_vias.geojson. This is NOT a traffic count — see docs/RATING_V3.md §3.
"""
import json, os, sys, urllib.parse, urllib.request
from collections import defaultdict
from shapely.geometry import LineString, MultiLineString, shape, mapping
from shapely.ops import linemerge, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "v2", "data", "trafico_vias.geojson")
BBOX = (25.52, -100.70, 25.92, -100.00)
Q = ('[out:json][timeout:180];way["highway"~"^(motorway|trunk|primary|secondary|tertiary)(_link)?$"]'
     '(%s,%s,%s,%s);out tags geom;' % BBOX)
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]
IDX = {"motorway": 5, "trunk": 5, "primary": 4, "secondary": 3, "tertiary": 2}

def fetch():
    for m in MIRRORS:
        try:
            req = urllib.request.Request(m, data=urllib.parse.urlencode({"data": Q}).encode(), headers={"User-Agent": "mapa-purificadoras/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print(m, e, file=sys.stderr)
    sys.exit("all Overpass mirrors failed")

raw = json.load(open(sys.argv[sys.argv.index("--raw") + 1])) if "--raw" in sys.argv else fetch()
muni = unary_union([shape(f["geometry"]) for f in json.load(open(os.path.join(ROOT, "data", "muni.geojson")))["features"]]).buffer(0.005)

groups = defaultdict(list)
n_ways = 0
for el in raw["elements"]:
    if el.get("type") != "way" or "geometry" not in el: continue
    t = el.get("tags", {}); h = t.get("highway", "")
    base = h.replace("_link", ""); link = h.endswith("_link")
    if base not in IDX: continue
    i = 1 if link else IDX[base]
    coords = [(g["lon"], g["lat"]) for g in el["geometry"]]
    if len(coords) < 2: continue
    n_ways += 1
    groups[(i, base, t.get("name", ""), t.get("ref", ""))].append(LineString(coords))

feats = []
for (i, base, name, ref), lines in groups.items():
    g = linemerge(lines).intersection(muni)
    if g.is_empty: continue
    g = g.simplify(0.00005, preserve_topology=False)
    parts = list(g.geoms) if hasattr(g, "geoms") else [g]
    parts = [p for p in parts if isinstance(p, LineString) and len(p.coords) >= 2]
    if not parts: continue
    cc = [[[round(x, 5), round(y, 5)] for x, y in p.coords] for p in parts]
    geom = {"type": "LineString", "coordinates": cc[0]} if len(cc) == 1 else {"type": "MultiLineString", "coordinates": cc}
    feats.append({"type": "Feature", "geometry": geom, "properties": {"i": i, "h": base + ("_link" if i == 1 else ""), "n": name, "r": ref}})
feats.sort(key=lambda f: f["properties"]["i"])
json.dump({"type": "FeatureCollection", "features": feats}, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
print("ways", n_ways, "features", len(feats), Counter(f["properties"]["i"] for f in feats), os.path.getsize(OUT))
