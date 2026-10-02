#!/usr/bin/env python3
"""Colonias con 0 competidores <=300 m (v3 base): cobertura de fuentes, anclas, rango, clasificacion 'cero real' vs 'brecha de datos' (solo evidencia).
NO modifica ningun score. Lee data/*.geojson y v2/data/colonias_v3.csv; escribe v2/data/colonias_competencia_cero.csv y docs/COMPETENCIA_CERO.md. Sin red."""
import json, math, os, re, numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.prepared import prep
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda f: os.path.join(ROOT, "data", f)
LAT0 = 25.70; KX = 111320.0 * math.cos(math.radians(LAT0)); KY = 110540.0
to_m = lambda lon, lat: ((lon + 100.3) * KX, (lat - LAT0) * KY)
def feats(f): return json.load(open(D(f), encoding="utf-8"))["features"]
def pts(f, filt=lambda p: True):
    return [to_m(*x["geometry"]["coordinates"][:2]) for x in feats(f) if x["geometry"]["type"] == "Point" and filt(x["properties"])]
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
cols = {f["properties"]["cve_col"]: f for f in feats("colonias.geojson")}
geom = {k: transform(lambda x, y, z=None: to_m(x, y), shape(f["geometry"])) for k, f in cols.items()}
# capas por fuente
L = {
 "denue": {"abarrotes": pts("anclas_abarrotes_zmm.geojson", lambda p: "denue" in p.get("s", "")), "tortilleria": pts("anclas_tortillerias_zmm.geojson", lambda p: "denue" in p.get("s", "")),
           "farmacia": pts("anclas_farmacias_barrio_zmm.geojson", lambda p: "denue" in p.get("s", "")), "banco": pts("anclas_bancos_prestamo_zmm.geojson", lambda p: "denue" in p.get("s", ""))},
 "places": {"anclas": pts("places_anclas_zmm.geojson"), "barrio": pts("places_anclas_barrio_zmm.geojson"), "purificadoras": pts("places_purificadoras_zmm.geojson"),
            "paradas": pts("anclas_paradas_zmm.geojson", lambda p: "places" in p.get("s", "")), "tortilleria": pts("anclas_tortillerias_zmm.geojson", lambda p: "places" in p.get("s", ""))},
 "osm": {"barrio": pts("osm_anclas_barrio_zmm.geojson"), "anclas": pts("anclas.geojson"), "retail": pts("retail.geojson"), "paradas": pts("anclas_paradas_zmm.geojson", lambda p: "osm" in p.get("s", ""))},
}
flat = {s: np.array([p for lst in d.values() for p in lst]) for s, d in L.items()}
# competidores: base dedupe (competencia_v3.geojson = comp_b) y crudos DENUE/Places antes de filtro industrial
comp_b = np.array([to_m(*x["geometry"]["coordinates"]) for x in json.load(open(f"{ROOT}/v2/data/competencia_v3.geojson"))["features"]])
denue_raw = np.array(pts("compet.geojson")); places_raw = np.array(pts("places_purificadoras_zmm.geojson"))
scout_c = []
fa = feats("field_adds.geojson"); deleted = set(json.load(open(D("field_adds_deleted.json"))))
for f in fa:
    p = f["properties"]
    if p.get("id") in deleted: continue
    txt = (p.get("name") or "") + " " + (p.get("nota_raw") or "") + " " + (p.get("descripcion") or "")
    if p.get("kind") == "purificadora" or (p.get("kind") == "otro" and re.search(r"purificador|recarga de agua|garraf", txt, re.I)): scout_c.append(to_m(*f["geometry"]["coordinates"]))
scout_c = np.array(scout_c)
def inpoly(arr, g, buf):
    if len(arr) == 0: return 0
    gg = prep(g.buffer(buf)); minx, miny, maxx, maxy = g.buffer(buf).bounds
    return sum(1 for x, y in arr if minx <= x <= maxx and miny <= y <= maxy and gg.contains(Point(x, y)))
def edge_dist(arr, g):
    if len(arr) == 0: return None
    return min(g.distance(Point(x, y)) for x, y in arr)
