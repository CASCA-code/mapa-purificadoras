#!/usr/bin/env python3
"""Build B4 (BORRADOR): datos de b4/data + data/b4_escenarios.csv. Offline, sin red.
Lee SOLO archivos existentes del repo (v2/data, v3_espectaculares/data, data/). No modifica nada existente.
SUPUESTOS (marcados): SEP_M, UMBRAL_CELDA, MAX_EST, categoria SADM, volumen 30 garr/dia (ESTIMADO de docs)."""
import json, csv, glob, math, shutil, os, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *a: os.path.join(R, *a)
OUT = J('b4', 'data')
os.makedirs(OUT, exist_ok=True)

# ---------- SUPUESTOS ----------
SEP_M = 600.0          # SUPUESTO: separacion minima entre estaciones propias en una colonia = 2 x radio caminable 300 m
RADIO_CAM_M = 300.0    # SUPUESTO: radio caminable (mismo radio que el modelo usa para competencia: R_comp_m=300)
UMBRAL_CELDA = 0.60    # SUPUESTO: una 2a/3a estacion solo si su celda >= 60 % de la mejor celda de la colonia
MAX_EST = 3            # pedido: 1-3 estaciones por colonia
METRO_INFO_M = 1000.0  # solo informativo (no entra al score)

def dist(a, b):  # (lat,lon) en m, proyeccion local
    return math.hypot((a[0]-b[0])*110540.0, (a[1]-b[1])*111320.0*math.cos(math.radians(25.7)))

# ---------- cells por colonia ----------
cells = collections.defaultdict(list)
for f in sorted(glob.glob(J('v2', 'data', 'cells_*.geojson'))):
    for ft in json.load(open(f))['features']:
        p = ft['properties']; lon, lat = ft['geometry']['coordinates']
        cells[p['k']].append((p['s'], lat, lon))

# ---------- banda de confianza ----------
band = {r['cve_col']: r for r in csv.DictReader(open(J('v2', 'data', 'colonias_v3_banda_confianza.csv'), encoding='utf-8'))}

# ---------- metro (v3_espectaculares) ----------
metro = []
for r in csv.DictReader(open(J('v3_espectaculares', 'data', 'metro_afluencia_indice.csv'), encoding='utf-8')):
    metro.append({'n': r['estacion'], 'l': r['linea'], 'lat': float(r['lat']), 'lon': float(r['lon']), 'i': float(r['indice_afluencia'])})
