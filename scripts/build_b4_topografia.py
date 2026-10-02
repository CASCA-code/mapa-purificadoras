#!/usr/bin/env python3
"""B4 topografía: pendiente a pie (radio 300 m) por colonia, estación sugerida y punto de «Dónde poner».
Fuente: Copernicus GLO-30 DSM (ESA, gratuito, ~30 m), ya en disco: /home/box/geo/base_mty/raw/dem/.
Offline. Solo agrega campos (pend_*, pd) a b4/data/*; no toca score_base ni rank_base.
Uso: python3 scripts/build_b4_topografia.py   (correr DESPUÉS de build_b4.py)"""
import json, os, glob, math, datetime
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import shape
import shapely
Image.MAX_IMAGE_PIXELS = None
DEM = '/home/box/geo/base_mty/raw/dem/'
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b4', 'data') + '/'
R_M = 300            # radio a pie
T_CUESTA = 8.0       # % SUPUESTO: >8 = «cuesta arriba»
T_EMP = 12.0         # % SUPUESTO: >12 = «muy empinada»
FACT = {'plana': 1.0, 'cuesta': 0.8, 'empinada': 0.6}   # SUPUESTO: ajuste del puntaje de celda
def clase(p): return 'empinada' if p > T_EMP else 'cuesta' if p > T_CUESTA else 'plana'

# mosaico: lon -100.7..-100.0, lat 25.5..25.9 (tiles N25 W101 y N25 W100)
LON0, LON1, LAT0, LAT1 = -100.70, -100.00, 25.50, 25.92
S = 3600.0
def load(tile_lon):
    f = DEM + 'Copernicus_DSM_COG_10_N25_00_W%03d_00_DEM.tif' % (-tile_lon)
    return np.array(Image.open(f), dtype=np.float32)
def rc(lon, lat, t_lon):   # fila/col dentro del tile
    return (26.0 - lat) * S, (lon - t_lon) * S
tiles = {-101: load(-101), -100: load(-100)}
r0, r1 = int((26 - LAT1) * S), int((26 - LAT0) * S) + 1
c_w = int((LON0 + 101) * S); c_e_w = 3600
c_e = int((LON1 + 100) * S) + 1
Z = np.hstack([tiles[-101][r0:r1, c_w:c_e_w], tiles[-100][r0:r1, 0:c_e]]).astype(np.float64)
Z[Z < -100] = np.nan
Z = np.where(np.isnan(Z), np.nanmean(Z), Z)
org_lon = -101 + c_w / S; org_lat = 26 - r0 / S
midlat = (LAT0 + LAT1) / 2
dy = 111320.0 / S; dx = 111320.0 * math.cos(math.radians(midlat)) / S
Zs = ndi.gaussian_filter(Z, 1.0)                     # suaviza ruido del DSM (techos/árboles)
gy, gx = np.gradient(Zs, dy, dx)
SL = np.hypot(gx, gy) * 100.0                        # pendiente %
ry, rx = R_M / dy, R_M / dx
ky, kx = int(math.ceil(ry)), int(math.ceil(rx))
yy, xx = np.mgrid[-ky:ky + 1, -kx:kx + 1]
K = ((yy / ry) ** 2 + (xx / rx) ** 2 <= 1).astype(float); K /= K.sum()
SL300 = ndi.convolve(SL, K, mode='nearest')          # pendiente media en radio 300 m
ZP = ndi.percentile_filter(Zs, 95, footprint=K > 0, mode='nearest') if False else None
# desnivel local: máx-mín suavizado en el disco (mediana de p95-p5 aprox. con max/min filter sobre Zs)
FP = K > 0
ZMAX = ndi.maximum_filter(Zs, footprint=FP, mode='nearest'); ZMIN = ndi.minimum_filter(Zs, footprint=FP, mode='nearest')
DESN = ZMAX - ZMIN
def px(lon, lat):
    return (np.clip(np.round((org_lat - lat) / (1 / S)).astype(int), 0, Z.shape[0] - 1),
            np.clip(np.round((lon - org_lon) / (1 / S)).astype(int), 0, Z.shape[1] - 1))
