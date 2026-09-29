#!/usr/bin/env python3
"""Rating v3 (colonias) + block heat (100 m cells) + "Dónde poner" + ranking-changes report for v2/ map.

Reads ONLY static files in data/ (read-only) and v2/data/trafico_vias.geojson (run build_trafico_vias_v3.py first).
Writes v2/data/ and docs/CAMBIOS_RANKING_V3.md. Formula + weights: docs/RATING_V3.md. No network calls.

BASE score = uniform-coverage sources only (DENUE, Google Places, OSM).  Scout field marks are a SEPARATE layer
(scout_bonus / score_with_scout) because the survey is concentrated in a few colonias.

  python3 scripts/build_v3_rating.py
"""
from __future__ import annotations
import csv, json, math, os, re, unicodedata, datetime
import numpy as np
from collections import Counter
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
W_TRAFFIC = {             # cell layer only (within 100 m). *_scout only count in the "with Scout" variant
    "semaforo_scout": 2.5, "alto_scout": 2.0,
    "semaforo_osm": 1.0, "alto_osm": 0.75,
    "parada": 1.0,
}
W_FLOW = {2: 0.5, 3: 1.0, 4: 1.5, 5: 1.5}   # cell flow component: best road class (OSM) within R_FLOW; class 5 capped (freeways: no pedestrian access)
R_FLOW = 60.0
SPOT_MIN_DIST = 300.0     # "Dónde poner": greedy spacing between listed spots (avoid 50 adjacent cells of the same block)
TOP_OVERALL, TOP_MUNI = 50, 10
COV_FULL = 10             # ≥10 Scout survey marks inside the colonia = 'encuestada' (label only; not used in any score)
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

# ---------- sources -------------------------------------------------------------------------------
# BASE = DENUE + Places + OSM (+ barrio layers built from those) — uniform coverage.
# SCOUT = field marks (concentrated in a few colonias) → separate evidence layer, never in the headline score.
pl = load("places_anclas_zmm.geojson")
retail = load("retail.geojson")
anc = load("anclas.geojson")

def make_src(scout):
    src = {}
    def add(cat, lst, source, name_key):
        if source == "scout" and not scout: return
        src.setdefault(cat, []).extend((x, y, source, (p.get(name_key) or "")) for x, y, p in lst)
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
    return src

def dedupe_fast(lst, r):
    """keep first (highest priority) point; drop later ones within r metres"""
    if len(lst) < 2: return lst
    xy = np.array([to_m(a[0], a[1]) for a in lst])
    t = cKDTree(xy); drop = np.zeros(len(lst), bool)
    for i in range(len(lst)):
        if drop[i]: continue
        for j in t.query_ball_point(xy[i], r):
            if j > i: drop[j] = True
    return [a for a, d in zip(lst, drop) if not d]

stats = {"anchors_raw": {}, "anchors_dedup_base": {}, "anchors_dedup_with_scout": {}}
anchors_b, anchors_s = {}, {}
for cat, lst in make_src(False).items():
    stats["anchors_raw"][cat] = len(lst); anchors_b[cat] = dedupe_fast(lst, 30.0); stats["anchors_dedup_base"][cat] = len(anchors_b[cat])
for cat, lst in make_src(True).items():
    anchors_s[cat] = dedupe_fast(lst, 30.0); stats["anchors_dedup_with_scout"][cat] = len(anchors_s[cat])

# ---------- traffic points ----------
scout_sema = [(x, y, "scout", "Semáforo") for x, y, p in fa_otro if "semaforo" in norm(p.get("name")) + norm(p.get("nota_raw"))]
scout_sema += [(x, y, "scout", "Semáforo") for x, y, p in fa_kind("semaforo")]
scout_alto = [(x, y, "scout", "Alto") for x, y, p in fa_kind("alto")]
osm_sema = dedupe_fast([(x, y, "osm", "Semáforo") for x, y, p in pts(load("semaforos_zmm.geojson"))], 15.0)
osm_alto = dedupe_fast([(x, y, "osm", "Alto") for x, y, p in pts(load("stops_zmm.geojson"))], 15.0)
def drop_near(base, cand, r):
    if not base: return cand
    t = cKDTree(np.array([to_m(a[0], a[1]) for a in base]))
    return [c for c in cand if not t.query_ball_point(to_m(c[0], c[1]), r)]
scout_all = scout_sema + scout_alto
traffic_b = {"semaforo_osm": osm_sema, "alto_osm": osm_alto, "parada": anchors_b["parada"]}
traffic_s = {"semaforo_scout": dedupe_fast(scout_sema, 15.0), "alto_scout": dedupe_fast(scout_alto, 15.0),
             "semaforo_osm": drop_near(scout_all, osm_sema, 15.0), "alto_osm": drop_near(scout_all, osm_alto, 15.0),
             "parada": anchors_s["parada"]}
