#!/usr/bin/env python3
"""Ancla OSM adicional (carniceria shop=butcher) en hex H3 r8; top 30 hex sin encuesta Scout. NO modifica scores.
Entrada fuera del repo: /workspace/downloads/osm_anchor_extra_raw.json (scripts/extract_osm_anchor_extra.py). Sin red.
Salida: v2/data/scout_top30_ancla_extra.csv (+ /workspace/downloads/ancla_extra_stats.json, ancla_extra_hex_all.csv). Correr con python que tenga h3 v4, shapely, scipy."""
import json, math, os
from collections import Counter
import numpy as np, pandas as pd, h3
from scipy.spatial import cKDTree
from shapely.geometry import shape, Polygon, Point
from shapely.ops import transform
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/workspace/downloads/osm_anchor_extra_raw.json"
LAT0 = 25.70; KX = 111320.0 * math.cos(math.radians(LAT0)); KY = 110540.0
to_m = lambda lon, lat: ((lon + 100.3) * KX, (lat - LAT0) * KY)
raw = json.load(open(RAW)); el = raw["elements"]
R = pd.DataFrame([dict(osm=f"{e['type']}/{e['id']}", lat=e["lat"], lon=e["lon"], kind=e["kind"], name=e["tags"].get("name", "")) for e in el])
R["x"], R["y"] = zip(*[to_m(lo, la) for lo, la in zip(R.lon, R.lat)])
S = dict(generator=raw["generator"], n_raw=len(R), por_tipo_raw=R.kind.value_counts().to_dict())
# dedupe interno 30 m dentro del mismo tipo (prioriza el que tiene nombre)
R = R.sort_values("name", key=lambda s: s.eq(""), kind="stable").reset_index(drop=True); drop = np.zeros(len(R), bool)
for k in R.kind.unique():
    idx = np.where(R.kind.values == k)[0]; t = cKDTree(R.loc[idx, ["x", "y"]].values)
    for ii, i in enumerate(idx):
        if drop[i]: continue
        for jj in t.query_ball_point(R.loc[i, ["x", "y"]].values, 30.0):
            j = idx[jj]
            if j > i: drop[j] = True
S["dup_internos"] = int(drop.sum()); R = R[~drop].reset_index(drop=True)
# distancia a cualquier ancla de anclas_v3 (todas las categorias); "nuevo" = > 30 m
a = json.load(open(f"{ROOT}/v2/data/anclas_v3.geojson"))["features"]
atree = cKDTree(np.array([to_m(*f["geometry"]["coordinates"]) for f in a]))
R["d_ancla_v3_m"], _ = atree.query(R[["x", "y"]].values); R["nuevo"] = R.d_ancla_v3_m > 30
cols = [(f["properties"], transform(to_m, shape(f["geometry"]))) for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]]
R["en_col167"] = [any(g.contains(Point(*to_m(lo, la))) for _, g in cols) for lo, la in zip(R.lon, R.lat)]
S["comparacion_tipos"] = {k: dict(n=int(len(g)), nuevos_vs_anclas_v3=int(g.nuevo.sum()), dentro_167=int(g.en_col167.sum()), nuevos_dentro_167=int((g.nuevo & g.en_col167).sum())) for k, g in R.groupby("kind")}
ELEGIDO = "butcher"
R = R[R.nuevo].reset_index(drop=True)
R["h3"] = [h3.latlng_to_cell(la, lo, 8) for la, lo in zip(R.lat, R.lon)]
g = R.groupby("h3").agg(n_butcher=("kind", lambda s: int((s == ELEGIDO).sum())), n_bakery=("kind", lambda s: int((s == "bakery").sum())),
                        n_greengrocer=("kind", lambda s: int((s == "greengrocer").sum())), n_marketplace=("kind", lambda s: int((s == "marketplace").sum())),
                        nombres=("name", lambda s: "; ".join(sorted({x[:28] for x in s if x})[:4]))).reset_index()
