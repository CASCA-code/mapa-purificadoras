#!/usr/bin/env python3
"""v3_espectaculares build (OFFLINE; no API calls, no keys).

Inputs (read-only):
  data/anclas_paradas_zmm.geojson  (Places+OSM bus stops, 2005)       data/anclas.geojson (escuela/iglesia/hospital)
  v2/data/anclas_v3.geojson (oxxo/banco/express...)                    v2/data/trafico_vias.geojson (display copy)
  /workspace/downloads/osm_paradas_raw.json     <- scripts/fetch_osm_paradas_espectaculares.py (Overpass)
  /workspace/downloads/osm_vias_oneway_raw.json <- scripts/fetch_osm_vias_oneway.py (Overpass, oneway/ref/name)
  data/roads_zmm.geojson (local streets, fallback; no names/oneway tags)  data/muni.geojson
  TomTom (EG-fabricas, INTERNAL; only AGGREGATES shipped): /home/box/geo/trafico/trafico.db (ro),
     /home/box/geo/base_mty/out/trafico_factor_pico_valle.csv
  EG-personas (optional): /workspace/estudio-peatonal/out/segmentos_general.csv
Outputs: v3_espectaculares/data/*  (see README.md)
"""
import csv, json, math, os, sqlite3, statistics, sys
import numpy as np
from shapely.geometry import LineString, Point, shape
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "v3_espectaculares", "data")
os.makedirs(OUT, exist_ok=True)
J = lambda *p: os.path.join(ROOT, *p)

