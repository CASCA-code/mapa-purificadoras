#!/usr/bin/env python3
"""Gaps rating v3 base vs densidad (viv/km2, hab/km2). Sin red. Solo lee archivos locales.
Salida: docs/GAPS_RATING_DENSIDAD.md + v2/data/gaps_rating_densidad.csv. NO toca scores."""
import csv, json, math, statistics as st, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
GEOD = Path("/home/box/geo/inegi_purificador/datos")
rows = list(csv.DictReader(open(ROOT/"v2/data/colonias_v3.csv", encoding="utf-8")))
cens = {r["cve_col"]: r for r in csv.DictReader(open(GEOD/"colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv", encoding="utf-8"))}
geom = {f["properties"]["cve_col"]: f["properties"] for f in json.load(open(GEOD/"colonias167_conapo_geom.geojson"))["features"]}
W = dict(D=0.40, A=0.30, C=0.30)

def pct(vals):
    o = sorted(range(len(vals)), key=lambda i: vals[i]); r = [0]*len(vals)
    i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and vals[o[j+1]] == vals[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2/(len(vals)-1)
        i = j+1
    return r

out = []
for r in rows:
    k = r["cve_col"]; g = geom[k]; c = cens[k]
    area = float(g["area_km2"])
    viv_est = float(r["viviendas_est"]); viv_cen = float(c["viv_hab_censo_est"]); pob = float(r["pob_conapo"])
    d = dict(cve_col=k, colonia=r["colonia"], municipio=r["municipio"], rank_base=int(r["rank_base"]), score_base=float(r["score_base"]),
             area_km2=area, pob_conapo=pob, viviendas_est=viv_est, viv_censo_modelo=viv_cen,
             dens_viv_est_km2=viv_est/area, dens_viv_censo_km2=viv_cen/area, dens_pob_km2=pob/area,
             D_star=float(r["D_star"]), A_star=float(r["A_star"]), C_star=float(r["C_star"]),
             pts_D=100*W["D"]*float(r["D_star"]), pts_A=100*W["A"]*float(r["A_star"]), pts_C=100*W["C"]*(1-float(r["C_star"])),
             pob_eff=float(g["pob_eff"]), demanda_raw=float(g["demanda_raw"]),
             intensidad=(float(g["demanda_raw"])/float(g["pob_eff"]) if float(g["pob_eff"]) else 0.0),
             comp_n_300m=int(r["comp_n_300m"]), anclas_por_1000viv=float(r["anclas_por_1000viv"]))
    out.append(d)

N = len(out)
pd = pct([o["dens_viv_censo_km2"] for o in out]); ps = pct([o["score_base"] for o in out])
for o, a, b in zip(out, pd, ps):
    o["pct_dens"] = a; o["pct_score"] = b; o["gap"] = a - b   # + = denso pero score bajo
med = {k: st.median(o[k] for o in out) for k in ("pts_D", "pts_A", "pts_C")}
top_dens = [o for o in out if o["pct_dens"] >= 0.75]
ref = {k: st.median(o[k] for o in top_dens) for k in ("pts_D", "pts_A", "pts_C")}
lab = {"pts_D": "Demanda*", "pts_A": "Anclas*", "pts_C": "(1-Comp*)"}

MED_INT = st.median(o['intensidad'] for o in out)
def reason(o, under):
    # under: que componente queda mas abajo de la mediana del 25% mas denso; over: cual esta mas arriba
    dif = {k: o[k] - ref[k] for k in ref}
    ks = sorted(dif, key=lambda k: dif[k])
    ks = ks if under else ks[::-1]
    k = ks[0]
    parts = [f"{lab[x]} {o[x]:.1f} pts vs mediana-denso {ref[x]:.1f}" for x in ks[:2]]
    extra = ""
    if under and k == "pts_D": extra = f"; pob_eff {o['pob_eff']:,.0f}, intensidad OVHAC/OVSAE {o['intensidad']:.3f} (mediana {MED_INT:.3f})"
    if under and k == "pts_C": extra = f"; {o['comp_n_300m']} competidores<=300m"
    if under and k == "pts_A": extra = f"; anclas {o['anclas_por_1000viv']:.1f}/1000 viv"
    if (not under) and k == "pts_C": extra = f"; {o['comp_n_300m']} competidores<=300m (Comp*=0 si 0)"
    return lab[k], "; ".join(parts) + extra

under = sorted(out, key=lambda o: -o["gap"])[:15]
over = sorted(out, key=lambda o: o["gap"])[:15]
fields = ["grupo","cve_col","colonia","municipio","rank_base","score_base","dens_viv_censo_km2","dens_viv_est_km2","dens_pob_km2","area_km2","viv_censo_modelo","pct_dens","pct_score","gap","D_star","A_star","C_star","pts_D","pts_A","pts_C","pob_eff","intensidad_OVHAC_OVSAE","comp_n_300m","componente_clave","detalle"]
with open(ROOT/"v2/data/gaps_rating_densidad.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for grp, lst, u in (("denso_score_bajo_posible_subvalorada", under, True), ("score_alto_denso_bajo_posible_sobrevalorada", over, False)):
        for o in lst:
            comp, det = reason(o, u)
            row = {k: (round(o[k], 3) if isinstance(o.get(k), float) else o.get(k)) for k in fields if k in o}
            row["intensidad_OVHAC_OVSAE"] = round(o["intensidad"], 3)
            row.update(grupo=grp, componente_clave=comp, detalle=det); w.writerow(row)

# correlacion Spearman score vs densidad
def spearman(a, b):
    ra, rb = pct(a), pct(b); ma, mb = st.mean(ra), st.mean(rb)
    return sum((x-ma)*(y-mb) for x, y in zip(ra, rb))/math.sqrt(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))
sp = {n: spearman([o[n] for o in out], [o["score_base"] for o in out]) for n in ("dens_viv_censo_km2","dens_viv_est_km2","dens_pob_km2","D_star","A_star","pts_C")}
sp_comp = spearman([o["dens_viv_censo_km2"] for o in out], [o["C_star"] for o in out])
sp_anc = spearman([o["dens_viv_censo_km2"] for o in out], [o["A_star"] for o in out])
sp_D = spearman([o["dens_viv_censo_km2"] for o in out], [o["D_star"] for o in out])

L = []
L.append("# Gaps: rating v3 base vs densidad de viviendas por colonia\n")
L.append("Etiqueta: **análisis con archivos locales** (script `scripts/analisis_gaps_rating_densidad.py`, sin red). **No altera ningún score** (`v2/data/colonias_v3.csv` intacto). CSV: `v2/data/gaps_rating_densidad.csv`.\n")
L.append("## Método\n")
L.append("- Densidad = viviendas habitadas (Censo 2020, modelo por traslape colonia-AGEB, `colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv`, columna `viv_hab_censo_est`) ÷ `area_km2` del polígono CONAPO (`colonias167_conapo_geom.geojson`). Se reportan también viv_est (CONAPO/3.6) y hab/km². **MODELO**: no es dato oficial por colonia.")
L.append("- Brecha = percentil de densidad − percentil de `score_base` (167 colonias). Positivo = denso con score bajo (posible subvalorada); negativo = score alto con densidad baja (posible sobrevalorada).")
L.append("- Razón por componente: puntos que aporta cada término a score_base (Demanda* ×40, Anclas* ×30, (1−Comp*) ×30) vs la mediana del 25 % más denso.")
L.append(f"- Spearman con score_base: densidad viv Censo {sp['dens_viv_censo_km2']:.2f} · viv_est {sp['dens_viv_est_km2']:.2f} · hab {sp['dens_pob_km2']:.2f}. Densidad vs Demanda* {sp_D:.2f} · vs Anclas* {sp_anc:.2f} · vs Comp* {sp_comp:.2f}.")
L.append(f"- Mediana puntos (todas): D {med['pts_D']:.1f} · A {med['pts_A']:.1f} · (1−C) {med['pts_C']:.1f}. Mediana del 25 % más denso (n={len(top_dens)}): D {ref['pts_D']:.1f} · A {ref['pts_A']:.1f} · (1−C) {ref['pts_C']:.1f}.\n")
def table(lst, u):
    t = ["| # | Colonia | Mun. | Rank base | Score | Viv/km² (Censo) | pct dens | pct score | D·A·(1−C) pts | Componente clave y razón |", "|--:|---|---|--:|--:|--:|--:|--:|---|---|"]
    for i, o in enumerate(lst, 1):
        comp, det = reason(o, u)
        t.append(f"| {i} | {o['colonia']} | {o['municipio']} | {o['rank_base']} | {o['score_base']:.1f} | {o['dens_viv_censo_km2']:,.0f} | {o['pct_dens']:.2f} | {o['pct_score']:.2f} | {o['pts_D']:.1f}·{o['pts_A']:.1f}·{o['pts_C']:.1f} | **{comp}**: {det} |")
    return "\n".join(t)
L.append("## 1. Denso pero score bajo (posible subvalorada) — top 15\n"); L.append(table(under, True)); L.append("")
L.append("## 2. Score alto pero densidad baja (posible sobrevalorada) — top 15\n"); L.append(table(over, False)); L.append("")
n_dz = sum(1 for o in under if o['pts_D'] < ref['pts_D'])
n_dz_pe = sum(1 for o in under if o['pts_D'] < ref['pts_D'] and o['pob_eff'] >= st.median(x['pob_eff'] for x in out))
n_ci = sum(1 for o in over if o['comp_n_300m'] == 0)
L.append("## 3. Lectura\n")
L.append(f"- **Score y densidad casi no se parecen** (Spearman {sp['dens_viv_censo_km2']:.2f}): el score no premia densidad por diseño. Demanda* = `pob_eff` × intensidad (0.85·OVHAC + 0.15·OVSAE, min-max) y Anclas*/Comp* están por 1 000 viv. del colonia, no por km².")
med_pe = st.median(x['pob_eff'] for x in out); med_in = st.median(x['intensidad'] for x in out)
n_lowpe = sum(1 for o in under if o['pts_D'] < ref['pts_D'] and o['pob_eff'] < med_pe)
n_lowin = sum(1 for o in under if o['pts_D'] < ref['pts_D'] and o['intensidad'] < med_in)
L.append(f"- Subvaloradas: {n_dz}/15 tienen Demanda* bajo la mediana del cuartil denso. De esas, {n_lowpe} tienen `pob_eff` < mediana de las 167 (colonia chica en habitantes) y {n_lowin} tienen intensidad OVHAC/OVSAE < mediana (hogares con poco hacinamiento / agua entubada). Es decir: densidad alta en polígonos pequeños + intensidad baja. Si Nicolás cree que densidad ≈ recarga (SUPUESTO, sin dato de ventas), son candidatas a revisar en campo; **no** se cambia el score.")
L.append(f"- Sobrevaloradas: {n_ci}/15 tienen 0 competidores ≤300 m (reciben 30/30 pts de (1−Comp*)) — ver `docs/COMPETENCIA_CERO.md`: el 0 es poco confiable; varias tienen además Anclas* alta (por 1 000 viv.; SUPUESTO: un denominador de viviendas chico infla la razón).")
L.append("- Limitación: viviendas/km² usa el área total del polígono CONAPO (incluye lotes baldíos/industria/cerros); colonias pequeñas tienen densidad ruidosa. Viv. Censo = MODELO por traslape de áreas con AGEB.")
L.append("")
EXTRA = ROOT/"scripts/_gaps_extra.md"
if EXTRA.exists(): L.append(EXTRA.read_text(encoding="utf-8"))
(ROOT/"docs/GAPS_RATING_DENSIDAD.md").write_text("\n".join(L), encoding="utf-8")
print("ok", sp, sp_comp, sp_anc, sp_D, ref, med)
for o in under[:5]+over[:5]: print(o["colonia"], round(o["gap"],2))
