#!/usr/bin/env python3
"""Rating v3 (colonias) + block heat (100 m cells) for v2/ map.

Reads ONLY static files in data/ (read-only) and writes v2/data/.
Formula + weights: docs/RATING_V3.md. No network calls.

  python3 scripts/build_v3_rating.py
"""
from __future__ import annotations
import csv, json, math, os, re, unicodedata, datetime
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform
from shapely.prepared import prep

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda f: os.path.join(ROOT, "data", f)
OUT = os.path.join(ROOT, "v2", "data")
os.makedirs(OUT, exist_ok=True)

LAT0 = 25.70
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110540.0
def to_m(lon, lat): return ((lon + 100.3) * KX, (lat - LAT0) * KY)
def to_ll(x, y): return (x / KX - 100.3, y / KY + LAT0)
def proj_geom(g): return transform(lambda x, y, z=None: to_m(x, y), g)

HAB_POR_VIV = 3.6          # same factor used by the v2 study (served_dwellings = served_pop/3.6)

# ---------- weights (documented in docs/RATING_V3.md) ----------
W_ANCHOR = {
    "cerveza": 1.50,       # Modelorama / Six / Tecate / depósito de cerveza → foot-traffic predictor
    "tortilleria": 1.25,
    "banco_bienestar_azteca": 1.25,  # Banco del Bienestar, Banco Azteca (incl. Elektra = Banco Azteca inside)
    "oxxo": 1.00,          # sells water pricier → positive
    "express": 1.00,       # Bodega Aurrera Express / Soriana Express → D+/D demographic proxy
    "iglesia": 1.00,
    "escuela": 1.00,
    "parada": 0.75,        # parada de camión
    "farmacia": 0.50,      # farmacia de barrio (not chains)
    "abarrotes": 0.40,     # 20k DENUE tienditas — dense, low weight each
}
W_TRAFFIC = {             # cell layer only (within 100 m)
    "semaforo_scout": 2.5, "alto_scout": 2.0,
    "semaforo_osm": 1.0, "alto_osm": 0.75,
    "parada": 1.0,
}
R_ANCHOR, R_TRAFFIC, R_COMP = 150.0, 100.0, 300.0
COMP_PENALTY = 4.0        # per competitor at distance 0, linear to 0 at 300 m
W_D, W_A, W_C = 0.40, 0.30, 0.30
COL_ANCHOR_BUFFER = 100.0 # anchors counted inside polygon + 100 m
COL_COMP_BUFFER = 300.0   # competitors counted inside polygon + 300 m
CELL = 100.0

def load(f):
    return json.load(open(D(f), encoding="utf-8"))["features"]

def pts(feats, filt=lambda p: True):
    out = []
    for f in feats:
        g = f.get("geometry") or {}
        if g.get("type") != "Point": continue
        p = f.get("properties") or {}
        if filt(p): out.append((g["coordinates"][0], g["coordinates"][1], p))
    return out

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return s

deleted = set(json.load(open(D("field_adds_deleted.json"))))
fa = [f for f in load("field_adds.geojson") if (f["properties"].get("id") not in deleted)]
def fa_kind(k): return pts(fa, lambda p: p.get("kind") == k)
fa_otro = pts(fa, lambda p: p.get("kind") == "otro")

# ---------- anchors, by category, in source-priority order (Scout first) ----------
src = {}   # cat -> list of (lon,lat,source,name)
def add(cat, lst, source, name_key):
    src.setdefault(cat, []).extend((x, y, source, (p.get(name_key) or "")) for x, y, p in lst)

