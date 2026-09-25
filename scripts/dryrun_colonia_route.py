#!/usr/bin/env python3
"""Dry-run Scout colonia route builder (mirrors scout.html logic).

Usage:
  python3 scripts/dryrun_colonia_route.py --cve 19039_0167
  python3 scripts/dryrun_colonia_route.py --name Croc
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLONIAS = os.path.join(ROOT, "data", "colonias.geojson")
ROADS = os.path.join(ROOT, "data", "roads_zmm.geojson")

STEP_M_COLONIA = 22
MAX_ROUTE_PTS_COLONIA = 4000
HOP_CONNECT_M = 350
CLIP_BUFFER_M = 25
AVENIDAS = {"primary", "secondary", "tertiary", "unclassified", "trunk"}
TODO_EXTRA = {"residential", "living_street", "service"}


def haversine_m(a_lat, a_lng, b_lat, b_lng):
    R = 6371000.0
    to_r = math.pi / 180
    d_lat = (b_lat - a_lat) * to_r
    d_lng = (b_lng - a_lng) * to_r
    s = (
        math.sin(d_lat / 2) ** 2
        + math.cos(a_lat * to_r) * math.cos(b_lat * to_r) * math.sin(d_lng / 2) ** 2
    )
    return 2 * R * math.asin(min(1.0, math.sqrt(s)))


def point_in_ring(lng, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_geom(lng, lat, geom):
    t = geom["type"]
    if t == "Polygon":
        rings = geom["coordinates"]
        if not point_in_ring(lng, lat, rings[0]):
            return False
        return not any(point_in_ring(lng, lat, h) for h in rings[1:])
    if t == "MultiPolygon":
        return any(
            point_in_geom(lng, lat, {"type": "Polygon", "coordinates": p})
            for p in geom["coordinates"]
        )
    return False


def outer_rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        return [p[0] for p in geom["coordinates"]]
    return []


def dist_point_to_seg_m(lat, lng, a_lat, a_lng, b_lat, b_lng):
    to_m_lat = 111320.0
    to_m_lng = 111320.0 * math.cos(lat * math.pi / 180)
    ax = (a_lng - lng) * to_m_lng
    ay = (a_lat - lat) * to_m_lat
    bx = (b_lng - lng) * to_m_lng
    by = (b_lat - lat) * to_m_lat
    dx, dy = bx - ax, by - ay
    len2 = dx * dx + dy * dy
    if len2 < 1e-6:
        return math.sqrt(ax * ax + ay * ay)
    t = max(0.0, min(1.0, (-ax * dx + -ay * dy) / len2))
    px, py = ax + t * dx, ay + t * dy
    return math.sqrt(px * px + py * py)


def point_near_geom(lng, lat, geom, buffer_m=CLIP_BUFFER_M):
    if point_in_geom(lng, lat, geom):
        return True
    if buffer_m <= 0:
        return False
    for ring in outer_rings(geom):
        for i in range(len(ring) - 1):
            if (
                dist_point_to_seg_m(
                    lat, lng, ring[i][1], ring[i][0], ring[i + 1][1], ring[i + 1][0]
                )
                <= buffer_m
            ):
                return True
    return False


def segments_cross(a, b, c, d):
    def cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    d1 = cross(c[0], c[1], d[0], d[1], a[0], a[1])
    d2 = cross(c[0], c[1], d[0], d[1], b[0], b[1])
    d3 = cross(a[0], a[1], b[0], b[1], c[0], c[1])
    d4 = cross(a[0], a[1], b[0], b[1], d[0], d[1])
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
        (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
    )


def edge_hits(a, b, geom):
    if point_near_geom(a[0], a[1], geom) or point_near_geom(b[0], b[1], geom):
        return True
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if point_near_geom(mx, my, geom):
        return True
    for ring in outer_rings(geom):
        for i in range(len(ring) - 1):
            if segments_cross(a, b, ring[i], ring[i + 1]):
                return True
    return False


def clip_line(coords, geom):
    pieces, cur = [], []

    def flush():
        nonlocal cur
        if len(cur) >= 2:
            pieces.append(cur)
        cur = []

    for i in range(len(coords) - 1):
        a, b = coords[i], coords[i + 1]
        if edge_hits(a, b, geom):
            if not cur:
                cur.append(a)
            elif cur[-1][0] != a[0] or cur[-1][1] != a[1]:
                flush()
                cur.append(a)
            cur.append(b)
        else:
            flush()
    flush()
    return pieces


def sample_polyline(coords, step_m):
    out = [{"lat": coords[0][1], "lng": coords[0][0]}]
    acc = 0.0
    for i in range(1, len(coords)):
        a, b = coords[i - 1], coords[i]
        a_lat, a_lng, b_lat, b_lng = a[1], a[0], b[1], b[0]
        seg = haversine_m(a_lat, a_lng, b_lat, b_lng)
        if seg < 1e-3:
            continue
        traveled = 0.0
        while acc + (seg - traveled) >= step_m:
            need = step_m - acc
            traveled += need
            t = traveled / seg
            out.append(
                {"lat": a_lat + (b_lat - a_lat) * t, "lng": a_lng + (b_lng - a_lng) * t}
            )
            acc = 0.0
        acc += seg - traveled
    last = coords[-1]
    prev = out[-1]
    if haversine_m(prev["lat"], prev["lng"], last[1], last[0]) > step_m * 0.35:
        out.append({"lat": last[1], "lng": last[0]})
    return out


def chain_greedy(segs, start_lat, start_lng):
    pool = []
    for coords in segs:
        pool.append(
            {
                "a": {"lat": coords[0][1], "lng": coords[0][0]},
                "b": {"lat": coords[-1][1], "lng": coords[-1][0]},
                "coords": coords,
            }
        )
    if not pool:
        return [], 0
    best_i, best_d = 0, 1e12
    for i, s in enumerate(pool):
        d = min(
            haversine_m(start_lat, start_lng, s["a"]["lat"], s["a"]["lng"]),
            haversine_m(start_lat, start_lng, s["b"]["lat"], s["b"]["lng"]),
        )
        if d < best_d:
            best_d, best_i = d, i
    ordered = []
    teleports = 0
    cur = pool.pop(best_i)
    if haversine_m(start_lat, start_lng, cur["b"]["lat"], cur["b"]["lng"]) < haversine_m(
        start_lat, start_lng, cur["a"]["lat"], cur["a"]["lng"]
    ):
        cur["coords"] = list(reversed(cur["coords"]))
        cur["a"], cur["b"] = cur["b"], cur["a"]
    ordered.append({"coords": cur["coords"], "teleport": False})
    tip = cur["b"]
    while pool:
        bi, bd, rev = -1, 1e12, False
        for j, s in enumerate(pool):
            da = haversine_m(tip["lat"], tip["lng"], s["a"]["lat"], s["a"]["lng"])
            db = haversine_m(tip["lat"], tip["lng"], s["b"]["lat"], s["b"]["lng"])
            if da < bd:
                bd, bi, rev = da, j, False
            if db < bd:
                bd, bi, rev = db, j, True
        if bi < 0:
            break
        teleport = bd > HOP_CONNECT_M
        if teleport:
            teleports += 1
        nxt = pool.pop(bi)
        coords = list(reversed(nxt["coords"])) if rev else list(nxt["coords"])
        ordered.append({"coords": coords, "teleport": teleport})
        tip = {"lat": coords[-1][1], "lng": coords[-1][0]}
    return ordered, teleports


def finalize(ordered, step_m=STEP_M_COLONIA, max_pts=MAX_ROUTE_PTS_COLONIA):
    path = []
    for entry in ordered:
        sampled = sample_polyline(entry["coords"], step_m)
        if entry.get("teleport") and sampled:
            sampled[0]["gap"] = True
        path.extend(sampled)
    cleaned = []
    for pt in path:
        if pt.get("gap"):
            cleaned.append(pt)
            continue
        prev = cleaned[-1] if cleaned else None
        if not prev or haversine_m(prev["lat"], prev["lng"], pt["lat"], pt["lng"]) >= step_m * 0.45:
            cleaned.append(pt)
    if len(cleaned) > max_pts:
        factor = len(cleaned) / max_pts
        alt = max(step_m + 2, math.ceil(step_m * max(1.2, factor)))
        if alt > step_m and alt <= 40:
            return finalize(ordered, alt, max_pts)
        stride = math.ceil(len(cleaned) / max_pts)
        th = cleaned[::stride]
        if th[-1] is not cleaned[-1]:
            th.append(cleaned[-1])
        cleaned = th
    return cleaned


def road_meters_in_poly(roads, geom):
    meters = 0.0
    feats = 0
    for f in roads["features"]:
        g = f.get("geometry") or {}
        if g.get("type") != "LineString":
            continue
        hw = (f.get("properties") or {}).get("highway") or ""
        if hw not in AVENIDAS and hw not in TODO_EXTRA:
            continue
        coords = g["coordinates"]
        hit = False
        piece_m = 0.0
        for i in range(len(coords) - 1):
            a, b = coords[i], coords[i + 1]
            if edge_hits(a, b, geom):
                hit = True
                piece_m += haversine_m(a[1], a[0], b[1], b[0])
        if hit:
            feats += 1
            meters += piece_m
    return feats, meters


def build_route(roads, geom, start_lat, start_lng):
    segs = []
    calles = set()
    for f in roads["features"]:
        g = f.get("geometry") or {}
        if g.get("type") != "LineString":
            continue
        hw = (f.get("properties") or {}).get("highway") or ""
        if hw not in AVENIDAS and hw not in TODO_EXTRA:
            continue
        coords = g["coordinates"]
        if len(coords) < 2:
            continue
        any_in = any(point_near_geom(c[0], c[1], geom) for c in coords)
        pieces = []
        if any_in:
            pieces = clip_line(coords, geom)
        else:
            for e in range(len(coords) - 1):
                if edge_hits(coords[e], coords[e + 1], geom):
                    pieces = clip_line(coords, geom)
                    break
        for piece in pieces:
            if len(piece) >= 2:
                segs.append(piece)
                oid = (f.get("properties") or {}).get("osm_id") or hw
                calles.add(oid)
    if not segs:
        return {"points": [], "calleCount": 0, "teleports": 0, "segCount": 0}
    ordered, teleports = chain_greedy(segs, start_lat, start_lng)
    points = finalize(ordered)
    return {
        "points": points,
        "calleCount": len(calles) or len(segs),
        "teleports": teleports,
        "segCount": len(segs),
    }


def find_feat(cols, cve=None, name=None):
    for f in cols["features"]:
        p = f.get("properties") or {}
        if cve and str(p.get("cve_col")) == str(cve):
            return f
        if name and (p.get("colonia") or "").lower() == name.lower():
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cve", default="19039_0167")
    ap.add_argument("--name", default=None)
    ap.add_argument("--roads", default=ROADS)
    args = ap.parse_args()
    with open(COLONIAS) as f:
        cols = json.load(f)
    with open(args.roads) as f:
        roads = json.load(f)
    feat = find_feat(cols, cve=args.cve, name=args.name)
    if not feat:
        print("colonia not found", file=sys.stderr)
        sys.exit(1)
    p = feat["properties"]
    geom = feat["geometry"]
    lat, lng = float(p["lat"]), float(p["lon"])
    n_ways, meters = road_meters_in_poly(roads, geom)
    built = build_route(roads, geom, lat, lng)
    print("colonia:", p.get("colonia"), "/", p.get("municipio"), "cve", p.get("cve_col"))
    print("area_km2:", p.get("area_km2"), "geom:", geom["type"])
    print("OSM ways intersecting (+%dm buffer):" % CLIP_BUFFER_M, n_ways)
    print("OSM road meters (approx edges hitting):", round(meters))
    print("route segments:", built["segCount"])
    print("calles:", built["calleCount"])
    print("teleports:", built["teleports"])
    print("route points (finalizeRoutePath):", len(built["points"]))
    print("roads file features:", len(roads.get("features") or []))
    props = roads.get("properties") or {}
    if props:
        print("roads scope:", props.get("scope"), "generated:", props.get("generated"))


if __name__ == "__main__":
    main()
