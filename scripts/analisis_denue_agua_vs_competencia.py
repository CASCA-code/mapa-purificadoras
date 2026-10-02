#!/usr/bin/env python3
"""DENUE 05_2026 (bulk NL, local) SCIAN agua/purificadoras vs competencia_v3, por colonia (poligono + 300 m, misma regla que v3).
Solo archivos locales (sin red). NO modifica ningun score. Salida: v2/data/denue_agua_vs_competencia.csv (+ detalle de puntos en /workspace/downloads)."""
import json, math, os, re, unicodedata
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENUE = "/home/box/geo/inegi_purificador/enlaces/denue_NL_2026-05_118MB.csv"
LAT0 = 25.70; KX = 111320.0 * math.cos(math.radians(LAT0)); KY = 110540.0
to_m = lambda lon, lat: ((lon + 100.3) * KX, (lat - LAT0) * KY)
def norm(s): return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
EXCL = re.compile(r"bonafont|\bciel\b|\be-?pura\b|santorini|electropura|embotelladora|envasadora|\bcedis\b|industrial|laboratorios|liquitek|coca[- ]?cola|pepsi|bebidas mundiales|arca continental|aqua ?fina|soy sanna", re.I)
SMALL = re.compile(r"^(0 a 5|6 a 10) personas")
# nombres que indican venta/recarga de agua (para SCIAN distintos de 312112)
NAME_AGUA = re.compile(r"purificad|garraf|recarga|\bagua (purificada|pura|de manantial|alcalina|y hielo)|venta de agua|expendio de agua|despachadora|agua(s)? y hielo|aquaclyva", re.I)
NAME_NO = re.compile(r"fritura|botana|fresca|nieve|paleta|cedis|bepusa|oxxo|7 eleven|aguacate|aguanaval|aguaje", re.I)
SCIAN_OK_B = {"461213": "bebidas no alcoholicas y hielo (menudeo)", "431211": "mayoreo bebidas no alcoholicas y hielo", "461110": "abarrotes", "462112": "minisuper", "461190": "otros alimentos", "312113": "hielo"}
d = pd.read_csv(DENUE, encoding="latin-1", dtype=str, usecols=["id", "nom_estab", "raz_social", "codigo_act", "nombre_act", "per_ocu", "nomb_asent", "municipio", "latitud", "longitud", "fecha_alta"])
d["lat"] = pd.to_numeric(d.latitud); d["lon"] = pd.to_numeric(d.longitud)
z = d[d.lat.between(25.52, 25.92) & d.lon.between(-100.70, -100.00)].copy()
z["nom"] = z.nom_estab.fillna(""); z["raz"] = z.raz_social.fillna("")
A = z[z.codigo_act == "312112"].copy(); A["grupo"] = "A_312112"
B = z[(z.codigo_act != "312112") & z.codigo_act.isin(SCIAN_OK_B) & z.nom.map(lambda s: bool(NAME_AGUA.search(s)) and not NAME_NO.search(s))].copy()   # solo nombre comercial
# 312113 hielo y otros solo si el nombre dice agua/purificad (hielo solo no es agua)
B = B[~((B.codigo_act == "312113") & ~B.nom.str.contains(r"agua|purificad", case=False, regex=True))]
B["grupo"] = "B_otro_scian_nombre_agua"
P = pd.concat([A, B]).reset_index(drop=True)
P["excl_v3"] = P.apply(lambda r: bool(EXCL.search(r.nom + " " + r.raz)), axis=1)
P["pequena"] = P.per_ocu.fillna("").map(lambda s: bool(SMALL.search(s)))
P["v3_filtro_ok"] = ~P.excl_v3 & (P.pequena | (P.codigo_act != "312112") | True)   # ver nota: v3 aplica el corte de personal solo a canal industrial
# replica exacta de denue_ok: excluye regex; canal 'industrial/embotellador' (por nombre, ver compet.geojson) y no pequena
cg = json.load(open(f"{ROOT}/data/compet.geojson"))["features"]
cg_ok = [f for f in cg if not EXCL.search((f["properties"].get("nombre") or "") + " " + (f["properties"].get("razon") or ""))
         and not (str(f["properties"].get("canal") or "").startswith("industrial") and not SMALL.search(f["properties"].get("estrato") or ""))]
v3 = json.load(open(f"{ROOT}/v2/data/competencia_v3.geojson"))["features"]
v3_xy = np.array([to_m(*f["geometry"]["coordinates"]) for f in v3]); v3_src = np.array([f["properties"]["s"] for f in v3]); v3_n = [f["properties"]["n"] for f in v3]
tree3 = cKDTree(v3_xy)
cg_xy = np.array([to_m(*f["geometry"]["coordinates"]) for f in cg]); cg_tree = cKDTree(cg_xy)
P["x"], P["y"] = zip(*[to_m(lo, la) for lo, la in zip(P.lon, P.lat)])
# match con compet.geojson (<=15 m) y con competencia_v3 (<=30 m, cualquier fuente)
dd, ii = cg_tree.query(P[["x", "y"]].values)
P["en_compet_geojson"] = dd <= 15
P["compet_canal"] = [cg[i]["properties"].get("canal") if dd_ <= 15 else "" for i, dd_ in zip(ii, dd)]
dd3, ii3 = tree3.query(P[["x", "y"]].values)
P["dist_v3_m"] = dd3.round(1); P["v3_cercano_fuente"] = v3_src[ii3]; P["en_v3_30m"] = dd3 <= 30
P["en_v3_denue_15m"] = [(dd3_ <= 15 and v3_src[i_] == "denue") for dd3_, i_ in zip(dd3, ii3)]
# candidatos "nuevos": DENUE agua, no excluido por regla v3, y a >30 m de TODO punto de competencia_v3
P["nuevo_vs_v3"] = ~P.en_v3_30m & ~P.excl_v3 & ~((P.compet_canal.fillna("").str.startswith("industrial")) & ~P.pequena) & ~((P.grupo != "A_312112") & ~P.pequena)   # B grande (>10 personas) = empresa, no recarga de barrio