pl = load("places_anclas_zmm.geojson")
retail = load("retail.geojson")
anc = load("anclas.geojson")
add("cerveza", fa_kind("modelorama"), "scout", "name")
add("cerveza", pts(pl, lambda p: p.get("kind") in ("modelorama", "six")), "places", "name")
add("cerveza", pts(retail, lambda p: p.get("subtipo") == "modelorama_six_cerveza"), "osm", "name")
add("express", fa_kind("express"), "scout", "name")
add("express", pts(pl, lambda p: p.get("kind") in ("express", "soriana_express")), "places", "name")
add("express", pts(retail, lambda p: p.get("subtipo") in ("aurrera_express", "soriana_express")), "osm", "name")
add("oxxo", pts(pl, lambda p: p.get("kind") == "oxxo"), "places", "name")
add("banco_bienestar_azteca", pts(load("anclas_bancos_prestamo_zmm.geojson")), "barrio", "n")
add("banco_bienestar_azteca", pts(pl, lambda p: p.get("kind") == "banco" and re.search(r"azteca|bienestar", norm(p.get("name")))), "places", "name")
add("banco_bienestar_azteca", pts(retail, lambda p: p.get("subtipo") in ("banco_azteca", "banco_bienestar")), "osm", "name")
add("iglesia", fa_kind("iglesia"), "scout", "name")
add("iglesia", pts(anc, lambda p: p.get("tipo") == "iglesia"), "osm", "name")
add("escuela", fa_kind("escuela"), "scout", "name")
add("escuela", pts(anc, lambda p: p.get("tipo") == "escuela"), "osm", "name")
add("tortilleria", pts(load("anclas_tortillerias_zmm.geojson")), "barrio", "n")
add("abarrotes", pts(load("anclas_abarrotes_zmm.geojson")), "barrio", "n")
add("farmacia", pts(load("anclas_farmacias_barrio_zmm.geojson")), "barrio", "n")
add("parada", pts(load("anclas_paradas_zmm.geojson")), "barrio", "n")

def dedupe(lst, r):
    """keep first (highest priority) point; drop later ones within r metres"""
    kept, xy = [], []
    tree_pts = []
    for it in lst:
        x, y = to_m(it[0], it[1])
        if tree_pts:
            t = cKDTree(np.array(tree_pts))
            if t.query_ball_point((x, y), r): continue
        kept.append(it); tree_pts.append((x, y))
    return kept

def dedupe_fast(lst, r):
    if len(lst) < 2: return lst
    xy = np.array([to_m(a[0], a[1]) for a in lst])
    t = cKDTree(xy); drop = np.zeros(len(lst), bool)
    for i in range(len(lst)):
        if drop[i]: continue
        for j in t.query_ball_point(xy[i], r):
            if j > i: drop[j] = True
    return [a for a, d in zip(lst, drop) if not d]

anchors = {}
stats = {"anchors_raw": {}, "anchors_dedup": {}}
for cat, lst in src.items():
    stats["anchors_raw"][cat] = len(lst)
    # multi-source categories → 30 m dedupe (barrio layers are already deduped internally)
    anchors[cat] = dedupe_fast(lst, 30.0)
    stats["anchors_dedup"][cat] = len(anchors[cat])

# ---------- traffic points ----------
scout_sema = [(x, y, "scout", "Semáforo") for x, y, p in fa_otro if "semaforo" in norm(p.get("name")) + norm(p.get("nota_raw"))]
scout_sema += [(x, y, "scout", "Semáforo") for x, y, p in fa_kind("semaforo")]
scout_alto = [(x, y, "scout", "Alto") for x, y, p in fa_kind("alto")]
osm_sema = [(x, y, "osm", "Semáforo") for x, y, p in pts(load("semaforos_zmm.geojson"))]
osm_alto = [(x, y, "osm", "Alto") for x, y, p in pts(load("stops_zmm.geojson"))]
def drop_near(base, cand, r):
    if not base: return cand
    t = cKDTree(np.array([to_m(a[0], a[1]) for a in base]))
    return [c for c in cand if not t.query_ball_point(to_m(c[0], c[1]), r)]
scout_all = scout_sema + scout_alto
osm_sema_d = drop_near(scout_all, dedupe_fast(osm_sema, 15.0), 15.0)
osm_alto_d = drop_near(scout_all, dedupe_fast(osm_alto, 15.0), 15.0)
traffic = {"semaforo_scout": dedupe_fast(scout_sema, 15.0), "alto_scout": dedupe_fast(scout_alto, 15.0),
           "semaforo_osm": osm_sema_d, "alto_osm": osm_alto_d, "parada": anchors["parada"]}
stats["traffic"] = {k: len(v) for k, v in traffic.items()}
stats["traffic_osm_removed_as_dup_of_scout"] = {"semaforo": len(dedupe_fast(osm_sema, 15.0)) - len(osm_sema_d),
                                                 "alto": len(dedupe_fast(osm_alto, 15.0)) - len(osm_alto_d)}