# ---------------- PARAMS (judgment values, NOT calibrated; documented in README) ----------------
PARAMS = {
    "radius_bus_m": 80,        # visibility zone, bus stop
    "radius_station_m": 150,   # metro / BRT / terminal
    "people_radius_m": 150,    # density of stops + anchors
    "w_stop_self": {"bus": 1.0, "brt": 2.0, "metro": 3.0, "terminal": 3.0},  # evidence of waiting people
    "w_other_stop": 1.0,       # each other distinct stop within people_radius
    "w_anchor": {"escuela": 1.0, "iglesia": 1.0, "hospital": 1.0, "banco": 1.0, "oxxo": 1.0, "express": 1.0},
    "w_people_density": 0.6, "w_people_pie": 0.4,   # pie = EG-personas modeled score of nearest segment (<=PIE_MAX_M)
    "pie_max_m": 80,
    "cap_other_stops": 15, "cap_anchors": 15,
    "dedupe_cross_source_m": 20,   # OSM > anclas_paradas(osm) > Places
    "station_cluster_m": 200,
    "nms_m": 200,              # one candidate per site in the ranking
    "top_n": 100,
}
CLASS_IDX = {"motorway": 5, "trunk": 5, "primary": 4, "secondary": 3, "tertiary": 2}  # same as v2 (links=1)
LAT0 = 25.70
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574.0
def px(lon, lat): return ((lon + 100.35) * KX, (lat - LAT0) * KY)
def unpx(x, y): return (x / KX - 100.35, y / KY + LAT0)
def hav_ok(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
COMP = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
def comp(b): return COMP[int(((b % 360) + 22.5) // 45) % 8]

# ---------------- municipalities ----------------
muni = [(f["properties"]["nom"], shape(f["geometry"])) for f in json.load(open(J("data", "muni.geojson")))["features"]]
def muni_of(lon, lat):
    p = Point(lon, lat)
    for n, g in muni:
        if g.contains(p): return n
    return None

# ---------------- TomTom aggregates (INTERNAL, 1 day, indicative) ----------------
tt = {}
dbp = "/home/box/geo/trafico/trafico.db"
if os.path.exists(dbp):
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    rows = c.execute("""select t.municipio, t.tramo_id, m.slot, m.tiempo_actual_s from tramos t join muestras m on m.tramo_id=t.tramo_id
                        where m.tipo_tiempo='historico_departAt' and m.tiempo_actual_s>0""").fetchall()
    by = {}
    for mu, tid, slot, t in rows: by.setdefault((mu, tid), {})[slot] = t
    agg = {}
    for (mu, tid), s in by.items():
        if "2200" not in s: continue
        for slot in ("0600", "0700", "0800", "1300", "1800"):
            if slot in s: agg.setdefault(mu, {}).setdefault(slot, []).append(s[slot] / s["2200"])
    for mu, d in agg.items():
        npar = len(d.get("0700", []))
        if npar < 4: continue   # privacy/robustness: skip tiny groups
        tt[mu] = {"n_pares": npar, **{"f" + k: round(statistics.median(v), 3) for k, v in d.items()}}
    allv = {k: [x for d in agg.values() for x in d.get(k, [])] for k in ("0700", "1800")}
    tt["_ZMM_total"] = {"n_pares": len(allv["0700"]), **{"f" + k: round(statistics.median(v), 3) for k, v in allv.items()}}
else:
    print("WARN: trafico.db not found; municipal multiplier = 1.0", file=sys.stderr)
TT_DEFAULT = tt.get("_ZMM_total", {"f0700": 1.0, "f1800": 1.0})
def mult_of(mu):
    d = tt.get(mu)
    if d: return round((d["f0700"] + d["f1800"]) / 2, 3), True
    return round((TT_DEFAULT["f0700"] + TT_DEFAULT["f1800"]) / 2, 3), False

# ---------------- stops ----------------
raw = json.load(open("/workspace/downloads/osm_paradas_raw.json"))["elements"]
def ctr(e): return (e["lon"], e["lat"]) if e["type"] == "node" else (e["center"]["lon"], e["center"]["lat"])
bus, st_pts = [], []   # bus: dict; station-class elements
for e in raw:
    t = e.get("tags", {})
    lon, lat = ctr(e)
    if t.get("railway") == "construction" or t.get("railway") == "station" and t.get("station") is None and "construction" in str(t): pass
    if t.get("railway") == "construction": continue
    is_rail = t.get("railway") in ("station", "subway_entrance", "halt") or t.get("station") in ("subway", "light_rail")
    is_pt_station = t.get("public_transport") == "station" and t.get("amenity") != "ferry_terminal" and t.get("station") != "ferry"
    is_term = t.get("amenity") == "bus_station"
    if t.get("amenity") == "ferry_terminal": continue
    if is_rail or (is_pt_station and not is_term):
        st_pts.append((lon, lat, e, "rail")); continue
    if is_term:
        net_ = ((t.get("network") or "") + " " + (t.get("operator") or "")).lower()
        st_pts.append((lon, lat, e, "brt" if ("ecov" in net_ or "transmetro" in net_) else "terminal")); continue
    if t.get("highway") == "bus_stop" or (t.get("public_transport") == "platform" and e["type"] == "node" and t.get("railway") is None and t.get("bus") == "yes"):
        net = (t.get("network") or "") + " " + (t.get("operator") or "")
        typ = "brt" if "transmetro" in net.lower() or "ecov" in net.lower() else "bus"
        bus.append(dict(lon=lon, lat=lat, type=typ, name=t.get("name", ""), ref=t.get("ref", ""), route_ref=t.get("route_ref", ""),
                        network=t.get("network", ""), direction=t.get("direction", ""), src="osm", osm_id=f'{e["type"][0]}{e["id"]}'))
# cluster stations
stations = []
for lon, lat, e, kind in sorted(st_pts, key=lambda r: (r[3] != "rail", r[3] != "brt", r[2].get("tags", {}).get("name") is None)):
    p = px(lon, lat); t = e.get("tags", {})
    for s in stations:
        if hav_ok(p, s["p"]) <= PARAMS["station_cluster_m"] and (s["kind"] == kind or True):
            s["n_el"] += 1
            if not s["name"] and t.get("name"): s["name"] = t["name"]
            s["lines"].add(t.get("network", "")); break
    else:
        net = t.get("network", "") + " " + t.get("operator", "")
        stations.append(dict(p=p, lon=lon, lat=lat, kind=kind, name=t.get("name", ""), n_el=1, lines={t.get("network", "")},
                             metro=("Metrorrey" in net or t.get("station") == "subway" or any(f"Línea {k}" in net or f"Linea {k}" in net for k in "123")),
                             osm_id=f'{e["type"][0]}{e["id"]}'))
stops = []
for s in stations:
    typ = s["kind"] if s["kind"] in ("terminal", "brt") else ("metro" if s["metro"] else "brt")
    stops.append(dict(lon=s["lon"], lat=s["lat"], type=typ, name=s["name"] or ("Estación OSM sin nombre"), ref="", route_ref="",
                      network=";".join(sorted(x for x in s["lines"] if x)), direction="", src="osm", osm_id=s["osm_id"], n_el=s["n_el"]))
n_station_clusters = len(stops)
# bus stops: priority OSM raw > anclas_paradas osm > places
pts_hi = [px(b["lon"], b["lat"]) for b in bus]
allstops = stops + bus
P = np.array([px(s["lon"], s["lat"]) for s in allstops]) if allstops else np.zeros((0, 2))
ap = json.load(open(J("data", "anclas_paradas_zmm.geojson")))["features"]
def near_existing(p, arr, r): return arr.size and (np.hypot(arr[:, 0] - p[0], arr[:, 1] - p[1]) <= r).any()
P_st = np.array([px(s["lon"], s["lat"]) for s in stops]) if stops else np.zeros((0, 2))
drop = {"osm_dup": 0, "places_dup_station": 0, "places_dup_bus": 0}
for pass_src in ("osm", "places"):
    for f in ap:
        pr = f["properties"]; s = pr.get("s", "")
        if (pass_src == "osm") != s.startswith("osm") and not (pass_src == "places" and not s.startswith("osm")): continue
        if pass_src == "osm" and not s.startswith("osm"): continue
        if pass_src == "places" and s.startswith("osm"): continue
        lon, lat = f["geometry"]["coordinates"]; p = px(lon, lat)
        if pr.get("t") == "transit_station" and near_existing(p, P_st, PARAMS["station_cluster_m"]):
            drop["places_dup_station"] += 1; continue
        if near_existing(p, P, PARAMS["dedupe_cross_source_m"]):
            drop["osm_dup" if pass_src == "osm" else "places_dup_bus"] += 1
            # enrich: add 'places' evidence to nearest existing
            d = np.hypot(P[:, 0] - p[0], P[:, 1] - p[1]); j = int(d.argmin())
            allstops[j].setdefault("also", set()).add(pass_src)
            if pass_src == "places" and not allstops[j]["name"] and pr.get("n"): allstops[j]["name"] = pr["n"]
            continue
        typ = "metro" if pr.get("t") == "transit_station" else "bus"   # Places transit_station = Metrorrey stations not matched to OSM (names 'Estacion X')
        allstops.append(dict(lon=lon, lat=lat, type=typ if typ != "bus" else "bus", name=pr.get("n", ""), ref="", route_ref="", network="",
                             direction="", src="places" if not s.startswith("osm") else "anclas_osm", osm_id="", places_type=pr.get("t")))
        P = np.vstack([P, [p]])
# Places 'transit_station' that are close to an OSM station were dropped by dedupe; remaining ones stay as 'terminal' (flag).
for s in allstops: s["p"] = px(s["lon"], s["lat"])
print("stops merged:", len(allstops), "stations clusters:", n_station_clusters, "dedupe:", drop)

# ---------------- anchors (people) ----------------
anch = []
for f in json.load(open(J("data", "anclas.geojson")))["features"]:
    t = f["properties"]["tipo"]
    if t in ("escuela", "iglesia", "hospital"): anch.append((f["geometry"]["coordinates"], t, "osm"))
seen = {(round(a[0][0], 4), round(a[0][1], 4), a[1]) for a in anch}
for f in json.load(open(J("v2", "data", "anclas_v3.geojson")))["features"]:
    c_ = f["properties"].get("c"); s = f["properties"].get("s")
    t = {"escuela": "escuela", "iglesia": "iglesia", "oxxo": "oxxo", "express": "express", "banco_bienestar_azteca": "banco"}.get(c_)
    if not t: continue
    k = (round(f["geometry"]["coordinates"][0], 4), round(f["geometry"]["coordinates"][1], 4), t)
    if k in seen: continue   # same cell+type already in anclas.geojson
    seen.add(k); anch.append((f["geometry"]["coordinates"], t, s))
A = np.array([px(*a[0]) for a in anch]); A_t = [a[1] for a in anch]
print("anchors:", len(anch))
anchors_out = [[round(a[0][0], 5), round(a[0][1], 5), a[1]] for a in anch]

# ---------------- roads ----------------
rr = json.load(open("/workspace/downloads/osm_vias_oneway_raw.json"))["elements"]
road_geoms, road_meta = [], []
for e in rr:
    if e.get("type") != "way" or "geometry" not in e: continue
    t = e["tags"]; h = t.get("highway", ""); base = h.replace("_link", "")
    if base not in CLASS_IDX: continue
    idx = 1 if h.endswith("_link") else CLASS_IDX[base]
    ow = t.get("oneway", "")
    if ow in ("yes", "true", "1") or h.startswith("motorway") or t.get("junction") in ("roundabout", "circular"): mode = "fwd"
    elif ow == "-1": mode = "rev"
    else: mode = "two"
    pts = [px(g["lon"], g["lat"]) for g in e["geometry"]]
    if len(pts) < 2: continue
    road_geoms.append(LineString(pts)); road_meta.append(dict(id=e["id"], name=t.get("name", ""), ref=t.get("ref", ""), h=h, idx=idx, mode=mode, src="osm"))
n_major = len(road_geoms)
for f in json.load(open(J("data", "roads_zmm.geojson")))["features"]:
    h = f["properties"]["highway"]
    if h not in ("residential", "service", "living_street", "unclassified"): continue   # primary/secondary/tertiary already from raw (with oneway)
    pts = [px(*c_) for c_ in f["geometry"]["coordinates"]]
    if len(pts) < 2: continue
    road_geoms.append(LineString(pts)); road_meta.append(dict(id=f["properties"]["osm_id"], name="(calle local sin nombre en data)", ref="", h=h, idx=0, mode="unk", src="roads_zmm"))
print("roads:", n_major, "major +", len(road_geoms) - n_major, "local")
tree = STRtree(road_geoms)

def bearing_at(line, p):
    d = line.project(Point(p)); L = line.length
    a = line.interpolate(max(d - 8, 0)); b = line.interpolate(min(d + 8, L))
    dx, dy = b.x - a.x, b.y - a.y
    if abs(dx) + abs(dy) < 1e-6: return None
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360

def adjacent(p, R):
    res = {}
    for j in tree.query(Point(p).buffer(R)):
        g = road_geoms[j]; d = g.distance(Point(p))
        if d > R: continue
        m = road_meta[j]
        b = bearing_at(g, p)
        key = m["id"]
        if key in res and res[key]["dist"] <= d: continue
        res[key] = dict(m, dist=d, b=b)
    return list(res.values())

# ---------------- EG-personas segments (modeled walk-flow score; optional) ----------------
seg_pts = None; seg_out = []
sp = "/workspace/estudio-peatonal/out/segmentos_general.csv"
if os.path.exists(sp):
    S = []
    with open(sp, newline="") as fh:
        for r in csv.DictReader(fh):
            try: S.append((float(r["lon_mid"]), float(r["lat_mid"]), float(r["pie_score"]), float(r["score"]), r["nombre_calle"], r["highway"]))
            except Exception: pass
    S.sort(key=lambda r: -r[3])
    for r in S[:2000]: seg_out.append([round(r[0], 5), round(r[1], 5), round(r[3], 1), round(r[2], 1), r[4]])
    SP = np.array([px(r[0], r[1]) for r in S]); seg_tree = STRtree([Point(x) for x in SP]); seg_S = S
    print("segments:", len(S))
else:
    print("WARN: EG-personas segments missing", file=sys.stderr); seg_tree = None

# ---------------- score ----------------
N = len(allstops)
for i, s in enumerate(allstops):
    p = s["p"]; R = PARAMS["radius_station_m"] if s["type"] in ("metro", "brt", "terminal") else PARAMS["radius_bus_m"]
    s["radius"] = R
    d = np.hypot(P[:, 0] - p[0], P[:, 1] - p[1]) if len(P) == N else None
    Pn = np.array([q["p"] for q in allstops]) if i == 0 else Pn
    d = np.hypot(Pn[:, 0] - p[0], Pn[:, 1] - p[1])
    s["n_other_stops"] = int(((d <= PARAMS["people_radius_m"]) & (d > 0.5)).sum())
    da = np.hypot(A[:, 0] - p[0], A[:, 1] - p[1]); mask = da <= PARAMS["people_radius_m"]
    cnt = {}
    for k in np.nonzero(mask)[0]: cnt[A_t[k]] = cnt.get(A_t[k], 0) + 1
    s["anchors"] = cnt
    s["raw_density"] = (PARAMS["w_stop_self"][s["type"]] + PARAMS["w_other_stop"] * min(s["n_other_stops"], PARAMS["cap_other_stops"])
                        + sum(PARAMS["w_anchor"][t] * min(n, PARAMS["cap_anchors"]) for t, n in cnt.items()))
    s["muni"] = muni_of(s["lon"], s["lat"]) or "fuera núcleo ZMM"
    s["mult"], s["mult_tomtom"] = mult_of(s["muni"])
    adj = sorted(adjacent(p, R), key=lambda r: (-r["idx"], r["dist"]))
    s["adj"] = adj
    s["pie"] = None
    if seg_tree is not None:
        j = int(seg_tree.nearest(Point(p)))
        if hav_ok(p, SP[j]) <= PARAMS["pie_max_m"]: s["pie"] = (seg_S[j][2], seg_S[j][4])
raws = np.array([s["raw_density"] for s in allstops])
rk = raws.argsort().argsort() / max(len(raws) - 1, 1)
for s, r in zip(allstops, rk):
    s["people_idx"] = float(r)
    if s["pie"] is not None:
        s["people"] = PARAMS["w_people_density"] * s["people_idx"] + PARAMS["w_people_pie"] * s["pie"][0] / 100
    else: s["people"] = s["people_idx"]
    top = s["adj"][0] if s["adj"] else None
    s["road_idx"] = top["idx"] if top else 0
    s["cars"] = s["road_idx"] / 5 * s["mult"]
    s["score_raw"] = s["people"] * s["cars"]
mx = max(s["score_raw"] for s in allstops) or 1
for s in allstops: s["score"] = round(100 * s["score_raw"] / mx, 1)

# ---------------- ranking with NMS ----------------
order = sorted(range(N), key=lambda i: -allstops[i]["score_raw"])
chosen = []
for i in order:
    s = allstops[i]
    if s["score_raw"] <= 0: break
    if any(hav_ok(s["p"], allstops[j]["p"]) < PARAMS["nms_m"] for j in chosen):
        for j in chosen:
            if hav_ok(s["p"], allstops[j]["p"]) < PARAMS["nms_m"]: allstops[j]["merged"] = allstops[j].get("merged", 0) + 1; break
        continue
    chosen.append(i)
    if len(chosen) >= PARAMS["top_n"]: break

def flow_deg(r):
    if r["b"] is None: return None
    if r["mode"] == "fwd": return r["b"]
    if r["mode"] == "rev": return (r["b"] + 180) % 360
    return None
def direction(top, adj):
    """Directions of travel for the top road. OSM often maps dual carriageways as 2 one-way ways: collect all same-name/ref edges of that class in radius."""
    if not top or top["b"] is None: return {"modo": "sin vía", "txt": "sin vía mayor en radio"}
    same = [r for r in adj if r["idx"] == top["idx"] and (r["name"], r["ref"]) == (top["name"], top["ref"]) and r["mode"] in ("fwd", "rev") and r["b"] is not None]
    if top["mode"] in ("fwd", "rev"):
        fl = []
        for r in same:
            f = flow_deg(r)
            if all(abs(((f - g + 180) % 360) - 180) > 60 for g in fl): fl.append(f)
        fl = [round(f) for f in fl]
        flows = " y ".join(f"{comp(f)} ({f}°)" for f in fl)
        faces = " y ".join(f"{comp(f+180)} ({round((f+180)%360)}°)" for f in fl)
        return {"modo": "un sentido x calzada" if len(fl) > 1 else "un sentido", "sentidos_deg": fl, "cartel_mira_deg": [round((f + 180) % 360) for f in fl],
                "txt": f"autos circulan hacia {flows}; cartel debe mirar {faces} para ver autos que llegan"}
    if top["mode"] == "two":
        bb = top["b"]
        return {"modo": "doble sentido", "sentidos_deg": [round(bb % 360), round((bb + 180) % 360)], "cartel_mira_deg": [round((bb + 180) % 360), round(bb % 360)],
                "txt": f"doble sentido ({comp(bb)}-{comp(bb+180)}, {round(bb%360)}°/{round((bb+180)%360)}°); cartel puede mirar {comp(bb)} o {comp(bb+180)}"}
    return {"modo": "desconocido", "txt": "calle local: sentido no disponible en data"}

IDXTXT = {0: "calle local (sin índice)", 1: "enlace/ramal", 2: "terciaria", 3: "secundaria", 4: "primaria", 5: "troncal/autopista"}
feats = []; table = []
for rank, i in enumerate(chosen, 1):
    s = allstops[i]; top = s["adj"][0] if s["adj"] else None
    dr = direction(top, s['adj'])
    flags = ["sin_conteos_reales", "indice_via=proxy_clase_OSM", "peso_personas=juicio_no_calibrado"]
    if s["src"] in ("places", "anclas_osm") : flags.append("fuente_Places_parcial" if s["src"] == "places" else "fuente_OSM_parcial")
    if s["src"] == "osm" and s["type"] == "bus": flags.append("OSM_parcial")
    if not s["mult_tomtom"]: flags.append("municipio_sin_TomTom(usa_total_ZMM)")
    if s["type"] == "metro" and s["src"] == "places": flags.append("Places_transit_station_sin_match_OSM")
    if top is None: flags.append("sin_via_mayor_en_radio")
    if s["pie"] is None: flags.append("sin_segmento_EG-personas<80m")
    others = [{"n": a["name"] or a["ref"], "clase": IDXTXT[a["idx"]], "d_m": round(a["dist"])} for a in s["adj"][1:4]]
    lat, lon = s["lat"], s["lon"]
    props = {"rank": rank, "id": s["osm_id"] or f"{s['src']}-{rank}", "name": s["name"] or "(sin nombre)", "tipo": s["type"], "ruta": s["route_ref"] or s["ref"] or s["network"],
             "muni": s["muni"], "radio_m": s["radius"], "via": (top["name"] or top["ref"] or "(sin nombre)") if top else "", "via_ref": top["ref"] if top else "",
             "via_clase": IDXTXT[s["road_idx"]], "via_idx": s["road_idx"], "via_dist_m": round(top["dist"]) if top else None, "direccion": dr["txt"], "modo": dr["modo"], "sentidos_deg": dr.get("sentidos_deg", []), "cartel_mira_deg": dr.get("cartel_mira_deg", []),
             "otras_vias": others, "score": s["score"], "personas": round(s["people"], 3), "personas_densidad_pct": round(s["people_idx"], 3),
             "pie_modelo": s["pie"][0] if s["pie"] else None, "otras_paradas_150m": s["n_other_stops"], "anclas_150m": s["anchors"],
             "autos": round(s["cars"], 3), "mult_muni": s["mult"], "mult_fuente": "TomTom indicativo" if s["mult_tomtom"] else "total ZMM TomTom (muni sin dato)",
             "paradas_fusionadas_200m": s.get("merged", 0),
             "gmaps": f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}",
             "streetview": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat:.6f},{lon:.6f}", "flags": flags}
    feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}, "properties": props})
    table.append(props)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "paradas_candidatas_top100.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(OUT, "paradas_candidatas_top100.csv"), "w", newline="") as fh:
    w = csv.writer(fh); cols = ["rank", "id", "name", "tipo", "ruta", "muni", "lat", "lon", "via", "via_clase", "direccion", "score", "personas", "autos", "mult_muni", "gmaps", "flags"]
    w.writerow(cols)
    for f in feats:
        p = f["properties"]; w.writerow([p.get(c_) if c_ not in ("lat", "lon", "flags") else None for c_ in cols[:6]] + [f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]] +
                                        [p[c_] for c_ in cols[8:15]] + [p["gmaps"], "|".join(p["flags"])] if False else
                                        [p["rank"], p["id"], p["name"], p["tipo"], p["ruta"], p["muni"], f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], p["via"], p["via_clase"], p["direccion"], p["score"], p["personas"], p["autos"], p["mult_muni"], p["gmaps"], "|".join(p["flags"])])