def at(arr, lon, lat):
    r, c = px(np.atleast_1d(lon), np.atleast_1d(lat)); return arr[r, c]

# 1) colonias: pendiente media/p90 de los píxeles dentro del polígono + 300 m desde centroide
col = json.load(open(D + 'colonias_b4.geojson'))
H, W = Z.shape
rows_i, cols_i = np.mgrid[0:H, 0:W]
for f in col['features']:
    p = f['properties']; g = shape(f['geometry'])
    minx, miny, maxx, maxy = g.bounds
    r_a, c_a = px(np.array([minx]), np.array([maxy])); r_b, c_b = px(np.array([maxx]), np.array([miny]))
    rs, cs = np.mgrid[r_a[0]:r_b[0] + 1, c_a[0]:c_b[0] + 1]
    lo = org_lon + (cs.ravel() + .5) / S; la = org_lat - (rs.ravel() + .5) / S
    m = shapely.contains_xy(g, lo, la)
    v = SL[rs.ravel()[m], cs.ravel()[m]] if m.sum() >= 3 else at(SL300, p['lon'], p['lat'])
    p['pend_media'] = round(float(np.mean(v)), 1)
    p['pend_p90'] = round(float(np.percentile(v, 90)), 1)
    p['pend_clase'] = clase(p['pend_media'])
    new = []
    for b in p.get('est') or []:
        s = float(at(SL300, b[0], b[1])[0]); new.append(b[:3] + [round(s, 1)])
    p['est'] = new
    p['n_est_plana'] = sum(1 for b in new if b[3] <= T_CUESTA)
json.dump(col, open(D + 'colonias_b4.geojson', 'w'), ensure_ascii=False, separators=(',', ':'))

# 2) estaciones sugeridas (capa)
es = json.load(open(D + 'estaciones_sugeridas.geojson'))
for f in es['features']:
    lon, lat = f['geometry']['coordinates'][:2]
    f['properties']['pd'] = round(float(at(SL300, lon, lat)[0]), 1)
json.dump(es, open(D + 'estaciones_sugeridas.geojson', 'w'), ensure_ascii=False, separators=(',', ':'))

# 3) puntos «Dónde poner»
sp = json.load(open(D + 'spots_b4.json'))
for r in sp['rows']:
    s = float(at(SL300, r['lon'], r['lat'])[0]); r['pend_300m_pct'] = round(s, 1)
    r['desnivel_300m_m'] = int(round(float(at(DESN, r['lon'], r['lat'])[0])))
    r['pend_clase'] = clase(s); r['cell_score_ajustado'] = round(r['cell_score'] * FACT[clase(s)], 2)
sp['topografia'] = {'fuente': 'Copernicus GLO-30 DSM (ESA), ~30 m, tiles N25 W101/W100', 'radio_m': R_M,
                    'umbral_cuesta_pct': T_CUESTA, 'umbral_empinada_pct': T_EMP, 'factores_SUPUESTO': FACT,
                    'generado': datetime.date.today().isoformat()}
json.dump(sp, open(D + 'spots_b4.json', 'w'), ensure_ascii=False, separators=(',', ':'))

# resumen
ps = [f['properties'] for f in col['features']]
print('colonias pend_media: p50 %.1f p90 %.1f max %.1f' % tuple(np.percentile([p['pend_media'] for p in ps], [50, 90, 100])))
for k in ('plana', 'cuesta', 'empinada'): print('colonias', k, sum(p['pend_clase'] == k for p in ps))
ests = [b[3] for p in ps for b in (p['est'] or [])]
print('estaciones', len(ests), 'plana(<=8)', sum(e <= T_CUESTA for e in ests), '8-12', sum(T_CUESTA < e <= T_EMP for e in ests), '>12', sum(e > T_EMP for e in ests))
sr = sp['rows']; print('spots', len(sr), {k: sum(r['pend_clase'] == k for r in sr) for k in FACT})
print('top steepest colonias:', sorted([(p['pend_media'], p['colonia'], p['municipio']) for p in ps], reverse=True)[:6])
print('flattest:', sorted([(p['pend_media'], p['colonia']) for p in ps])[:3])
print('dem shape', Z.shape, 'dx %.1f dy %.1f' % (dx, dy))