# ---------- competition (same rules as docs/COMPETENCIA.md) ----------
EXCL = re.compile(r"bonafont|\bciel\b|\be-?pura\b|santorini|electropura|embotelladora|envasadora|\bcedis\b|industrial|laboratorios|liquitek|coca[- ]?cola|pepsi|bebidas mundiales|arca continental|aqua ?fina|soy sanna", re.I)
SMALL = re.compile(r"^(0 a 5|6 a 10) personas")
def denue_ok(p):
    if EXCL.search((p.get("nombre") or "") + " " + (p.get("razon") or "")): return False
    if str(p.get("canal") or "").startswith("industrial") and not SMALL.search(p.get("estrato") or ""): return False
    return True
comp = [(x, y, "scout", p.get("name") or "") for x, y, p in fa_kind("purificadora")]
comp += [(x, y, "scout", p.get("name") or "") for x, y, p in fa_otro
         if re.search(r"purificador|recarga de agua|garraf", norm(p.get("name")) + " " + norm(p.get("nota_raw")) + " " + norm(p.get("descripcion")))]
comp += [(x, y, "denue", p.get("nombre") or "") for x, y, p in pts(load("compet.geojson"), denue_ok)]
comp += [(x, y, "places", p.get("name") or "") for x, y, p in pts(load("places_purificadoras_zmm.geojson"), lambda p: not EXCL.search(p.get("name") or ""))]
stats["comp_raw"] = len(comp)
comp = dedupe_fast(comp, 30.0)
stats["comp_dedup"] = len(comp)

# ---------- colonias ----------
cols = load("colonias.geojson")
N = len(cols)
geoms_m = [proj_geom(shape(f["geometry"])) for f in cols]
def count_in(geom_m, lst):
    if not lst: return 0
    g = prep(geom_m); minx, miny, maxx, maxy = geom_m.bounds
    n = 0
    for a in lst:
        x, y = to_m(a[0], a[1])
        if minx <= x <= maxx and miny <= y <= maxy and g.contains(Point(x, y)): n += 1
    return n