json.dump(metro, open(J('b4', 'data', 'metro_estaciones.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- colonias_b4.geojson ----------
src = json.load(open(J('v2', 'data', 'colonias_v3.geojson'), encoding='utf-8'))
# ---------- SCORE B4 (competencia SUMA) ----------
# score_b4 = 100 x (0.40*Demanda* + 0.30*Anclas* + 0.30*Comp_bonus*)   (docs/B4_FORMULA.md)
# Comp_bonus* = min(P, CAP_P)/CAP_P, P = percentil de purificadoras a <=300 m por 1,000 viviendas (= C_star de v3, 0 comp => 0).
# SUPUESTO: tope en p80 (CAP_P = 0.80). La formula anterior (competencia RESTA: 1-C_star) queda como score_prev / rank_prev.
W_D, W_A, W_C = 0.40, 0.30, 0.30
CAP_P = 0.80            # SUPUESTO
def comp_bonus(c): return min(c, CAP_P) / CAP_P
def rank_by(feats, key, tie):
    order = sorted(feats, key=lambda p: (-p[key], p[tie]))
    for i, p in enumerate(order): p['_r_'+key] = i + 1
for ft in src['features']:
    p = ft['properties']
    p['score_prev'] = p['score_base']; p['rank_prev'] = p['rank_base']
    p['score_with_scout_prev'] = p['score_with_scout']; p['rank_with_scout_prev'] = p['rank_with_scout']
    p['Cb_star'] = round(comp_bonus(p['C_star']), 4)
    p['score_base'] = round(100 * (W_D*p['D_star'] + W_A*p['A_star'] + W_C*comp_bonus(p['C_star'])), 2)
    p['score_with_scout'] = round(100 * (W_D*p['D_star'] + W_A*p['A_star_scout'] + W_C*comp_bonus(p['C_star_scout'])), 2)
    p['sin_verificar'] = p['comp_n_300m'] == 0     # 0 competidores => bonus 0 y marca 'sin verificar'
_P = [ft['properties'] for ft in src['features']]
rank_by(_P, 'score_base', 'rank_prev'); rank_by(_P, 'score_with_scout', 'rank_with_scout_prev')
for p in _P:
    p['rank_base'] = p.pop('_r_score_base'); p['rank_with_scout'] = p.pop('_r_score_with_scout')
    p['scout_bonus'] = round(p['score_with_scout'] - p['score_base'], 2)
    p['delta_rank_v2_to_base'] = p['v2_rank'] - p['rank_base']
    p['delta_rank_base_to_scout'] = p['rank_base'] - p['rank_with_scout']
    p['delta_rank_prev_to_b4'] = p['rank_prev'] - p['rank_base']

sites_fc = []
dist_n = collections.Counter()
for ft in src['features']:
    p = ft['properties']; k = p['cve_col']
    for drop in ('best', 'cells_file', 'A_star_scout', 'C_star_scout'):
        p.pop(drop, None)
    b = band.get(k)
    if b:
        for c in ('rank_p10', 'rank_p50', 'rank_p90', 'ancho_banda'):
            p[c] = int(float(b[c]))
        p['banda'] = b['banda']; p['confianza'] = b['confianza']
        p['prob_top30'] = float(b['prob_top30']); p['prob_top30_estres'] = float(b['prob_top30_estres'])
        p['comp_cero_desconocido'] = b['comp_cero_desconocido'] == 'True'
    # estaciones sugeridas
    cl = sorted(cells.get(k, []), reverse=True)
    acc = []
    if cl:
        acc = [cl[0]]
        for c in cl[1:]:
            if len(acc) >= MAX_EST: break
            if c[0] >= UMBRAL_CELDA * cl[0][0] and all(dist(c[1:], a[1:]) >= SEP_M for a in acc):
                acc.append(c)
    p['n_est_sugeridas'] = len(acc)
    p['est'] = [[round(a[2], 5), round(a[1], 5), a[0]] for a in acc]
    dist_n[len(acc)] += 1
    for i, a in enumerate(acc):
        sites_fc.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(a[2], 5), round(a[1], 5)]},
                         'properties': {'k': k, 'c': p['colonia'], 'm': p['municipio'], 'i': i+1, 'n': len(acc), 's': a[0], 'rb': p['rank_base']}})
    # metro mas cercano (informativo)
    if 'lat' in p:
        best = min(metro, key=lambda m: dist((p['lat'], p['lon']), (m['lat'], m['lon'])))
        d = dist((p['lat'], p['lon']), (best['lat'], best['lon']))
        if d <= METRO_INFO_M:
            p['metro_cerca'] = {'n': best['n'], 'l': best['l'], 'd': int(round(d)), 'i': best['i']}
