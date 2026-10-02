#!/usr/bin/env python3
"""Procesa OSM agua (Overpass, descargado aparte) -> v2/data/osm_agua_zmm.geojson y compara con competencia_v3 (dedupe 30 m).
Entrada: /workspace/downloads/osm_agua_zmm_raw.json. Sin red. No toca scores ni archivos existentes."""
import json, csv, math, sys
from pathlib import Path
from collections import defaultdict, Counter
from shapely.geometry import shape, Point
from shapely.prepared import prep
ROOT = Path(__file__).resolve().parent.parent
RAW = Path("/workspace/downloads/osm_agua_zmm_raw.json")
raw = json.load(open(RAW))
KX = 111320*math.cos(math.radians(25.7)); KY = 110574
def to_m(lon, lat): return ((lon+100.3)*KX, (lat-25.7)*KY)
def dist(a, b): return math.hypot(*(x-y for x, y in zip(to_m(*a), to_m(*b))))

def clasifica(t):
    n = (t.get("name") or "").lower()
    if t.get("shop") in ("water", "water_purification", "water_refill"): return "competidor", "shop=" + t["shop"]
    if t.get("vending") == "water" or (t.get("amenity") == "vending_machine" and ("agua" in n or "water" in n)): return "competidor", "vending_machine agua"
    if "purificad" in n or "garraf" in n or "agua pura" in n: return "competidor", "nombre agua purificada"
    if t.get("amenity") == "drinking_water": return "bebedero_publico", "amenity=drinking_water (grifo/fuente; NO competidor)"
    return "descartado", "nombre coincide por regex pero no es venta de agua (hielo/aqua/motel/calle)"
feats = []
for e in raw["elements"]:
    t = e.get("tags", {}); lat = e.get("lat") or e["center"]["lat"]; lon = e.get("lon") or e["center"]["lon"]
    cl, why = clasifica(t)
    feats.append({"type":"Feature","geometry":{"type":"Point","coordinates":[round(lon,6),round(lat,6)]},
                  "properties":{"osm":f"{e['type']}/{e['id']}","clase":cl,"criterio":why,"name":t.get("name",""),
                                "tags":{k:v for k,v in t.items() if k in ("amenity","shop","vending","fee","operator","brand","craft","drink:water")}}})
comp = json.load(open(ROOT/"v2/data/competencia_v3.geojson"))["features"]
cpts = [tuple(f["geometry"]["coordinates"]) for f in comp]
cols = json.load(open(ROOT/"v2/data/colonias_v3.geojson"))["features"]
meta = {r["cve_col"]: r for r in csv.DictReader(open(ROOT/"v2/data/colonias_v3.csv", encoding="utf-8"))}
cero = {r["cve_col"]: r for r in csv.DictReader(open(ROOT/"v2/data/colonias_competencia_cero.csv", encoding="utf-8"))}
# polys en metros
from shapely.ops import transform
polys = []
for f in cols:
    g = shape(f["geometry"]); gm = transform(lambda x, y, z=None: to_m(x, y), g)
    polys.append((f["properties"]["cve_col"], gm))
# el geojson de colonias no trae cve_col -> mapear por orden con csv
cve_order = [r["cve_col"] for r in csv.DictReader(open(ROOT/"v2/data/colonias_v3.csv", encoding="utf-8"))]
if "cve_col" not in cols[0]["properties"]:
    polys = [(cve_order[i], p[1]) for i, p in enumerate(polys)]
for f in feats:
    lon, lat = f["geometry"]["coordinates"]
    near = min((dist((lon, lat), c) for c in cpts), default=None)
    f["properties"]["dist_competencia_v3_m"] = round(near, 1)
    f["properties"]["nuevo_vs_v3_30m"] = bool(f["properties"]["clase"] == "competidor" and near > 30)
    x, y = to_m(lon, lat); p = Point(x, y)
    f["properties"]["colonia_poligono"] = next((meta[c]["colonia"] for c, g in polys if g.contains(p)), "")
    f["properties"]["colonias_300m"] = [meta[c]["colonia"] for c, g in polys if g.distance(p) <= 300]
    f["properties"]["cve_300m"] = [c for c, g in polys if g.distance(p) <= 300]
out = {"type":"FeatureCollection","metadata":{"fuente":"OpenStreetMap vía Overpass (overpass.private.coffee), ODbL","osm_base_timestamp":raw.get("osm3s",{}).get("timestamp_osm_base"),
       "bbox":"25.52,-100.70,25.92,-100.00","dedupe_m":30,"nota":"indicativo; OSM subcuenta negocios de agua"}, "features":feats}
json.dump(out, open(ROOT/"v2/data/osm_agua_zmm.geojson","w"), ensure_ascii=False, separators=(",",":"))
cnt = Counter(f["properties"]["clase"] for f in feats)
print("total", len(feats), dict(cnt))
comps = [f for f in feats if f["properties"]["clase"] == "competidor"]
print("competidores OSM", len(comps), "nuevos(>30 m de v3)", sum(f["properties"]["nuevo_vs_v3_30m"] for f in comps))
for f in comps:
    p = f["properties"]; print(p["osm"], p["name"], p["criterio"], "d_v3=", p["dist_competencia_v3_m"], "nuevo=", p["nuevo_vs_v3_30m"], "| en poligono:", p["colonia_poligono"], "| <=300m:", p["colonias_300m"], "| cero:", [c for c in p["cve_300m"] if c in cero])
json.dump({"n_total":len(feats),"clases":dict(cnt),"n_comp":len(comps),"n_nuevos":sum(f["properties"]["nuevo_vs_v3_30m"] for f in comps)}, open("/workspace/work/osm_resumen.json","w"))