z = v[v.comp_n_300m == 0].copy()
# tasa de deteccion de referencia: competidores <=300 m por 1000 viv, TODAS las colonias (v3 base)
rate = v.comp_n_300m.sum() / (v.viviendas_est.sum() / 1000.0)
rate_pos = None
rows = []
for _, r in z.iterrows():
    g = geom[r.cve_col]
    rec = {"cve_col": r.cve_col, "colonia": r.colonia, "municipio": r.municipio, "rank_base": r.rank_base, "score_base": r.score_base, "viviendas_est": r.viviendas_est,
           "anclas_pond": r.anclas_pond, "anclas_por_1000viv": r.anclas_por_1000viv, "n_abarrotes": r.n_abarrotes, "n_oxxo": r.n_oxxo, "n_tortilleria": r.n_tortilleria,
           "n_parada": r.n_parada, "n_farmacia": r.n_farmacia, "n_escuela": r.n_escuela, "n_iglesia": r.n_iglesia, "n_anclas_total": int(sum(r[f"n_{c}"] for c in ["cerveza", "tortilleria", "banco_bienestar_azteca", "oxxo", "express", "iglesia", "escuela", "parada", "farmacia", "abarrotes"])),
           "scout_marks": r.scout_marks, "cobertura_campo": r.cobertura_campo, "comp_300m_con_scout": r.comp_n_300m_with_scout,
           "denue_pts_zona": sum(inpoly(np.array(l), g, 100) for l in L["denue"].values()), "places_pts_zona": sum(inpoly(np.array(l), g, 100) for l in L["places"].values()),
           "osm_pts_zona": sum(inpoly(np.array(l), g, 100) for l in L["osm"].values()),
           "denue_compet_crudo_300m": inpoly(denue_raw, g, 300), "places_purif_crudo_300m": inpoly(places_raw, g, 300),
           "scout_purif_300m": inpoly(scout_c, g, 300)}
    d = edge_dist(comp_b, g); rec["dist_competidor_mas_cercano_m"] = round(d) if d is not None else None
    rec["competidores_<=600m_borde"] = int(sum(1 for x, y in comp_b if g.distance(Point(x, y)) <= 600))
    rec["competidores_<=1000m_borde"] = int(sum(1 for x, y in comp_b if g.distance(Point(x, y)) <= 1000))
    lam = rate * r.viviendas_est / 1000.0
    rec["esperados_si_tasa_media"] = round(lam, 2); rec["p_cero_si_tasa_media"] = round(math.exp(-lam), 3)
    rows.append(rec)
o = pd.DataFrame(rows)
# umbrales de referencia (de las 167 colonias, evidencia)
act = lambda df: df.n_abarrotes + df.n_oxxo + df.n_tortilleria
v["_act"] = act(v); v["_act_k"] = v._act / (v.viviendas_est / 1000)
o["comercio_barrio_por_1000viv"] = ((o.n_abarrotes + o.n_oxxo + o.n_tortilleria) / (o.viviendas_est / 1000)).round(1)
med_act = float(v._act_k.median())
def clasif(r):
    why = []
    if r.scout_purif_300m > 0 or r.comp_300m_con_scout > 0:
        return "brecha_confirmada_por_scout", f"Scout marcó {int(max(r.scout_purif_300m, r.comp_300m_con_scout))} purificadora(s) ≤300 m que DENUE/Places no tenían", 0, 0
    gap = 0
    if r.p_cero_si_tasa_media <= 0.15: gap += 1; why.append(f"p(0)≈{r.p_cero_si_tasa_media:.2f} con tasa media ({r.esperados_si_tasa_media:.1f} esperados)")
    if r.comercio_barrio_por_1000viv >= med_act: gap += 1; why.append(f"comercio de barrio {r.comercio_barrio_por_1000viv:.0f}/1000 viv ≥ mediana {med_act:.0f}")
    if r.dist_competidor_mas_cercano_m is not None and r.dist_competidor_mas_cercano_m <= 600: gap += 1; why.append(f"competidor a {r.dist_competidor_mas_cercano_m} m del borde (vecino)")
    if (r.denue_compet_crudo_300m + r.places_purif_crudo_300m) > 0: gap += 1; why.append("hay puntos DENUE/Places ≤300 m excluidos como industrial/marca")
    if r.places_pts_zona == 0 or r.denue_pts_zona == 0: gap += 1; why.append("sin puntos de " + ("Places" if r.places_pts_zona == 0 else "DENUE") + " en la zona (cobertura débil)")
    real = 0; rwhy = []
    if r.p_cero_si_tasa_media >= 0.40: real += 1; rwhy.append(f"p(0)≈{r.p_cero_si_tasa_media:.2f} (colonia chica)")
    if r.dist_competidor_mas_cercano_m is None or r.dist_competidor_mas_cercano_m > 1000: real += 1; rwhy.append("ningún competidor ≤1 km")
    if r.cobertura_campo == "encuestada": real += 1; rwhy.append("Scout ≥10 marcas sin purificadora")
    if r.comercio_barrio_por_1000viv < med_act and r.places_pts_zona > 0 and r.denue_pts_zona > 0: real += 1; rwhy.append("comercio bajo con cobertura DENUE+Places")
    if gap >= 3 and gap > real: return "brecha_probable", "; ".join(why), gap, real
    if real >= 3 and real > gap: return "cero_real_probable", "; ".join(rwhy), gap, real
    if gap >= 2 and gap > real: return "indeterminado_inclina_brecha", "; ".join(why), gap, real
    if real >= 2 and real > gap: return "indeterminado_inclina_real", "; ".join(rwhy), gap, real
    return "indeterminado", "; ".join(why[:2] + rwhy[:2]), gap, real