json.dump(src, open(J('b4', 'data', 'colonias_b4.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'type': 'FeatureCollection', 'features': sites_fc}, open(J('b4', 'data', 'estaciones_sugeridas.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- spots con separacion B4 (filtro greedy sobre spots_v3) ----------
sp = json.load(open(J('v2', 'data', 'spots_v3.json'), encoding='utf-8'))
rows = sp['rows']
def filt(idx):
    out = []
    for i in idx:
        r = rows[i]
        if all(dist((r['lat'], r['lon']), (rows[j]['lat'], rows[j]['lon'])) >= SEP_M for j in out):
            out.append(i)
    return out
overall = filt(sp['overall']); muni = {m: filt(v) for m, v in sp['muni'].items()}
newrows = {}
for lst in [overall] + list(muni.values()):
    for i in lst: newrows[i] = True
remap = {i: n for n, i in enumerate(sorted(newrows))}
rows2 = [rows[i] for i in sorted(newrows)]
for n, i in enumerate(overall): rows[i]['rank_zmm'] = n+1
for m, lst in muni.items():
    for n, i in enumerate(lst): rows[i]['rank_muni'] = n+1
spots = {'note': sp['note'] + ' B4: separacion minima 600 m (SUPUESTO) aplicada sobre las filas de spots_v3 (se descartan las que quedan a <600 m de otra mejor).',
         'sep_m': SEP_M, 'n_original_zmm': len(sp['overall']), 'rows': rows2,
         'overall': [remap[i] for i in overall], 'muni': {m: [remap[i] for i in l] for m, l in muni.items()}}
json.dump(spots, open(J('b4', 'data', 'spots_b4.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- copias de capas (solo lectura del original) ----------
for f in ('manifest_v3.json', 'cambios_v3.json', 'anclas_v3.geojson', 'competencia_v3.geojson', 'semaforos_altos_v3.geojson',
          'scout_marks_v3.geojson', 'trafico_vias.geojson') + tuple(os.path.basename(x) for x in glob.glob(J('v2', 'data', 'cells_*.geojson'))):
    shutil.copyfile(J('v2', 'data', f), J('b4', 'data', f))

# ---------- ECONOMIA ----------
PRECIO_MAQ = 87000.0            # DATO Nicolas
META = 21750.0                  # DATO usuario/reporte (no verificado)
PRECIO_GARR = 12.0              # DATO (docs)
RENTA = 1000.0                  # DATO usuario/reporte (no verificado) -- UNIT_ECONOMICS_RECONCILIADO
OTROS_PEOR, OTROS_MEJOR = 0.85, 0.30   # ESTIMADO (RECONCILIADO) luz+filtros+sal por garrafon
tar = {int(r['m3_mes']): r for r in csv.DictReader(open(J('data', 'sadm_tarifas_sep2026_cat2_cat6.csv'), encoding='utf-8'))}
def agua(garr, rec, cat):
    m3 = garr*19/1000/rec
    m3f = math.ceil(round(m3, 6))
    r = tar[m3f]
    if cat == 'cat2': return m3, m3f, float(r['cat2_valor_consumo_mxn'])+float(r['cat2_cargo_fijo_mxn'])
    return m3, m3f, float(r['cat6_valor_consumo_mxn'])+float(r['cat6_cargo_fijo_mxn'])
# escenarios: id, etiqueta, categoria, recuperacion, garr/dia, agua plana por garr (None si tarifa)
ESC = [
 ('BASE', 'BASE B4: Cat. 6 comercial @80 % · 30 garr/día', 'cat6', 0.80, 30, None),
 ('S_CAT2', 'Sensibilidad SADM: Cat. 2 doméstica @80 %', 'cat2', 0.80, 30, None),
 ('S_C6_65', 'Cat. 6 @65 % recuperación', 'cat6', 0.65, 30, None),
 ('S_C6_50', 'Cat. 6 @50 % recuperación', 'cat6', 0.50, 30, None),
 ('S_C2_50', 'Cat. 2 @50 % recuperación', 'cat2', 0.50, 30, None),
 ('S_FLAT250', 'Agua plana $2.50/garr @80 % [NICOLÁS, sin tarifa]', 'plano', 0.80, 30, 2.50),
 ('V25', 'Cat. 6 @80 % · 25 garr/día', 'cat6', 0.80, 25, None),
 ('V20', 'Cat. 6 @80 % · 20 garr/día', 'cat6', 0.80, 20, None),
 ('V15', 'Cat. 6 @80 % · 15 garr/día', 'cat6', 0.80, 15, None),
 ('V40', 'Cat. 6 @80 % · 40 garr/día', 'cat6', 0.80, 40, None),
 ('V20_C2', 'Cat. 2 @80 % · 20 garr/día', 'cat2', 0.80, 20, None),
]
def fmt(x, d=2): return '' if x is None else f'{x:.{d}f}'
econ = []
for eid, lbl, cat, rec, gd, flat in ESC:
    g = gd*30
    ing = g*PRECIO_GARR
    if flat is None: m3, m3f, a = agua(g, rec, cat)
    else: m3, m3f, a = g*19/1000/rec, None, g*flat
    mp = ing - RENTA - a - OTROS_PEOR*g
    mm = ing - RENTA - a - OTROS_MEJOR*g
    row = {'id': eid, 'escenario': lbl, 'categoria_sadm': cat, 'recuperacion': rec, 'garr_dia': gd, 'garr_mes': g,
           'ingreso_mes': ing, 'renta_mes': RENTA, 'm3_facturados': m3f, 'agua_mes': round(a, 2), 'agua_por_garr': round(a/g, 3),
           'margen_peor': round(mp, 2), 'margen_mejor': round(mm, 2)}
    for lab, m in (('peor', mp), ('mejor', mm)):
        row['payback_1est_meses_'+lab] = round(PRECIO_MAQ/m, 1) if m > 0 else None
        n = math.ceil(META/m) if m > 0 else None
        row['est_para_meta_'+lab] = n
        row['payback_4est_meses_'+lab] = round(4*PRECIO_MAQ/(4*m), 1) if m > 0 else None  # = 1 est (todas iguales); explicito
        row['capital_4est'] = 4*PRECIO_MAQ
        row['margen_4est_'+lab] = round(4*m, 2)
        row['capital_est_meta_'+lab] = (n*PRECIO_MAQ) if n else None
        row['payback_est_meta_meses_'+lab] = round(n*PRECIO_MAQ/(n*m), 1) if n else None
        row['cubre_meta_con_4_'+lab] = 4*m >= META
    econ.append(row)
cols = list(econ[0].keys())
with open(J('data', 'b4_escenarios.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); [w.writerow(r) for r in econ]

# ---------- ESCALONADO (SUPUESTO): 1 estacion abre por mes; rampa 50/75/100 % de 30 garr/dia ----------
RAMP = [0.50, 0.75, 1.00]   # SUPUESTO
def margen_vol(f, otros, cat='cat6', rec=0.80):
    g = 900*f
    m3, m3f, a = agua(g, rec, cat)
    return g*PRECIO_GARR - RENTA - a - otros*g
def simular(n, otros, cat='cat6'):
    cum = 0.0; capital = n*PRECIO_MAQ; mes = 0
    while cum < capital and mes < 200:
        mes += 1
        for k in range(n):               # estacion k abre en el mes k+1
            t = mes-(k+1)
            if t < 0: continue
            f = RAMP[t] if t < len(RAMP) else 1.0
            cum += margen_vol(f, otros, cat)
    return mes
esc_rows = []
for n in (1, 3, 4):
    for cat in ('cat6', 'cat2'):
        esc_rows.append({'id': f'ESCAL_{n}_{cat}', 'n': n, 'cat': cat, 'peor': simular(n, OTROS_PEOR, cat), 'mejor': simular(n, OTROS_MEJOR, cat)})
for r in esc_rows: print('ESCAL', r)
with open(J('data', 'b4_escalonado.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['id', 'n_estaciones', 'categoria_sadm', 'capital', 'meses_hasta_payback_peor', 'meses_hasta_payback_mejor', 'supuesto'])
    for r in esc_rows: w.writerow([r['id'], r['n'], r['cat'], r['n']*PRECIO_MAQ, r['peor'], r['mejor'], 'SUPUESTO: 1 estacion abre por mes; rampa 50/75/100 % en meses 1/2/3 de cada estacion; 30 garr/dia a plena; 80 % recuperacion; otros costos peor 0.85 / mejor 0.30'])

json.dump({'precio_maquina': PRECIO_MAQ, 'meta': META, 'precio_garr': PRECIO_GARR, 'renta': RENTA, 'otros_peor': OTROS_PEOR, 'otros_mejor': OTROS_MEJOR,
           'sep_m': SEP_M, 'radio_cam_m': RADIO_CAM_M, 'umbral_celda': UMBRAL_CELDA, 'rows': econ, 'escalonado': esc_rows,
           'dist_est': dict(dist_n)}, open(J('b4', 'data', 'economia.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('est dist', dict(dist_n), 'total sitios', len(sites_fc))
print('spots overall', len(sp['overall']), '->', len(overall))
for r in econ: print(r['id'], r['agua_mes'], r['margen_peor'], r['margen_mejor'], r['payback_1est_meses_peor'], r['payback_1est_meses_mejor'], r['est_para_meta_peor'], r['est_para_meta_mejor'])