def pct_rank(vals, zero_is_zero=False):
    v = np.array(vals, float); order = v.argsort(kind="stable")
    ranks = np.empty(len(v)); 
    # average rank for ties
    sv = v[order]; i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and sv[j + 1] == sv[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    r = ranks / (len(v) - 1)
    if zero_is_zero: r[v == 0] = 0.0
    return r

rows = []
for f, gm in zip(cols, geoms_m):
    p = f["properties"]
    ga = gm.buffer(COL_ANCHOR_BUFFER); gc = gm.buffer(COL_COMP_BUFFER)
    cnt = {cat: count_in(ga, lst) for cat, lst in anchors.items()}
    a_raw = sum(W_ANCHOR[c] * n for c, n in cnt.items())
    # bias check: same count without Scout field marks (Scout survey is concentrated in a few colonias)
    cnt_scout = {cat: count_in(ga, [a for a in lst if a[2] == "scout"]) for cat, lst in anchors.items() if any(a[2] == "scout" for a in lst)}
    a_raw_desk = a_raw - sum(W_ANCHOR[c] * n for c, n in cnt_scout.items())
    viv = (p.get("pob_conapo") or 0) / HAB_POR_VIV
    c_n = count_in(gc, comp)
    rows.append(dict(p=p, cnt=cnt, a_raw=a_raw, viv=viv, c_n=c_n, n_scout=sum(cnt_scout.values()),
                     a_dens_desk=a_raw_desk / (viv / 1000.0) if viv > 0 else 0.0,
                     a_dens=a_raw / (viv / 1000.0) if viv > 0 else 0.0,
                     c_dens=c_n / (viv / 1000.0) if viv > 0 else 0.0))

A_star = pct_rank([r["a_dens"] for r in rows])
C_star = pct_rank([r["c_dens"] for r in rows], zero_is_zero=True)
for r, a, c in zip(rows, A_star, C_star):
    d = float(r["p"].get("demanda_star") or 0)
    r["A_star"], r["C_star"], r["D_star"] = float(a), float(c), d
    r["v3"] = 100 * (W_D * d + W_A * a + W_C * (1 - c))
A_desk = pct_rank([r["a_dens_desk"] for r in rows])
for r, a in zip(rows, A_desk):
    r["v3_desk"] = 100 * (W_D * r["D_star"] + W_A * float(a) + W_C * (1 - r["C_star"]))
for rk, i in enumerate(sorted(range(N), key=lambda i: -rows[i]["v3_desk"]), 1): rows[i]["v3_desk_rank"] = rk
order = sorted(range(N), key=lambda i: -rows[i]["v3"])
for rk, i in enumerate(order, 1): rows[i]["v3_rank"] = rk

# ---------- cells ----------
def tree_of(lst, w_fn):
    if not lst: return None, None
    xy = np.array([to_m(a[0], a[1]) for a in lst]); return cKDTree(xy), np.array([w_fn(a) for a in lst])
anc_all = [(a, cat) for cat, lst in anchors.items() if cat != "parada" for a in lst]
anc_tree = cKDTree(np.array([to_m(a[0][0], a[0][1]) for a in anc_all]))
anc_w = np.array([W_ANCHOR[c] for _, c in anc_all])
tr_all = [(a, k) for k, lst in traffic.items() for a in lst]
tr_tree = cKDTree(np.array([to_m(a[0][0], a[0][1]) for a in tr_all]))
tr_w = np.array([W_TRAFFIC[k] for _, k in tr_all])
comp_xy = np.array([to_m(a[0], a[1]) for a in comp]); comp_tree = cKDTree(comp_xy)

cells_by_muni = {}
n_cells_total = 0
for idx, (f, gm) in enumerate(zip(cols, geoms_m)):
    p = f["properties"]; r = rows[idx]; g = prep(gm)
    minx, miny, maxx, maxy = gm.bounds
    x0 = math.floor(minx / CELL) * CELL; y0 = math.floor(miny / CELL) * CELL
    best = []
    x = x0 + CELL / 2
    while x < maxx:
        y = y0 + CELL / 2
        while y < maxy:
            if g.contains(Point(x, y)):
                n_cells_total += 1
                ia = anc_tree.query_ball_point((x, y), R_ANCHOR)
                it = tr_tree.query_ball_point((x, y), R_TRAFFIC)
                ic = comp_tree.query_ball_point((x, y), R_COMP)
                a = float(anc_w[ia].sum()) if ia else 0.0
                t = float(tr_w[it].sum()) if it else 0.0
                if ic:
                    dd = np.hypot(comp_xy[ic, 0] - x, comp_xy[ic, 1] - y)
                    c = float((COMP_PENALTY * (1 - dd / R_COMP)).sum())
                else: c = 0.0
                raw = a + t - c
                s = raw * (0.5 + r["v3"] / 100.0)
                if s > 0:
                    lon, lat = to_ll(x, y)
                    best.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
                                 "properties": {"s": round(s, 1), "a": round(a, 1), "t": round(t, 1), "c": round(c, 1),
                                                "nc": len(ic), "k": p["cve_col"]}})
            y += CELL
        x += CELL
    best.sort(key=lambda ft: -ft["properties"]["s"])
    r["n_cells_pos"] = len(best)
    r["best_cells"] = [ft["geometry"]["coordinates"] + [ft["properties"]["s"]] for ft in best[:5]]
    cells_by_muni.setdefault(p["municipio"], []).extend(best)

def slug(s): return re.sub(r"[^a-z0-9]+", "_", norm(s)).strip("_")
# global normalisation for colour: p95 of s
all_s = np.array([ft["properties"]["s"] for v in cells_by_muni.values() for ft in v])
p95 = float(np.percentile(all_s, 95)) if len(all_s) else 1.0
cell_manifest = {}
for m, fts in cells_by_muni.items():
    fn = f"cells_{slug(m)}.geojson"
    json.dump({"type": "FeatureCollection", "features": fts}, open(os.path.join(OUT, fn), "w"), ensure_ascii=False, separators=(",", ":"))
    cell_manifest[m] = {"file": fn, "n": len(fts)}