cl = o.apply(clasif, axis=1, result_type="expand"); o["clasificacion"] = cl[0]; o["evidencia"] = cl[1]; o["senales_brecha"] = cl[2]; o["senales_real"] = cl[3]
o = o.sort_values("rank_base")
# prioridad Scout: sin encuesta (0 marcas), no brecha ya confirmada, ordenadas por rank_base (donde verificar cambia la decision)
cand = o[(o.cobertura_campo != "encuestada") & (~o.clasificacion.isin(["brecha_confirmada_por_scout", "cero_real_probable", "indeterminado_inclina_real"]))]
pri = cand.sort_values("rank_base").head(15).copy(); pri["prioridad_scout"] = range(1, len(pri) + 1)
o["prioridad_scout"] = o.cve_col.map(dict(zip(pri.cve_col, pri.prioridad_scout)))
o["etiqueta"] = "heuristica con evidencia (no es verdad de campo); no altera score"
o.to_csv(f"{ROOT}/v2/data/colonias_competencia_cero.csv", index=False)
cnt = o.clasificacion.value_counts().to_dict()
print(len(o), cnt, "rate", round(rate, 3), "med_act", round(med_act, 1))
# ---------- doc ----------
W = []; w = W.append
w("# Competencia cero: 58 colonias sin competidores ≤300 m\n")
w("Etiqueta: **heurística con evidencia** (conteos de archivos locales); no es verdad de campo y **no altera ningún score** (`v2/data/colonias_v3.csv` intacto). Script: `scripts/analisis_competencia_cero.py` (sin red). Tabla completa: `v2/data/colonias_competencia_cero.csv` (58 filas).\n")
w("## 1. Qué es el «0»\n")
w(f"- v3 base cuenta purificadoras dentro del polígono+300 m (DENUE 312112 filtrado + Places, dedupe 30 m). **{len(o)} de 167** colonias dan 0 → Comp\\*=0 → reciben los 30 pts completos de «(1−Comp)». Con marcas Scout bajan a **{int((v.comp_n_300m_with_scout==0).sum())}**: Scout encontró competidores ≤300 m en **{len(o)-int((v.comp_n_300m_with_scout==0).sum())}** de estas 58 que DENUE/Places no veían (esa es la evidencia directa de brecha de datos).")
w(f"- Tasa media de detección (todas las colonias): **{rate:.2f} competidores ≤300 m por 1 000 viv.** Si una colonia tuviera esa tasa, la probabilidad de observar 0 es `exp(−tasa×viv/1000)` (columna `p_cero_si_tasa_media`). Para colonias grandes, un 0 es poco creíble.")
exp0 = float(np.exp(-rate * v.viviendas_est / 1000).sum())
w(f"- **Chequeo global:** con esa tasa homogénea se esperarían **{exp0:.0f}** colonias con 0 y se observan **{len(o)}**. Es decir, el número de ceros **no es mayor** que el que produce una detección escasa pero pareja: no hay prueba estadística de que el conjunto sea un hueco de datos; el problema es que la tasa misma (1 por 1 000 viv.) es un piso (informales invisibles), así que los 0 individuales no son confiables.")
w("- DENUE ve 93 formales; informales no se ven; Places trae máx. 60 por búsqueda/tile (ver `docs/RATING_V3.md` §4).\n")
w("## 2. Regla de clasificación (transparente)\n")
w(f"1. **brecha_confirmada_por_scout**: Scout marcó purificadora ≤300 m.\n2. **brecha_probable**: ≥3 señales de brecha y más que las de «real». Señales de brecha: p(0)≤0.15; comercio de barrio (abarrotes+Oxxo+tortillerías)/1 000 viv ≥ mediana de las 167 ({med_act:.0f}); competidor a ≤600 m del borde; puntos DENUE/Places ≤300 m descartados (industrial/marca); sin puntos de Places o DENUE en la zona.\n3. **cero_real_probable**: ≥3 señales de «real»: p(0)≥0.40; ningún competidor ≤1 km; Scout ≥10 marcas sin purificadora; comercio bajo con cobertura DENUE+Places.\n4. **indeterminado_inclina_brecha / _inclina_real**: 2 señales de un lado y más que del otro. **indeterminado**: el resto → verificar en campo.\n")
w("«Real» sólo significa «sin evidencia de que falte dato»; ninguna categoría prueba que no haya competencia informal.\n")
w("## 3. Resultado\n")
w("| Clasificación | Colonias |\n|---|--:|")
for k in ["brecha_confirmada_por_scout", "brecha_probable", "indeterminado_inclina_brecha", "indeterminado", "indeterminado_inclina_real", "cero_real_probable"]: w(f"| {k} | {cnt.get(k,0)} |")
top = o[o.rank_base <= 30]
w(f"\nEn el **top-30 del ranking base** hay **{len(top)}** de estas colonias: " + ", ".join(f"{r.colonia} (#{r.rank_base}, {r.clasificacion})" for _, r in top.iterrows()) + ".\n")
w(f"Cobertura de fuentes (puntos en polígono+100 m): sin ningún punto DENUE: {int((o.denue_pts_zona==0).sum())}; sin Places: {int((o.places_pts_zona==0).sum())}; sin OSM: {int((o.osm_pts_zona==0).sum())}. Colonias con competidor a ≤600 m del borde: {int((o.dist_competidor_mas_cercano_m<=600).sum())}; sin competidor ≤1 km: {int(((o.dist_competidor_mas_cercano_m>1000)|o.dist_competidor_mas_cercano_m.isna()).sum())}.\n")
w("## 4. Las 58 colonias\n")
w("| # base | Colonia | Municipio | Viv. | Anclas pond. | Abarr./Oxxo/Tort. | DENUE / Places / OSM (pts) | Comp. más cercano (m) | p(0) | Scout (marcas · comp.) | Clasificación |\n|--:|---|---|--:|--:|---|---|--:|--:|---|---|")
for _, r in o.iterrows():
    w(f"| {r.rank_base} | {r.colonia} | {r.municipio} | {int(r.viviendas_est)} | {r.anclas_pond:.1f} | {int(r.n_abarrotes)}/{int(r.n_oxxo)}/{int(r.n_tortilleria)} | {int(r.denue_pts_zona)} / {int(r.places_pts_zona)} / {int(r.osm_pts_zona)} | {'' if pd.isna(r.dist_competidor_mas_cercano_m) else int(r.dist_competidor_mas_cercano_m)} | {r.p_cero_si_tasa_media:.2f} | {int(r.scout_marks)} · {int(r.comp_300m_con_scout)} | {r.clasificacion} |")
