#!/usr/bin/env python3
"""Densidad de comercio de barrio OSM (shop=supermarket|convenience) en hex H3 res 8; top 30 hex no encuestados por Scout.
Entrada raw (fuera del repo): /workspace/downloads/osm_retail_zmm_raw.json. Sin red. NO modifica scores.
Salida: v2/data/scout_top30_retail.csv (+ /workspace/downloads/retail_hex_all.csv). Ejecutar con un python que tenga h3 (v4) y shapely."""
import json, math, os, re, unicodedata
from collections import Counter
import numpy as np, pandas as pd, h3
from scipy.spatial import cKDTree
from shapely.geometry import shape, Polygon, Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/workspace/downloads/osm_retail_zmm_raw.json"
LAT0 = 25.70; KX = 111320.0 * math.cos(math.radians(LAT0)); KY = 110540.0
to_m = lambda lon, lat: ((lon + 100.3) * KX, (lat - LAT0) * KY)
def norm(s): return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
raw = json.load(open(RAW)); el = raw["elements"]
R = pd.DataFrame([dict(osm=f"{e['type']}/{e['id']}", lat=e["lat"], lon=e["lon"], shop=e["tags"].get("shop"), name=e["tags"].get("name", ""), brand=e["tags"].get("brand", "")) for e in el])
n_raw = len(R)
R["x"], R["y"] = zip(*[to_m(lo, la) for lo, la in zip(R.lon, R.lat)])
# 1) dedupe interno 30 m (prioriza el que tiene nombre)
R = R.sort_values("name", key=lambda s: s.eq(""), kind="stable").reset_index(drop=True)
t = cKDTree(R[["x", "y"]].values); drop = np.zeros(len(R), bool)
for i in range(len(R)):
    if drop[i]: continue
    for j in t.query_ball_point(R.loc[i, ["x", "y"]].values, 30.0):
        if j > i: drop[j] = True
n_dup_int = int(drop.sum()); R = R[~drop].reset_index(drop=True)
# 2) dedupe vs anclas_v3 (oxxo/express/cerveza; 30 m, misma regla que v3). Abarrotes (DENUE) no esta en anclas_v3 -> no se resta.
a = json.load(open(f"{ROOT}/v2/data/anclas_v3.geojson"))["features"]
cats = {"oxxo", "express", "cerveza"}
axy = np.array([to_m(*f["geometry"]["coordinates"]) for f in a if f["properties"].get("c") in cats]); atree = cKDTree(axy)
dd, _ = atree.query(R[["x", "y"]].values); R["en_anclas_v3_30m"] = dd <= 30
n_dup_v3 = int(R.en_anclas_v3_30m.sum())
R = R[~R.en_anclas_v3_30m].reset_index(drop=True)
# 3) hex H3 res 8
R["h3"] = [h3.latlng_to_cell(la, lo, 8) for la, lo in zip(R.lat, R.lon)]
R["cadena"] = R.apply(lambda r: bool(re.search(r"oxxo|7.?eleven|six|super ?city|kiosko|extra|circle ?k|walmart|soriana|aurrera|heb|h-e-b|chedraui|la fe", norm(r["name"] + " " + r["brand"]))), axis=1)
g = R.groupby("h3").agg(n_total=("osm", "size"), n_super=("shop", lambda s: int((s == "supermarket").sum())), n_conv=("shop", lambda s: int((s == "convenience").sum())),
                        n_nombre_cadena=("cadena", "sum"), nombres=("name", lambda s: "; ".join(sorted({x[:28] for x in s if x})[:4]))).reset_index()
g["lat"], g["lon"] = zip(*[h3.cell_to_latlng(c) for c in g.h3])
# 4) Scout: marcas de encuesta (sin favorito/lock), por hex y vecinos anillo 1
sm = json.load(open(f"{ROOT}/v2/data/scout_marks_v3.geojson"))["features"]
surv = [f for f in sm if f["properties"].get("k") not in ("favorito", "lock")]
sc = Counter(h3.latlng_to_cell(f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], 8) for f in surv)
g["scout_en_hex"] = g.h3.map(lambda c: sc.get(c, 0))
g["scout_vecinos_ring1"] = g.h3.map(lambda c: sum(sc.get(n, 0) for n in h3.grid_disk(c, 1) if n != c))
# 5) colonia (poligono que intersecta el hex; la de mayor area)
cols = [(f["properties"], shape(f["geometry"])) for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]]
v3 = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv").set_index("cve_col")
try: bc = pd.read_csv(f"{ROOT}/v2/data/colonias_v3_banda_confianza.csv").set_index("cve_col")
except Exception: bc = None
def col_of(c):
    hp = Polygon([(lo, la) for la, lo in h3.cell_to_boundary(c)])
    best, ba = None, 0.0
    for p, gm in cols:
        if gm.intersects(hp):
            ar = gm.intersection(hp).area
            if ar > ba: best, ba = p, ar
    return best, ba / hp.area if best else 0.0