stats["traffic_base"] = {k: len(v) for k, v in traffic_b.items()}
stats["traffic_with_scout"] = {k: len(v) for k, v in traffic_s.items()}

# ---------- competition (same rules as docs/COMPETENCIA.md) ----------
EXCL = re.compile(r"bonafont|\bciel\b|\be-?pura\b|santorini|electropura|embotelladora|envasadora|\bcedis\b|industrial|laboratorios|liquitek|coca[- ]?cola|pepsi|bebidas mundiales|arca continental|aqua ?fina|soy sanna", re.I)
SMALL = re.compile(r"^(0 a 5|6 a 10) personas")
def denue_ok(p):
    if EXCL.search((p.get("nombre") or "") + " " + (p.get("razon") or "")): return False
    if str(p.get("canal") or "").startswith("industrial") and not SMALL.search(p.get("estrato") or ""): return False
    return True
comp_scout = [(x, y, "scout", p.get("name") or "") for x, y, p in fa_kind("purificadora")]
comp_scout += [(x, y, "scout", p.get("name") or "") for x, y, p in fa_otro
               if re.search(r"purificador|recarga de agua|garraf", norm(p.get("name")) + " " + norm(p.get("nota_raw")) + " " + norm(p.get("descripcion")))]
comp_desk = [(x, y, "denue", p.get("nombre") or "") for x, y, p in pts(load("compet.geojson"), denue_ok)]
comp_desk += [(x, y, "places", p.get("name") or "") for x, y, p in pts(load("places_purificadoras_zmm.geojson"), lambda p: not EXCL.search(p.get("name") or ""))]
comp_b = dedupe_fast(comp_desk, 30.0)
comp_s = dedupe_fast(comp_scout + comp_desk, 30.0)
stats["comp_raw_base"] = len(comp_desk); stats["comp_dedup_base"] = len(comp_b)
stats["comp_raw_with_scout"] = len(comp_desk) + len(comp_scout); stats["comp_dedup_with_scout"] = len(comp_s)

# ---------- Scout marks (survey evidence; favorito/lock pins are NOT survey marks) ----------
scout_marks = [(x, y, p.get("kind") or "", (p.get("name") or "")) for x, y, p in pts(fa, lambda p: p.get("kind") != "favorito")]
overrides = json.load(open(D("field_adds_overrides.json")))
pins = []
for x, y, p in pts(fa, lambda p: p.get("kind") == "favorito"):
    o = overrides.get(p.get("id"), {})
    locked = bool(o.get("lock") or p.get("lock") or p.get("status") == "lock")
    pins.append((x, y, "lock" if locked else "favorito", p.get("name") or "", p.get("status") or ""))
stats["scout_marks_total"] = len(scout_marks)
stats["scout_marks_by_kind"] = dict(Counter(k for _, _, k, _ in scout_marks))
stats["pins_favorito"] = sum(1 for p in pins if p[2] == "favorito"); stats["pins_lock"] = sum(1 for p in pins if p[2] == "lock")

