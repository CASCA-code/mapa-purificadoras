#!/usr/bin/env python3
"""Grid 100 m: n competidores <=300 m del centro de celda (competencia_v3 + OSM agua nuevos >30 m). Sin red.
Celdas emitidas: count>0 o centro dentro de polígono de colonia (+300 m) (para ver los ceros). Salida: v2/data/heat_competencia_300m.csv"""
import json, csv, math
from pathlib import Path
import numpy as np
from shapely.geometry import shape, Point
from shapely.ops import transform, unary_union
from shapely.prepared import prep
from shapely import contains_xy
ROOT = Path(__file__).resolve().parent.parent
LAT0, LON0 = 25.7, -100.3
KX = 111320*math.cos(math.radians(LAT0)); KY = 110574
to_m = lambda lon, lat: ((lon-LON0)*KX, (lat-LAT0)*KY)
comp = [(f["geometry"]["coordinates"], "v3") for f in json.load(open(ROOT/"v2/data/competencia_v3.geojson"))["features"]]
osm = [(f["geometry"]["coordinates"], "osm") for f in json.load(open(ROOT/"v2/data/osm_agua_zmm.geojson"))["features"]
       if f["properties"]["clase"] == "competidor" and f["properties"]["nuevo_vs_v3_30m"]]
pts = comp + osm
P = np.array([to_m(*c) for c, _ in pts]); src = np.array([s for _, s in pts])
cols = json.load(open(ROOT/"v2/data/colonias_v3.geojson"))["features"]
polys = [(f["properties"]["cve_col"], transform(lambda x, y, z=None: to_m(x, y), shape(f["geometry"]))) for f in cols]
U = unary_union([g.buffer(300) for _, g in polys])
minx, miny, maxx, maxy = U.bounds
minx = min(minx, P[:, 0].min()-300); miny = min(miny, P[:, 1].min()-300); maxx = max(maxx, P[:, 0].max()+300); maxy = max(maxy, P[:, 1].max()+300)
S = 100.0
xs = np.arange(math.floor(minx/S)*S+S/2, maxx, S); ys = np.arange(math.floor(miny/S)*S+S/2, maxy, S)
print("grid bruto", len(xs), "x", len(ys))
rows = []
Ucap = prep(U)
for y in ys:
    # prefiltro por banda: puntos a <=300 m en y
    sel = np.where(np.abs(P[:, 1]-y) <= 300)[0]
    for x in xs:
        n = nv = no = 0
        if len(sel):
            d = np.hypot(P[sel, 0]-x, P[sel, 1]-y); m = d <= 300
            n = int(m.sum()); nv = int((m & (src[sel] == "v3")).sum()); no = n-nv
        inside = Ucap.contains(Point(x, y)) if n == 0 else True
        if n > 0 or inside:
            ce = ""
            for cve, g in polys:
                if g.contains(Point(x, y)): ce = cve; break
            rows.append((round(LAT0+y/KY, 6), round(LON0+x/KX, 6), n, nv, no, ce))
with open(ROOT/"v2/data/heat_competencia_300m.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["lat", "lon", "n_comp_300m", "n_v3", "n_osm_nuevo", "cve_col_centro"]); w.writerows(rows)
from collections import Counter
c = Counter(r[2] for r in rows)
print("celdas", len(rows), "max", max(c), "dist", sorted(c.items())[:12], "celdas con n=0 dentro de colonias+300:", c[0])
print("celdas con n>=1:", sum(v for k, v in c.items() if k >= 1))