# all stops (compact) for context layer: [lon,lat,type,score]
json.dump([[round(s["lon"], 5), round(s["lat"], 5), s["type"], s["score"]] for s in allstops], open(os.path.join(OUT, "paradas_todas.json"), "w"), separators=(",", ":"))
json.dump(anchors_out, open(os.path.join(OUT, "anclas_flujo.json"), "w"), separators=(",", ":"))
json.dump(seg_out, open(os.path.join(OUT, "segmentos_personas_top.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# display copy of v2 road-class proxy
import shutil; shutil.copy(J("v2", "data", "trafico_vias.geojson"), os.path.join(OUT, "trafico_vias.geojson"))
# TomTom municipal aggregates (no OD coords, no raw samples)
mf = json.load(open(J("data", "muni.geojson")))
for f in mf["features"]:
    n = f["properties"]["nom"]; d = tt.get(n)
    f["properties"] = {"nom": n, "tomtom": d if d else None, "mult": mult_of(n)[0] if d else None}
    f["geometry"] = json.loads(json.dumps(f["geometry"]))
json.dump(mf, open(os.path.join(OUT, "tomtom_muni_indicativo.geojson"), "w"), ensure_ascii=False, separators=(",", ":"))
tt_pub = {k: v for k, v in tt.items()}
manifest = {"generated_by": "scripts/build_espectaculares.py", "params": PARAMS, "n_stops_merged": len(allstops), "n_stop_total": len(allstops),
            "stops_by_type": {t: sum(1 for s in allstops if s["type"] == t) for t in ("bus", "brt", "metro", "terminal")},
            "stops_by_source": {k: sum(1 for s in allstops if s["src"] == k) for k in ("osm", "anclas_osm", "places")},
            "n_station_clusters": n_station_clusters, "anchors": len(anch), "road_edges": {"osm_major": n_major, "local": len(road_geoms) - n_major},
            "tomtom_aggregates_by_municipio": tt_pub, "tomtom_note": "TomTom indicativo, 1 día (mar 2026-10-06 perfil histórico), uso interno. OD industriales, NO conteos por vía.",
            "osm_snapshot": json.load(open("/workspace/downloads/osm_paradas_raw.json")).get("osm3s", {}).get("timestamp_osm_base")}
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(manifest["stops_by_type"]), manifest["stops_by_source"], "tt:", tt)
for p in table[:10]: print(p["rank"], p["name"], p["tipo"], p["muni"], p["via"], p["via_clase"], p["score"], "|", p["direccion"])