# ---------- outputs: colonias v3 ----------
fields = ["v3_rank", "score_v3", "v2_rank", "score_v2", "delta_rank", "cve_col", "municipio", "colonia", "grado", "pob_conapo", "viviendas_est",
          "D_star", "A_star", "C_star", "anclas_pond", "anclas_por_1000viv", "comp_n_300m", "comp_por_1000viv"] + \
         [f"n_{c}" for c in W_ANCHOR] + ["n_anclas_scout", "score_v3_sin_scout", "rank_v3_sin_scout", "cells_pos", "lat", "lon"]
out_rows, feats = [], []
def r4(v): return round(float(v), 4)
for i in order:
    r = rows[i]; p = r["p"]
    o = {"v3_rank": r["v3_rank"], "score_v3": round(r["v3"], 2), "v2_rank": p["rank"], "score_v2": round(float(p["score_100"]), 2),
         "delta_rank": p["rank"] - r["v3_rank"], "cve_col": p["cve_col"], "municipio": p["municipio"], "colonia": p["colonia"], "grado": p["grado"],
         "pob_conapo": round(p["pob_conapo"]), "viviendas_est": round(r["viv"]),
         "D_star": r4(r["D_star"]), "A_star": r4(r["A_star"]), "C_star": r4(r["C_star"]),
         "anclas_pond": round(r["a_raw"], 2), "anclas_por_1000viv": round(r["a_dens"], 2),
         "comp_n_300m": r["c_n"], "comp_por_1000viv": round(r["c_dens"], 3)}
    for c in W_ANCHOR: o[f"n_{c}"] = r["cnt"][c]
    o["n_anclas_scout"] = r["n_scout"]; o["score_v3_sin_scout"] = round(r["v3_desk"], 2); o["rank_v3_sin_scout"] = r["v3_desk_rank"]
    o["cells_pos"] = r["n_cells_pos"]; o["lat"] = p["lat"]; o["lon"] = p["lon"]
    out_rows.append(o)
    props = dict(o); props["best"] = r["best_cells"]; props["cells_file"] = cell_manifest.get(p["municipio"], {}).get("file")
    geom = shape(cols[i]["geometry"]).simplify(0.00003, preserve_topology=True)
    gj = mapping(geom)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "geometry": gj, "properties": props})

with open(os.path.join(OUT, "colonias_v3.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out_rows)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "colonias_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))

# overlay point layers for the v2 map (compact)
def pts_fc(lst, extra):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
            "properties": {"n": a[3][:60], "s": a[2], **extra(a)}} for a in lst]}
anc_ov = [a + (cat,) for cat, lst in anchors.items() if cat not in ("abarrotes",) for a in lst]
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
           "properties": {"n": a[3][:60], "s": a[2], "c": a[4]}} for a in anc_ov]}, open(os.path.join(OUT, "anclas_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(pts_fc(comp, lambda a: {}), open(os.path.join(OUT, "competencia_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
tr_ov = [a + (k,) for k, lst in traffic.items() if k != "parada" for a in lst]
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
           "properties": {"s": a[2], "k": a[4]}} for a in tr_ov]}, open(os.path.join(OUT, "semaforos_altos_v3.geojson"), "w"), separators=(",", ":"))

manifest = {"built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "weights": {"W_D": W_D, "W_A": W_A, "W_C": W_C, "anchor": W_ANCHOR, "traffic": W_TRAFFIC,
                        "R_anchor_m": R_ANCHOR, "R_traffic_m": R_TRAFFIC, "R_comp_m": R_COMP, "comp_penalty": COMP_PENALTY,
                        "cell_m": CELL, "hab_por_viv": HAB_POR_VIV},
            "cells": cell_manifest, "cells_total_in_colonias": n_cells_total, "cells_positive": int(len(all_s)), "cell_s_p95": round(p95, 1),
            "n_colonias": N, **stats}
json.dump(manifest, open(os.path.join(OUT, "manifest_v3.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(manifest, ensure_ascii=False, indent=1))
for o in out_rows[:20]: print(o["v3_rank"], o["score_v3"], o["colonia"], "|", o["municipio"], "| v2 #", o["v2_rank"], "| A", o["anclas_por_1000viv"], "C", o["comp_n_300m"])