res = [col_of(c) for c in g.h3]
g["cve_col"] = [r[0]["cve_col"] if r[0] else "" for r in res]; g["colonia"] = [r[0]["colonia"] if r[0] else "" for r in res]
g["municipio"] = [r[0]["municipio"] if r[0] else "" for r in res]; g["frac_hex_en_colonia"] = [round(r[1], 2) for r in res]
g["rank_base_colonia"] = g.cve_col.map(lambda k: int(v3.loc[k, "rank_base"]) if k else None)
g["comp_300m_colonia"] = g.cve_col.map(lambda k: int(v3.loc[k, "comp_n_300m"]) if k else None)
if bc is not None: g["confianza_colonia"] = g.cve_col.map(lambda k: bc.loc[k, "confianza"] if k else "")
g["gmaps"] = [f"https://www.google.com/maps/search/?api=1&query={la:.5f},{lo:.5f}" for la, lo in zip(g.lat, g.lon)]
g = g.sort_values(["n_total", "n_super"], ascending=False)
g.to_csv("/workspace/downloads/retail_hex_all.csv", index=False)
elig = g[(g.scout_en_hex == 0) & (g.cve_col != "") & (g.frac_hex_en_colonia >= 0.15)].copy()   # >=15 % del hex dentro de la colonia (evita hex que solo rozan el poligono)
top = elig.head(30).copy(); top.insert(0, "prioridad", range(1, len(top) + 1))
top["etiqueta"] = "VERIFICADO conteo OSM (shop=supermarket|convenience) en hex H3 r8; densidad de comercio = proxy de flujo, SUPUESTO; plan de campo, sin visita hecha"
top["nota_campo"] = "contar 10 min peatones/clientes en esquina comercial; anotar en Scout (kind express/otro); ver tambien recargas informales"
cols_out = ["prioridad", "h3", "lat", "lon", "n_total", "n_super", "n_conv", "n_nombre_cadena", "nombres", "cve_col", "colonia", "municipio", "frac_hex_en_colonia", "rank_base_colonia",
            "comp_300m_colonia"] + (["confianza_colonia"] if bc is not None else []) + ["scout_en_hex", "scout_vecinos_ring1", "gmaps", "etiqueta", "nota_campo"]
top[cols_out].to_csv(f"{ROOT}/v2/data/scout_top30_retail.csv", index=False)
S = dict(generator=raw.get("generator"), n_raw=n_raw, n_dup_interno=n_dup_int, n_dup_anclas_v3=n_dup_v3, n_unicos=len(R), n_hex=len(g), n_hex_en_colonias=int((g.cve_col != "").sum()),
         n_hex_surveyed=int((g.scout_en_hex > 0).sum()), n_elig=len(elig), shops=R["shop"].value_counts().to_dict(), max_n=int(g.n_total.max()),
         top30_n_min=int(top.n_total.min()), top30_n_max=int(top.n_total.max()), hex_con_scout_top30_global=int((g.head(30).scout_en_hex > 0).sum()),
         top30_global_en_colonias=int((g.head(30).cve_col != "").sum()), mediana_hex=float(g.n_total.median()), pctl_top30_cut=float(g.n_total.quantile(.99)),
         cadenas=int(R.cadena.sum()), top30_municipios=top.municipio.value_counts().to_dict(), top30_confianza=(top.confianza_colonia.value_counts().to_dict() if bc is not None else {}),
         top30_rank_base_le30=int((top.rank_base_colonia <= 30).sum()))
json.dump(S, open("/workspace/downloads/scout_top30_stats.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(S, indent=1, ensure_ascii=False))