g = g[g.n_butcher > 0].copy(); g["n_complemento"] = g.n_bakery + g.n_greengrocer + g.n_marketplace
g["lat"], g["lon"] = zip(*[h3.cell_to_latlng(c) for c in g.h3])
sm = json.load(open(f"{ROOT}/v2/data/scout_marks_v3.geojson"))["features"]
surv = [f for f in sm if f["properties"].get("k") not in ("favorito", "lock")]
sc = Counter(h3.latlng_to_cell(f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], 8) for f in surv)
g["scout_en_hex"] = g.h3.map(lambda c: sc.get(c, 0)); g["scout_vecinos_ring1"] = g.h3.map(lambda c: sum(sc.get(n, 0) for n in h3.grid_disk(c, 1) if n != c))
v3 = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv").set_index("cve_col"); bc = pd.read_csv(f"{ROOT}/v2/data/colonias_v3_banda_confianza.csv").set_index("cve_col")
def col_of(c):
    hp = transform(to_m, Polygon([(lo, la) for la, lo in h3.cell_to_boundary(c)])); cen = hp.centroid
    best, ba = None, 0.0
    for p, gm in cols:
        if gm.intersects(hp):
            ar = gm.intersection(hp).area
            if ar > ba: best, ba = p, ar
    if best: return best, ba / hp.area, 0.0
    dmin, pm = 1e18, None
    for p, gm in cols:
        d = gm.distance(cen)
        if d < dmin: dmin, pm = d, p
    return pm, 0.0, dmin
res = [col_of(c) for c in g.h3]
g["cve_col"] = [r[0]["cve_col"] for r in res]; g["colonia_cercana"] = [r[0]["colonia"] for r in res]; g["municipio"] = [r[0]["municipio"] for r in res]
g["frac_hex_en_colonia"] = [round(r[1], 2) for r in res]; g["dist_a_colonia_m"] = [int(round(r[2])) for r in res]
g["rank_base_colonia"] = g.cve_col.map(lambda k: int(v3.loc[k, "rank_base"])); g["comp_300m_colonia"] = g.cve_col.map(lambda k: int(v3.loc[k, "comp_n_300m"]))
g["confianza_colonia"] = g.cve_col.map(lambda k: bc.loc[k, "confianza"])
g["gmaps"] = [f"https://www.google.com/maps/search/?api=1&query={la:.5f},{lo:.5f}" for la, lo in zip(g.lat, g.lon)]
g = g.sort_values(["n_butcher", "n_complemento", "dist_a_colonia_m"], ascending=[False, False, True])
g.to_csv("/workspace/downloads/ancla_extra_hex_all.csv", index=False)
elig = g[g.scout_en_hex == 0].copy()
top = elig.head(30).copy(); top.insert(0, "prioridad", range(1, len(top) + 1))
top["etiqueta"] = "VERIFICADO conteo OSM shop=butcher (nuevos >30 m de anclas_v3) en hex H3 r8; vinculo con flujo de recarga = SUPUESTO; plan de campo, sin visita hecha"
top["nota_campo"] = "contar 10 min peatones/clientes frente a la carniceria; anotar en Scout (kind otro); revisar recargas informales"
cols_out = ["prioridad", "h3", "lat", "lon", "n_butcher", "n_complemento", "n_bakery", "n_greengrocer", "n_marketplace", "nombres", "cve_col", "colonia_cercana", "municipio",
            "frac_hex_en_colonia", "dist_a_colonia_m", "rank_base_colonia", "comp_300m_colonia", "confianza_colonia", "scout_en_hex", "scout_vecinos_ring1", "gmaps", "etiqueta", "nota_campo"]
top[cols_out].to_csv(f"{ROOT}/v2/data/scout_top30_ancla_extra.csv", index=False)
S.update(elegido=ELEGIDO, n_butcher_nuevos=int((R.kind == ELEGIDO).sum()), n_hex_butcher=len(g), n_hex_con_scout=int((g.scout_en_hex > 0).sum()), n_elig=len(elig),
         hex_dentro_167=int((g.frac_hex_en_colonia > 0).sum()), top30_dentro_167=int((top.frac_hex_en_colonia > 0).sum()),
         top30_dist_le500=int((top.dist_a_colonia_m <= 500).sum()), top30_dist_le1500=int((top.dist_a_colonia_m <= 1500).sum()), top30_dist_max=int(top.dist_a_colonia_m.max()),
         top30_n_butcher=top.n_butcher.value_counts().sort_index(ascending=False).to_dict(), top30_municipios=top.municipio.value_counts().to_dict(),
         top30_confianza=top.confianza_colonia.value_counts().to_dict(), top30_con_complemento=int((top.n_complemento > 0).sum()),
         max_butcher_hex=int(g.n_butcher.max()), nombre_cadena_carniceria=int(R[R.kind == ELEGIDO].name.str.contains("Carnes|Carnicer", case=False, regex=True).sum()))
json.dump(S, open("/workspace/downloads/ancla_extra_stats.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(S, indent=1, ensure_ascii=False))