# ---------- roads (traffic proxy, from v2/data/trafico_vias.geojson) ----------
roads = json.load(open(os.path.join(OUT, "trafico_vias.geojson"), encoding="utf-8"))["features"]
rx, ry, rc, rn = [], [], [], []
for f in roads:
    p = f["properties"]; g = f["geometry"]
    lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for ln in lines:
        m = [to_m(a, b) for a, b in ln]
        for (x1, y1), (x2, y2) in zip(m[:-1], m[1:]):
            L_ = math.hypot(x2 - x1, y2 - y1); n = max(1, int(L_ // 10))
            for k in range(n + 1):
                t = k / n; rx.append(x1 + (x2 - x1) * t); ry.append(y1 + (y2 - y1) * t); rc.append(p["i"]); rn.append(p.get("n") or p.get("r") or "")
rc = np.array(rc); rxy = np.column_stack([rx, ry])
ave = rc >= 2                                   # avenues: class 2–5 (links = 1 are ramps, not flow)
ave_tree = cKDTree(rxy[ave]); ave_c = rc[ave]; ave_n = [n for n, a in zip(rn, ave) if a]
def flow_class(x, y):
    """max road class (2–5) within R_FLOW m; 0 if none"""
    ii = ave_tree.query_ball_point((x, y), R_FLOW)
    return int(ave_c[ii].max()) if ii else 0
def nearest_ave(x, y, rmax=300.0):
    d, i = ave_tree.query((x, y), distance_upper_bound=rmax)
    if not np.isfinite(d): return None
    return {"clase": int(ave_c[i]), "nombre": ave_n[i], "dist_m": int(round(d))}

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
def items_in(geom_m, lst):
    g = prep(geom_m); minx, miny, maxx, maxy = geom_m.bounds; out = []
    for a in lst:
        x, y = to_m(a[0], a[1])
        if minx <= x <= maxx and miny <= y <= maxy and g.contains(Point(x, y)): out.append(a)
    return out

def pct_rank(vals, zero_is_zero=False):
    v = np.array(vals, float); order = v.argsort(kind="stable")
    ranks = np.empty(len(v)); sv = v[order]; i = 0
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
    viv = (p.get("pob_conapo") or 0) / HAB_POR_VIV
    kv = viv / 1000.0 if viv > 0 else None
    cnt_b = {c: count_in(ga, l) for c, l in anchors_b.items()}
    cnt_s = {c: count_in(ga, l) for c, l in anchors_s.items()}
    a_b = sum(W_ANCHOR[c] * n for c, n in cnt_b.items()); a_s = sum(W_ANCHOR[c] * n for c, n in cnt_s.items())
    c_b = count_in(gc, comp_b); c_s = count_in(gc, comp_s)
    marks = items_in(gm, scout_marks); kinds = Counter(m[2] for m in marks)
    npin = items_in(gm, pins)
    rows.append(dict(p=p, cnt=cnt_b, cnt_s=cnt_s, a_raw=a_b, a_raw_s=a_s, viv=viv, c_n=c_b, c_n_s=c_s,
                     a_dens=a_b / kv if kv else 0.0, a_dens_s=a_s / kv if kv else 0.0,
                     c_dens=c_b / kv if kv else 0.0, c_dens_s=c_s / kv if kv else 0.0,
                     n_scout_marks=len(marks), scout_kinds=";".join(f"{k}:{n}" for k, n in sorted(kinds.items())),
                     n_pin_fav=sum(1 for q in npin if q[2] == "favorito"), n_pin_lock=sum(1 for q in npin if q[2] == "lock"),
                     n_scout_anchor_used=sum(cnt_s.values()) - sum(cnt_b.values())))

A_b = pct_rank([r["a_dens"] for r in rows]); C_b = pct_rank([r["c_dens"] for r in rows], True)
A_s = pct_rank([r["a_dens_s"] for r in rows]); C_s = pct_rank([r["c_dens_s"] for r in rows], True)
for r, ab, cb, as_, cs in zip(rows, A_b, C_b, A_s, C_s):
    d = float(r["p"].get("demanda_star") or 0)
    r.update(D_star=d, A_star=float(ab), C_star=float(cb), A_star_s=float(as_), C_star_s=float(cs))
    r["base"] = 100 * (W_D * d + W_A * ab + W_C * (1 - cb))
    r["withs"] = 100 * (W_D * d + W_A * as_ + W_C * (1 - cs))
    r["bonus"] = r["withs"] - r["base"]
order = sorted(range(N), key=lambda i: -rows[i]["base"])
for rk, i in enumerate(order, 1): rows[i]["rank_base"] = rk
for rk, i in enumerate(sorted(range(N), key=lambda i: -rows[i]["withs"]), 1): rows[i]["rank_scout"] = rk

# coverage of field survey (Scout marks inside polygon, excluding favorito pins)
def cobertura(n): return "sin encuesta" if n == 0 else ("parcial" if n < COV_FULL else "encuestada")
for r in rows: r["cobertura"] = cobertura(r["n_scout_marks"])

# ---------- why did rank move? (v2 → v3 base) ----------
# v2 = 40·D + 25·(1−Comp2*) + 20·A2* + 15·(1−Canibal*)   (Canibal*=0 for all → +15 constant)
# v3 = 40·D + 30·A3* + 30·(1−C3*)                      → D identical; only anchors and competition terms differ.
for r in rows:
    p = r["p"]
    r["dA_raw"] = W_A * 100 * r["A_star"] - 20 * p["anclas_star"]
    r["dC_raw"] = W_C * 100 * (1 - r["C_star"]) - 25 * (1 - p["comp_star"])
mA = float(np.mean([r["dA_raw"] for r in rows])); mC = float(np.mean([r["dC_raw"] for r in rows]))
for r in rows:   # centred: subtract the average shift (a uniform shift does not change ranks)
    r["dA"] = r["dA_raw"] - mA; r["dC"] = r["dC_raw"] - mC
    dom = "anclas" if abs(r["dA"]) >= abs(r["dC"]) else "competencia"
    r["cause_main"] = dom
    r["cause_txt"] = f"anclas {r['dA']:+.1f} pts, competencia {r['dC']:+.1f} pts (demanda 0.0)"
    ds = W_A * 100 * (r["A_star_s"] - r["A_star"]); dcs = W_C * 100 * (r["C_star"] - r["C_star_s"])
    r["scout_dA"], r["scout_dC"] = ds, dcs
    r["scout_cause"] = ("anclas" if abs(ds) >= abs(dcs) else "competencia") if abs(ds) + abs(dcs) > 1e-9 else "—"

# ---------- cells ----------
class Var:
    def __init__(s, anchors, traffic, comp, wt):
        anc_all = [(a, cat) for cat, lst in anchors.items() if cat != "parada" for a in lst]
        s.anc_t = cKDTree(np.array([to_m(a[0][0], a[0][1]) for a in anc_all]))
        s.anc_w = np.array([W_ANCHOR[c] for _, c in anc_all]); s.anc_cat = [c for _, c in anc_all]
        tr_all = [(a, k) for k, lst in traffic.items() for a in lst]
        s.tr_t = cKDTree(np.array([to_m(a[0][0], a[0][1]) for a in tr_all]))
        s.tr_w = np.array([W_TRAFFIC[k] for _, k in tr_all]); s.tr_k = [k for _, k in tr_all]
        s.comp_xy = np.array([to_m(a[0], a[1]) for a in comp]); s.comp_t = cKDTree(s.comp_xy)
    def eval(s, x, y):
        ia = s.anc_t.query_ball_point((x, y), R_ANCHOR); it = s.tr_t.query_ball_point((x, y), R_TRAFFIC)
        ic = s.comp_t.query_ball_point((x, y), R_COMP)
        a = float(s.anc_w[ia].sum()) if ia else 0.0; t = float(s.tr_w[it].sum()) if it else 0.0
        c = float((COMP_PENALTY * (1 - np.hypot(s.comp_xy[ic, 0] - x, s.comp_xy[ic, 1] - y) / R_COMP)).sum()) if ic else 0.0
        return a, t, c, len(ic), ia, it
VB = Var(anchors_b, traffic_b, comp_b, None); VS = Var(anchors_s, traffic_s, comp_s, None)
sm_xy = np.array([to_m(a[0], a[1]) for a in scout_marks]); sm_t = cKDTree(sm_xy)
pin_xy = np.array([to_m(a[0], a[1]) for a in pins]); pin_t = cKDTree(pin_xy)

all_cells = []          # for "Dónde poner"
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
                fi = flow_class(x, y); fl = W_FLOW.get(fi, 0.0)
                a, t, c, nc, _, _ = VB.eval(x, y)
                s = (a + t + fl - c) * (0.5 + r["base"] / 100.0)
                if s > 0:
                    a2, t2, c2, nc2, _, _ = VS.eval(x, y)
                    s2 = (a2 + t2 + fl - c2) * (0.5 + r["withs"] / 100.0)
                    sm = len(sm_t.query_ball_point((x, y), R_ANCHOR))
                    lon, lat = to_ll(x, y)
                    ft = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
                          "properties": {"s": round(s, 1), "a": round(a, 1), "t": round(t, 1), "f": round(fl, 1), "fi": fi, "c": round(c, 1),
                                         "nc": nc, "sm": sm, "sb": round(s2 - s, 1), "k": p["cve_col"]}}
                    best.append(ft)
                    all_cells.append((s, x, y, lon, lat, idx, ft["properties"]))
            y += CELL
        x += CELL
    best.sort(key=lambda ft: -ft["properties"]["s"])
    r["n_cells_pos"] = len(best)
    r["best_cells"] = [ft["geometry"]["coordinates"] + [ft["properties"]["s"]] for ft in best[:5]]
    cells_by_muni.setdefault(p["municipio"], []).extend(best)

def slug(s): return re.sub(r"[^a-z0-9]+", "_", norm(s)).strip("_")
all_s = np.array([ft["properties"]["s"] for v in cells_by_muni.values() for ft in v])
p95 = float(np.percentile(all_s, 95)) if len(all_s) else 1.0
cell_manifest = {}
for m, fts in cells_by_muni.items():
    fn = f"cells_{slug(m)}.geojson"
    json.dump({"type": "FeatureCollection", "features": fts}, open(os.path.join(OUT, fn), "w"), ensure_ascii=False, separators=(",", ":"))
    cell_manifest[m] = {"file": fn, "n": len(fts)}

# ---------- "Dónde poner": greedy spacing over base cell score ----------
all_cells.sort(key=lambda c: -c[0])
chosen, chosen_xy = [], np.zeros((0, 2))
_buf = []
for c in all_cells:
    if _buf and np.min(np.hypot(np.array(_buf)[:, 0] - c[1], np.array(_buf)[:, 1] - c[2])) < SPOT_MIN_DIST: continue
    chosen.append(c); _buf.append((c[1], c[2]))
# competitors found only by Scout (no DENUE/Places point within 30 m): shown apart in the spot rows
_bt = cKDTree(np.array([to_m(a[0], a[1]) for a in comp_b]))
comp_scout_new = [a for a in comp_s if a[2] == "scout" and not _bt.query_ball_point(to_m(a[0], a[1]), 30.0)]
csn_xy = np.array([to_m(a[0], a[1]) for a in comp_scout_new]) if comp_scout_new else np.zeros((0, 2))
spot_rows, overall_idx, muni_idx = [], [], {m: [] for m in cells_by_muni}
muni_seen = Counter()
for rank_all, c in enumerate(chosen, 1):
    s, x, y, lon, lat, ci, cp = c
    m = cols[ci]["properties"]["municipio"]
    take_overall = len(overall_idx) < TOP_OVERALL
    take_muni = muni_seen[m] < TOP_MUNI
    if not (take_overall or take_muni): continue
    muni_seen[m] += 1
    r = rows[ci]
    _, _, _, _, ia, it = VB.eval(x, y)
    by_cat = Counter(VB.anc_cat[i] for i in ia)
    tk = Counter(VB.tr_k[i] for i in it)
    dd = np.hypot(VB.comp_xy[:, 0] - x, VB.comp_xy[:, 1] - y)
    near_c = int(round(float(dd.min()))) if len(dd) else None
    sm_i = sm_t.query_ball_point((x, y), R_ANCHOR)
    sm_kinds = Counter(scout_marks[i][2] for i in sm_i)
    pin_i = pin_t.query_ball_point((x, y), R_ANCHOR)
    row = {"rank_zmm": None, "rank_muni": None, "colonia": r["p"]["colonia"], "municipio": m, "cve_col": r["p"]["cve_col"],
           "lat": round(lat, 5), "lon": round(lon, 5), "cell_score": cp["s"], "colonia_score_base": round(r["base"], 1), "colonia_rank_base": r["rank_base"],
           "anclas_pond": cp["a"], "anclas_150m": {k: n for k, n in sorted(by_cat.items(), key=lambda kv: -kv[1])},
           "semaforos_osm_100m": tk.get("semaforo_osm", 0), "altos_osm_100m": tk.get("alto_osm", 0), "paradas_100m": tk.get("parada", 0),
           "trafico_pts": cp["t"], "flujo_pts": cp["f"], "avenida_cercana": nearest_ave(x, y),
           "competidor_mas_cercano_m": near_c, "competidores_300m": cp["nc"], "castigo_comp": cp["c"],
           "purif_scout_extra_300m": int((np.hypot(csn_xy[:, 0] - x, csn_xy[:, 1] - y) <= R_COMP).sum()) if len(csn_xy) else 0,
           "scout_marks_150m": {k: n for k, n in sm_kinds.items()}, "scout_bonus_celda": cp["sb"],
           "pines": [{"tipo": pins[i][2], "nombre": pins[i][3], "dist_m": int(round(math.hypot(pin_xy[i][0] - x, pin_xy[i][1] - y)))} for i in pin_i],
           "gmaps": f"https://www.google.com/maps?q={lat:.5f},{lon:.5f}"}
    idx_row = len(spot_rows); spot_rows.append(row)
    if take_overall: overall_idx.append(idx_row); row["rank_zmm"] = len(overall_idx)
    if take_muni: muni_idx[m].append(idx_row); row["rank_muni"] = len(muni_idx[m])
spots = {"note": "Índice de flujo = clase de vía OSM (1–5), proxy jerárquico, NO aforo. Score = base (sin Scout). Separación mínima entre spots: %d m." % SPOT_MIN_DIST,
         "rows": spot_rows, "overall": overall_idx, "muni": muni_idx,
         "params": {"min_dist_m": SPOT_MIN_DIST, "top_overall": TOP_OVERALL, "top_muni": TOP_MUNI, "r_anchor": R_ANCHOR, "r_traffic": R_TRAFFIC,
                    "r_comp": R_COMP, "r_flow": R_FLOW, "w_flow": W_FLOW}}
json.dump(spots, open(os.path.join(OUT, "spots_v3.json"), "w"), ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(OUT, "spots_v3.csv"), "w", newline="", encoding="utf-8") as fh:
    cols_ = ["rank_zmm", "rank_muni", "municipio", "colonia", "cell_score", "colonia_score_base", "colonia_rank_base", "anclas_pond", "anclas_150m",
             "semaforos_osm_100m", "altos_osm_100m", "paradas_100m", "flujo_pts", "avenida_clase", "avenida_nombre", "avenida_dist_m",
             "competidor_mas_cercano_m", "competidores_300m", "purif_scout_extra_300m", "scout_marks_150m", "scout_bonus_celda", "pines", "lat", "lon", "gmaps"]
    w = csv.DictWriter(fh, fieldnames=cols_); w.writeheader()
    for rw in spot_rows:
        av = rw["avenida_cercana"] or {}
        w.writerow({**{k: rw.get(k) for k in cols_ if k in rw}, "anclas_150m": ";".join(f"{k}:{n}" for k, n in rw["anclas_150m"].items()),
                    "avenida_clase": av.get("clase", ""), "avenida_nombre": av.get("nombre", ""), "avenida_dist_m": av.get("dist_m", ""),
                    "scout_marks_150m": ";".join(f"{k}:{n}" for k, n in rw["scout_marks_150m"].items()),
                    "pines": ";".join(f"{q['tipo']}:{q['nombre']}({q['dist_m']}m)" for q in rw["pines"])})

# ---------- outputs: colonias v3 ----------
fields = ["rank_base", "score_base", "rank_with_scout", "score_with_scout", "scout_bonus", "scout_marks", "cobertura_campo", "scout_marks_kinds",
          "scout_anchor_marks_used", "pins_favorito", "pins_lock", "v2_rank", "score_v2", "delta_rank_v2_to_base", "delta_rank_base_to_scout",
          "cause_main", "cause_anclas_pts", "cause_competencia_pts", "scout_cause", "cve_col", "municipio", "colonia", "grado", "pob_conapo", "viviendas_est",
          "D_star", "A_star", "C_star", "anclas_pond", "anclas_por_1000viv", "comp_n_300m", "comp_por_1000viv"] + \
         [f"n_{c}" for c in W_ANCHOR] + ["comp_n_300m_with_scout", "cells_pos", "lat", "lon"]
out_rows, feats = [], []
def r4(v): return round(float(v), 4)
for i in order:
    r = rows[i]; p = r["p"]
    o = {"rank_base": r["rank_base"], "score_base": round(r["base"], 2), "rank_with_scout": r["rank_scout"], "score_with_scout": round(r["withs"], 2),
         "scout_bonus": round(r["bonus"], 2), "scout_marks": r["n_scout_marks"], "cobertura_campo": r["cobertura"], "scout_marks_kinds": r["scout_kinds"],
         "scout_anchor_marks_used": r["n_scout_anchor_used"], "pins_favorito": r["n_pin_fav"], "pins_lock": r["n_pin_lock"],
         "v2_rank": p["rank"], "score_v2": round(float(p["score_100"]), 2), "delta_rank_v2_to_base": p["rank"] - r["rank_base"],
         "delta_rank_base_to_scout": r["rank_base"] - r["rank_scout"], "cause_main": r["cause_main"],
         "cause_anclas_pts": round(r["dA"], 2), "cause_competencia_pts": round(r["dC"], 2), "scout_cause": r["scout_cause"],
         "cve_col": p["cve_col"], "municipio": p["municipio"], "colonia": p["colonia"], "grado": p["grado"],
         "pob_conapo": round(p["pob_conapo"]), "viviendas_est": round(r["viv"]),
         "D_star": r4(r["D_star"]), "A_star": r4(r["A_star"]), "C_star": r4(r["C_star"]),
         "anclas_pond": round(r["a_raw"], 2), "anclas_por_1000viv": round(r["a_dens"], 2),
         "comp_n_300m": r["c_n"], "comp_por_1000viv": round(r["c_dens"], 3)}
    for c in W_ANCHOR: o[f"n_{c}"] = r["cnt"][c]
    o["comp_n_300m_with_scout"] = r["c_n_s"]; o["cells_pos"] = r["n_cells_pos"]; o["lat"] = p["lat"]; o["lon"] = p["lon"]
    out_rows.append(o)
    props = dict(o); props["best"] = r["best_cells"]; props["cells_file"] = cell_manifest.get(p["municipio"], {}).get("file")
    props["A_star_scout"] = r4(r["A_star_s"]); props["C_star_scout"] = r4(r["C_star_s"])
    geom = shape(cols[i]["geometry"]).simplify(0.00003, preserve_topology=True)
    gj = mapping(geom)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "geometry": gj, "properties": props})