# ---------- por colonia (poligono + 300 m) ----------
cols = json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")[["cve_col", "rank_base", "comp_n_300m", "scout_marks", "cobertura_campo"]]
def proj(g): return transform(lambda x, y, z=None: to_m(x, y), g)
pts_all = [Point(x, y) for x, y in zip(P.x, P.y)]
st = STRtree(pts_all)
v3pts = [Point(x, y) for x, y in v3_xy]; st3 = STRtree(v3pts)
rows = []
for f in cols:
    p = f["properties"]; g300 = proj(shape(f["geometry"])).buffer(300.0)
    ia = st.query(g300, predicate="intersects"); ia = np.array(sorted(ia), dtype=int)
    sub = P.iloc[ia] if len(ia) else P.iloc[[]]
    i3 = st3.query(g300, predicate="intersects"); i3 = np.array(sorted(i3), dtype=int)
    n_v3_den = int((v3_src[i3] == "denue").sum()); n_v3_pl = int((v3_src[i3] == "places").sum())
    rows.append(dict(cve_col=p["cve_col"], colonia=p["colonia"], municipio=p["municipio"],
        n_312112_total=int((sub.grupo == "A_312112").sum()),
        n_312112_no_excluido_v3=int(((sub.grupo == "A_312112") & ~sub.excl_v3).sum()),
        n_otro_scian_nombre_agua=int((sub.grupo == "B_otro_scian_nombre_agua").sum()),
        n_denue_agua_total=len(sub),
        n_v3_denue=n_v3_den, n_v3_places=n_v3_pl, comp_n_v3_total=len(i3),
        n_denue_nuevo_vs_v3=int(sub.nuevo_vs_v3.sum()),
        nuevos_nombres="; ".join(sorted(set(sub[sub.nuevo_vs_v3].nom.str.title().str[:40])))[:200]))
R = pd.DataFrame(rows).merge(v, on="cve_col", validate="1:1")
assert (R.comp_n_v3_total == R.comp_n_300m).all(), "no reproduce comp_n_300m de v3"
R["delta_312112_vs_v3denue"] = R.n_312112_total - R.n_v3_denue
R["delta_denue_agua_vs_v3total"] = R.n_denue_agua_total - R.comp_n_v3_total
R["delta_nuevos_vs_v3"] = R.n_denue_nuevo_vs_v3
R["clase"] = np.select([R.n_denue_nuevo_vs_v3 > 0, R.delta_denue_agua_vs_v3total > 0, R.delta_denue_agua_vs_v3total < 0], ["DENUE aporta puntos nuevos", "DENUE>v3 (solo conteo)", "DENUE<v3 (v3 tiene Places/otros)"], "igual")
R["cero_en_v3"] = R.comp_n_300m == 0
R["etiqueta"] = "VERIFICADO (conteo en DENUE 05_2026 bulk, poligono+300 m); no altera score"
R = R.sort_values("rank_base")
R.to_csv(f"{ROOT}/v2/data/denue_agua_vs_competencia.csv", index=False)
P.drop(columns=["x", "y"]).to_csv("/workspace/downloads/denue_agua_puntos_detalle.csv", index=False)
# ---------- resumen ----------
S = dict(n_bbox_312112=int((P.grupo == "A_312112").sum()), n_B=int((P.grupo != "A_312112").sum()), n_compet_geojson=len(cg), n_compet_ok=len(cg_ok),
         n_v3_denue=int((v3_src == "denue").sum()), A_en_compet_geojson=int(P[P.grupo == "A_312112"].en_compet_geojson.sum()),
         A_excl_regex=int(P[(P.grupo == "A_312112")].excl_v3.sum()), A_nuevo=int(P[(P.grupo == "A_312112")].nuevo_vs_v3.sum()), B_nuevo=int(P[P.grupo != "A_312112"].nuevo_vs_v3.sum()),
         A_fecha_alta_max=str(P[P.grupo == "A_312112"].fecha_alta.max()), A_per_ocu=P[P.grupo == "A_312112"].per_ocu.value_counts().to_dict(),
         clase=R.clase.value_counts().to_dict(),
         ceros_con_nuevo=int(((R.cero_en_v3) & (R.n_denue_nuevo_vs_v3 > 0)).sum()), ceros_con_algun_denue=int(((R.cero_en_v3) & (R.n_denue_agua_total > 0)).sum()),
         colonias_con_nuevo=int((R.n_denue_nuevo_vs_v3 > 0).sum()), sum_denue_agua=int(R.n_denue_agua_total.sum()), sum_v3=int(R.comp_n_v3_total.sum()),
         dens_mas=int((R.delta_denue_agua_vs_v3total > 0).sum()), dens_menos=int((R.delta_denue_agua_vs_v3total < 0).sum()), dens_igual=int((R.delta_denue_agua_vs_v3total == 0).sum()))
print(json.dumps(S, indent=1, ensure_ascii=False))
json.dump(S, open("/workspace/downloads/denue_agua_stats.json", "w"), indent=1, ensure_ascii=False)