w("\n## 5. Prioridad Scout (top 15)\n")
w("Criterio: colonias de esta lista con cobertura Scout **no completa** (<10 marcas; incluye 1 sola marca), que no sean ya «brecha confirmada», «cero real probable» ni «inclina real», ordenadas por rank base (donde verificar puede cambiar una decisión de zona). Sólo orden de visita; no cambia scores.\n")
w("| Prioridad | # base | Colonia | Municipio | Clasificación | Evidencia |\n|--:|--:|---|---|---|---|")
for _, r in pri.iterrows():
    w(f"| {r.prioridad_scout} | {r.rank_base} | {r.colonia} | {r.municipio} | {r.clasificacion} | {r.evidencia} |")
w("\nQué verificar en campo (10–15 min por colonia): recorrer las calles comerciales; contar recargas/purificadoras informales (sin letrero), precio de recarga y garrafón; anotar en Scout (kind `purificadora`). Una brecha confirmada ya baja el score «con Scout» (ver `docs/CAMBIOS_RANKING_V3.md`).\n")
w("## 6. Límites\n- Heurística sobre los mismos datos que generan el 0: no puede ver competidores que ninguna fuente tiene; sólo detecta incoherencias (comercio alto/colonia grande/vecinos cercanos).\n- `p(0)` supone tasa homogénea (Poisson); la densidad real de recargas varía por NSE y zona.\n- Viviendas = pob/3.6 (ver `docs/SENSIBILIDAD_VIVIENDAS.md`: sobrestima ~10 %; el efecto en p(0) es pequeño).\n- Cada señal es débil por separado (p. ej. «comercio ≥ mediana» lo cumple la mitad de las colonias por construcción; «competidor a ≤600 m» es común). La clasificación sólo ordena dónde mirar primero.\n- Scout cubre 17 de 167 colonias; «sin encuesta» ≠ «sin competencia».")
open(f"{ROOT}/docs/COMPETENCIA_CERO.md", "w", encoding="utf-8").write("\n".join(W) + "\n")