with open(os.path.join(OUT, "colonias_v3.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out_rows)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "colonias_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))

# overlay point layers for the v2 map (compact). Anchors/semáforos: base sources + Scout ones flagged s="scout" (separate layer in UI).
anc_base_keys = {(round(a[0], 5), round(a[1], 5), cat) for cat, lst in anchors_b.items() for a in lst}
anc_ov = [a + (cat,) for cat, lst in anchors_b.items() if cat != "abarrotes" for a in lst]
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
           "properties": {"n": a[3][:60], "s": a[2], "c": a[4]}} for a in anc_ov]}, open(os.path.join(OUT, "anclas_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
           "properties": {"n": a[3][:60], "s": a[2]}} for a in comp_b]}, open(os.path.join(OUT, "competencia_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
tr_ov = [a + (k,) for k, lst in traffic_b.items() if k != "parada" for a in lst]
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]},
           "properties": {"s": a[2], "k": a[4]}} for a in tr_ov]}, open(os.path.join(OUT, "semaforos_altos_v3.geojson"), "w"), separators=(",", ":"))
# Scout layer (separate): survey marks + favorito/lock pins. Names only — no phones/contacts.
sc_feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]}, "properties": {"k": a[2], "n": a[3][:60]}} for a in scout_marks]
sc_feats += [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(a[0], 5), round(a[1], 5)]}, "properties": {"k": a[2], "n": a[3][:60]}} for a in pins]
json.dump({"type": "FeatureCollection", "features": sc_feats}, open(os.path.join(OUT, "scout_marks_v3.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))

# ---------- ranking-change summaries ----------
munis = sorted({r["p"]["municipio"] for r in rows})
def top_counts(key_rank, n):
    c = Counter(r["p"]["municipio"] for r in rows if key_rank(r) <= n); return {m: c.get(m, 0) for m in munis}
muni_summary = {m: {"colonias": sum(1 for r in rows if r["p"]["municipio"] == m),
                    "top20_v2": top_counts(lambda r: r["p"]["rank"], 20)[m], "top20_base": top_counts(lambda r: r["rank_base"], 20)[m], "top20_scout": top_counts(lambda r: r["rank_scout"], 20)[m],
                    "top50_v2": top_counts(lambda r: r["p"]["rank"], 50)[m], "top50_base": top_counts(lambda r: r["rank_base"], 50)[m], "top50_scout": top_counts(lambda r: r["rank_scout"], 50)[m]} for m in munis}
def mover(r): return r["p"]["rank"] - r["rank_base"]
ups = sorted(rows, key=lambda r: -mover(r))[:10]; downs = sorted(rows, key=lambda r: mover(r))[:10]
def mv_row(r): return {"colonia": r["p"]["colonia"], "municipio": r["p"]["municipio"], "v2_rank": r["p"]["rank"], "rank_base": r["rank_base"], "rank_scout": r["rank_scout"],
                       "delta": mover(r), "cause": r["cause_main"], "dA": round(r["dA"], 1), "dC": round(r["dC"], 1), "cve_col": r["p"]["cve_col"]}
cambios = {"muni_summary": muni_summary, "ups": [mv_row(r) for r in ups], "downs": [mv_row(r) for r in downs],
           "scout_ups": [mv_row(r) | {"scout_delta": r["rank_base"] - r["rank_scout"], "scout_cause": r["scout_cause"]} for r in sorted(rows, key=lambda r: -(r["rank_base"] - r["rank_scout"]))[:5]],
           "mean_shift": {"anclas_pts": round(mA, 2), "competencia_pts": round(mC, 2)}}
json.dump(cambios, open(os.path.join(OUT, "cambios_v3.json"), "w"), ensure_ascii=False, separators=(",", ":"))

cov = Counter(r["cobertura"] for r in rows)
manifest = {"built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "weights": {"W_D": W_D, "W_A": W_A, "W_C": W_C, "anchor": W_ANCHOR, "traffic": W_TRAFFIC, "flow_by_road_class": {str(k): v for k, v in W_FLOW.items()},
                        "R_anchor_m": R_ANCHOR, "R_traffic_m": R_TRAFFIC, "R_comp_m": R_COMP, "R_flow_m": R_FLOW, "comp_penalty": COMP_PENALTY,
                        "cell_m": CELL, "hab_por_viv": HAB_POR_VIV, "cobertura_full_marks": COV_FULL, "spot_min_dist_m": SPOT_MIN_DIST},
            "cells": cell_manifest, "cells_total_in_colonias": n_cells_total, "cells_positive": int(len(all_s)), "cell_s_p95": round(p95, 1),
            "n_colonias": N, "cobertura_campo": dict(cov), "scout_base_rank_spearman_note": "ver docs/CAMBIOS_RANKING_V3.md", **stats}
json.dump(manifest, open(os.path.join(OUT, "manifest_v3.json"), "w"), ensure_ascii=False, indent=1)

# ---------- docs/CAMBIOS_RANKING_V3.md ----------
def md_rows(lst, extra=None):
    return lst
L_ = []
w_ = L_.append
w_("# Cambios de ranking: v2 → v3 base → v3 con Scout\n")
w_(f"_Generado por `scripts/build_v3_rating.py` (build {manifest['built_at']}). Todos los valores salen de `v2/data/colonias_v3.csv`._\n")
w_("- **v2** = ranking del mapa actual (`score_100`: 0.40 Demanda + 0.25 (1−Comp) + 0.20 Anclas + 0.15 (1−Canibal, constante)).")
w_("- **v3 base** = 0.40 Demanda + 0.30 Anclas + 0.30 (1−Comp) con **sólo DENUE + Places + OSM** (titular).")
w_("- **v3 con Scout** = misma fórmula sumando marcas Scout (anclas, competencia). Se muestra aparte; el bonus es evidencia de campo, no ranking base.\n")
w_("## Por qué se mueven las colonias\n")
w_("La **Demanda\\*** es idéntica (mismo valor, mismo peso 0.40), así que **nunca** explica un cambio. Sólo cambian dos términos:\n")
w_("- **Anclas**: v2 `20·Anclas*_v2` (ponderación por tipo, por cercanía al centroide) → v3 `30·Anclas*` (conteo ponderado en polígono+100 m por 1 000 viv., percentil).")
w_("- **Competencia**: v2 `25·(1−Comp*_v2)` → v3 `30·(1−Comp*)` (purificadoras ≤300 m del polígono por 1 000 viv., percentil; 0 ⇒ máximo).")
w_("- El +15 de Canibal (v2) es igual para todas y no mueve ranks.")
w_(f"- Puntos por causa están **centrados** (se resta el desplazamiento medio: anclas {mA:+.2f}, competencia {mC:+.2f}) para que sólo reflejen movimiento relativo. `causa` = término con mayor |Δ|.\n")
w_("## Resumen por municipio: cuántas colonias en top 20 / top 50\n")
w_("| Municipio | Colonias | Top20 v2 | Top20 base | Top20 +Scout | Top50 v2 | Top50 base | Top50 +Scout |\n|---|--:|--:|--:|--:|--:|--:|--:|")
for m in munis:
    s = muni_summary[m]; w_(f"| {m} | {s['colonias']} | {s['top20_v2']} | {s['top20_base']} | {s['top20_scout']} | {s['top50_v2']} | {s['top50_base']} | {s['top50_scout']} |")
w_("\n## Top 10 v3 base\n")
w_("| # base | Colonia | Municipio | Score base | # v2 | # con Scout | Marcas Scout | Cobertura | Anclas/1000 viv | Purif. ≤300 m | Demanda* | Anclas* | Comp* |\n|--:|---|---|--:|--:|--:|--:|---|--:|--:|--:|--:|--:|")
for i in order[:10]:
    r = rows[i]; p = r["p"]
    w_(f"| {r['rank_base']} | {p['colonia']} | {p['municipio']} | {r['base']:.1f} | {p['rank']} | {r['rank_scout']} | {r['n_scout_marks']} | {r['cobertura']} | {r['a_dens']:.1f} | {r['c_n']} | {r['D_star']:.2f} | {r['A_star']:.2f} | {r['C_star']:.2f} |")
def mtab(lst):
    w_("| Colonia | Municipio | # v2 | # base | Δ | Causa | Δ anclas (pts) | Δ comp. (pts) |\n|---|---|--:|--:|--:|---|--:|--:|")
    for r in lst:
        w_(f"| {r['p']['colonia']} | {r['p']['municipio']} | {r['p']['rank']} | {r['rank_base']} | {mover(r):+d} | {r['cause_main']} | {r['dA']:+.1f} | {r['dC']:+.1f} |")
w_("\n## Top 10 que suben (v2 → v3 base)\n"); mtab(ups)
w_("\n## Top 10 que bajan (v2 → v3 base)\n"); mtab(downs)
w_("\n## Efecto Scout (base → con Scout): mayores subidas / bajadas\n")
w_("| Colonia | Municipio | # base | # con Scout | Δ | Marcas Scout | Bonus (pts) | Causa |\n|---|---|--:|--:|--:|--:|--:|---|")
for r in sorted(rows, key=lambda r: -(r["rank_base"] - r["rank_scout"]))[:8] + sorted(rows, key=lambda r: (r["rank_base"] - r["rank_scout"]))[:5]:
    w_(f"| {r['p']['colonia']} | {r['p']['municipio']} | {r['rank_base']} | {r['rank_scout']} | {r['rank_base']-r['rank_scout']:+d} | {r['n_scout_marks']} | {r['bonus']:+.1f} | {r['scout_cause']} |")
w_(f"\nCobertura de campo: {cov.get('sin encuesta',0)} colonias **sin encuesta** (0 marcas Scout), {cov.get('parcial',0)} parciales (1–{COV_FULL-1}), {cov.get('encuestada',0)} encuestadas (≥{COV_FULL}).\n")
w_("## Tabla completa (167 colonias)\n")
w_("| Colonia | Municipio | # v2 | # base | # +Scout | Δ v2→base | Causa | Marcas Scout | Cobertura |\n|---|---|--:|--:|--:|--:|---|--:|---|")
for i in order:
    r = rows[i]; p = r["p"]
    w_(f"| {p['colonia']} | {p['municipio']} | {p['rank']} | {r['rank_base']} | {r['rank_scout']} | {mover(r):+d} | {r['cause_main']} ({r['dA']:+.1f}/{r['dC']:+.1f}) | {r['n_scout_marks']} | {r['cobertura']} |")
open(os.path.join(ROOT, "docs", "CAMBIOS_RANKING_V3.md"), "w", encoding="utf-8").write("\n".join(L_) + "\n")

print(json.dumps({k: manifest[k] for k in ("cells_positive", "cobertura_campo", "scout_marks_by_kind", "pins_favorito", "pins_lock", "comp_dedup_base", "comp_dedup_with_scout")}, ensure_ascii=False))
for i in order[:12]:
    r = rows[i]; print(r["rank_base"], round(r["base"], 2), r["p"]["colonia"], "|", r["p"]["municipio"], "| v2 #", r["p"]["rank"], "| scout #", r["rank_scout"], "| marks", r["n_scout_marks"])
