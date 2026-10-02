#!/usr/bin/env python3
"""Extrae de un .pbf Geofabrik (pyosmium) amenity=marketplace y shop=butcher|greengrocer|bakery en el bbox ZMM (nodos + vias por centroide; relaciones omitidas). Fallback porque Overpass no responde. Salida fuera del repo."""
import osmium, json, time
SRC = "/home/box/geo/base_mty/raw/pbf/mexico-260929.osm.pbf"
S, W, N, E = 25.52, -100.70, 25.92, -100.00
def key(t):
    if t.get("amenity")=="marketplace": return "marketplace"
    s=t.get("shop")
    if s in ("butcher","greengrocer","bakery"): return s
    return None
t0=time.time(); ways={}; need=set(); out=[]
for o in osmium.FileProcessor(SRC, osmium.osm.WAY):
    t={x.k:x.v for x in o.tags}; k=key(t)
    if k: ways[o.id]=(k,t,[n.ref for n in o.nodes]); need.update(n.ref for n in o.nodes)
nodes={}
for o in osmium.FileProcessor(SRC, osmium.osm.NODE):
    if o.id in need: nodes[o.id]=(o.location.lat,o.location.lon)
    if o.tags:
        t={x.k:x.v for x in o.tags}; k=key(t)
        if k and S<=o.location.lat<=N and W<=o.location.lon<=E:
            out.append(dict(type="node",id=o.id,lat=o.location.lat,lon=o.location.lon,kind=k,tags=t))
for i,(k,t,refs) in ways.items():
    pts=[nodes[r] for r in refs if r in nodes]
    if not pts: continue
    la=sum(p[0] for p in pts)/len(pts); lo=sum(p[1] for p in pts)/len(pts)
    if S<=la<=N and W<=lo<=E: out.append(dict(type="way",id=i,lat=la,lon=lo,kind=k,tags=t))
json.dump({"generator":"pyosmium sobre Geofabrik mexico-260929.osm.pbf (2026-09-29), (c) OpenStreetMap contributors ODbL; fallback: Overpass 4 mirrors sin conexion 2026-10-02","bbox":"lat 25.52..25.92, lon -100.70..-100.00","elements":out},open("/workspace/downloads/osm_anchor_extra_raw.json","w"),ensure_ascii=False)
from collections import Counter
print(Counter(e["kind"] for e in out), Counter((e["type"],e["kind"]) for e in out), time.time()-t0)
