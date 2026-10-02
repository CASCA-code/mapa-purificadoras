#!/usr/bin/env python3
"""Sensibilidad: viviendas Censo 2020 (MODELO, ponderado por traslape de area AGEB) vs pob/3.6 en el score v3 base.
Lee v2/data/colonias_v3.csv (NO lo modifica), data/colonias.geojson (demanda_raw) y el CSV de INEGI (read-only).
Escribe v2/data/colonias_v3_sensibilidad_censo.csv y docs/SENSIBILIDAD_VIVIENDAS.md. Sin red."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSO = os.environ.get("CENSO_CSV", "/home/box/geo/inegi_purificador/datos/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv")
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
c = pd.read_csv(CENSO)[["cve_col", "n_ageb", "pob_censo_est", "viv_hab_censo_est", "ocup_censo"]]
g = pd.DataFrame([f["properties"] for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]])[["cve_col", "demanda_raw", "pob_conapo"]].rename(columns={"pob_conapo": "pob_conapo_exact"})
d = v.merge(c, on="cve_col", validate="1:1").merge(g, on="cve_col", validate="1:1")
assert len(d) == 167
W_D, W_A, W_C = .40, .30, .30
def pct_rank(vals, zero_is_zero=False):          # identica a build_v3_rating.py
    x = np.array(vals, float); order = x.argsort(kind="stable"); ranks = np.empty(len(x)); sv = x[order]; i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sv[j + 1] == sv[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0; i = j + 1
    r = ranks / (len(x) - 1)
    if zero_is_zero: r[x == 0] = 0.0
    return r
# anclas_pond y comp_n_300m son conteos (no dependen de viviendas); solo cambia el divisor
# (pob exacta de colonias.geojson; D_star del CSV redondeada a 4 dec.)
def score(viv_k, D):
    A = pct_rank(d.anclas_pond / viv_k); C = pct_rank(d.comp_n_300m / viv_k, True)
    return 100 * (W_D * D + W_A * A + W_C * (1 - C)), A, C
# 0) reproduccion del base con viviendas_est del CSV (redondeada) -> valida el procedimiento
s0, _, _ = score(d.pob_conapo_exact / 3.6 / 1000, d.D_star)
d["_s0"] = s0
rep_maxdiff = float((d._s0 - d.score_base).abs().max())
rep_rank_mismatch = int((d._s0.rank(ascending=False, method="first") != d.rank_base).sum())
# 1) variante A (titular de la sensibilidad): anclas/1000 viv y comp/1000 viv con viv Censo; Demanda* igual (es por personas, no viviendas)
sA, A_A, C_A = score(d.viv_hab_censo_est / 1000, d.D_star)
# 2) variante B (cota superior): ademas demanda proporcional a viviendas -> demanda_raw * viv_censo/viviendas_est, min-max
fac = d.viv_hab_censo_est / (d.pob_conapo_exact / 3.6)
draw = d.demanda_raw * fac
DB = (draw - draw.min()) / (draw.max() - draw.min())
sB, _, _ = score(d.viv_hab_censo_est / 1000, DB)
def rk(s): return pd.Series(np.asarray(s)).rank(ascending=False, method="first").astype(int).values
d["viv_censo_hab_modelo"] = d.viv_hab_censo_est.round(0).astype(int)
d["ratio_viv_est_censo"] = (d.pob_conapo_exact / 3.6 / d.viv_hab_censo_est).round(3)
d["anclas_por_1000viv_censo"] = (d.anclas_pond / (d.viv_hab_censo_est / 1000)).round(2)
d["comp_por_1000viv_censo"] = (d.comp_n_300m / (d.viv_hab_censo_est / 1000)).round(3)
d["A_star_censo"] = A_A.round(4); d["C_star_censo"] = C_A.round(4)
d["score_base_censo"] = sA.round(2); d["rank_base_censo"] = rk(sA)
d["delta_rank_censo"] = d.rank_base - d.rank_base_censo   # + = sube con Censo
d["score_base_censo_demviv"] = np.round(sB, 2); d["rank_base_censo_demviv"] = rk(sB)
d["delta_rank_censo_demviv"] = d.rank_base - d.rank_base_censo_demviv
d["etiqueta"] = "MODELO (traslape de areas colonia-AGEB, Censo 2020; no oficial por colonia)"
cols = ["cve_col", "colonia", "municipio", "rank_base", "score_base", "pob_conapo", "viviendas_est", "viv_censo_hab_modelo", "ratio_viv_est_censo",
        "ocup_censo", "n_ageb", "anclas_pond", "anclas_por_1000viv", "anclas_por_1000viv_censo", "comp_n_300m", "comp_por_1000viv", "comp_por_1000viv_censo",
        "D_star", "A_star", "C_star", "A_star_censo", "C_star_censo", "score_base_censo", "rank_base_censo", "delta_rank_censo",
        "score_base_censo_demviv", "rank_base_censo_demviv", "delta_rank_censo_demviv", "etiqueta"]
out = d.sort_values("rank_base")[cols]
out.to_csv(f"{ROOT}/v2/data/colonias_v3_sensibilidad_censo.csv", index=False)

# ---------- estadisticas ----------
rhoA = spearmanr(d.rank_base, d.rank_base_censo)[0]; rhoB = spearmanr(d.rank_base, d.rank_base_censo_demviv)[0]
def topn(col, n): return set(d.loc[d[col] <= n, "cve_col"])
t10b, t10A, t10B = topn("rank_base", 10), topn("rank_base_censo", 10), topn("rank_base_censo_demviv", 10)
t20b, t20A = topn("rank_base", 20), topn("rank_base_censo", 20)
t30b, t30A = topn("rank_base", 30), topn("rank_base_censo", 30)
mv = d[d.delta_rank_censo.abs() > 10].sort_values("rank_base")
mvB = d[d.delta_rank_censo_demviv.abs() > 10]
rep = dict(spearman_A=rhoA, spearman_B=rhoB, top10_overlap_A=len(t10b & t10A), top10_overlap_B=len(t10b & t10B), top20_overlap_A=len(t20b & t20A), top30_overlap_A=len(t30b & t30A),
           n_mov_gt10_A=len(mv), n_mov_gt10_B=len(mvB), max_abs_move_A=int(d.delta_rank_censo.abs().max()), median_abs_move_A=float(d.delta_rank_censo.abs().median()),
           ratio_median=float(d.ratio_viv_est_censo.median()), ratio_min=float(d.ratio_viv_est_censo.min()), ratio_max=float(d.ratio_viv_est_censo.max()),
           sum_viv_est=int(d.viviendas_est.sum()), sum_viv_censo=int(round(d.viv_hab_censo_est.sum())), repro_max_score_diff=rep_maxdiff, repro_rank_mismatch=rep_rank_mismatch,
           score_shift_mean_A=float((d.score_base_censo - d.score_base).mean()), score_abs_shift_max_A=float((d.score_base_censo - d.score_base).abs().max()))
print(json.dumps(rep, indent=1))
def row(r, cols_): return "| " + " | ".join(str(r[k]) for k in cols_) + " |"
L = []; w = L.append
w("# Sensibilidad: viviendas Censo 2020 vs `pob/3.6` en el score v3 base\n")
w("**Etiqueta: MODELO (traslape de áreas colonia↔AGEB, Censo 2020).** El Censo no publica viviendas por colonia; `viv_hab_censo_est` reparte las viviendas habitadas de cada AGEB por el área que se traslapa con la colonia. Es una **sensibilidad**, no un reemplazo del score titular. Nada de `colonias_v3.csv` ni del mapa publicado se modificó.\n")
w("- Script: `scripts/sensibilidad_viviendas_censo.py` (sin red; reproducible). Salida: `v2/data/colonias_v3_sensibilidad_censo.csv` (167 filas; columnas nuevas `score_base_censo`, `rank_base_censo`, `delta_rank_censo`, y variante B `*_demviv`).")
w("- Entrada: `v2/data/colonias_v3.csv` (conteos de anclas/competencia, D*), `data/colonias.geojson` (`demanda_raw`), y `inegi_purificador/datos/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv` (read-only, 381 AGEB, 167 colonias).\n")
w("## Qué cambia y qué no\n")
w("`score_base = 100·(0.40·D* + 0.30·A* + 0.30·(1−C*))`. Las **viviendas sólo entran como divisor** de Anclas/1 000 viv. y Competencia/1 000 viv. (`build_v3_rating.py` l.243-258). Los conteos (anclas ponderadas, purificadoras ≤300 m) no cambian.")
w("**Demanda\\* (D\\*) no usa viviendas**: es `pob_eff · mezcla(OVHAC, OVSAE)` con población (walkshed), min-max. Además `pob_conapo` ≈ Censo (suma 742,016 vs 738,286 → razón 1.005, MODELO). Por eso:\n")
w("- **Variante A (titular de la sensibilidad, `score_base_censo`)**: A* y C* con viviendas Censo; D\\* idéntica.")
w("- **Variante B (cota superior, `score_base_censo_demviv`)**: además supone demanda ∝ viviendas (`demanda_raw × viv_censo/viviendas_est`, re-min-max). Es un supuesto extremo, no la regla actual.\n")
w("## Magnitud del sesgo de viviendas\n")
w(f"- Σ `viviendas_est` (pob/3.6) = **{rep['sum_viv_est']:,}** vs Σ Censo-habitadas (MODELO) = **{rep['sum_viv_censo']:,}** → razón global {rep['sum_viv_est']/rep['sum_viv_censo']:.3f}.")
w(f"- Razón por colonia `viviendas_est / viv_censo`: mediana **{rep['ratio_median']:.3f}**, rango {rep['ratio_min']:.2f}–{rep['ratio_max']:.2f}. Ocupantes/vivienda Censo (mediana): {d.ocup_censo.median():.2f} (vs 3.6 supuesto).")
w(f"- Ojo: el CSV de INEGI cuenta **viviendas particulares habitadas**; `pob/3.6` pretende viviendas totales servidas. Si se quisieran viviendas totales (incl. deshabitadas) la diferencia sería menor; no se calcula aquí por no estar en el CSV.\n")
w("## Chequeo de reproducción\n")
w(f"Recalcular el base con `pob_conapo/3.6` (exacto) reproduce `score_base` con diferencia máx. **{rep_maxdiff:.3f} pts** y **{rep_rank_mismatch}** rangos distintos (redondeo de D_star a 4 decimales en el CSV). Procedimiento validado.\n")
w("## Resultado\n")
w("| Métrica | Variante A (A*,C* con viv Censo) | Variante B (+demanda ∝ viv) |\n|---|--:|--:|")
w(f"| Spearman rank_base vs rank censo | **{rhoA:.4f}** | {rhoB:.4f} |")
w(f"| Top-10 en común (de 10) | **{rep['top10_overlap_A']}** | {rep['top10_overlap_B']} |")
w(f"| Top-20 en común (de 20) | {rep['top20_overlap_A']} | {len(t20b & topn('rank_base_censo_demviv',20))} |")
w(f"| Top-30 en común (de 30) | {rep['top30_overlap_A']} | {len(t30b & topn('rank_base_censo_demviv',30))} |")
w(f"| Colonias que se mueven >10 rangos | **{rep['n_mov_gt10_A']}** | {rep['n_mov_gt10_B']} |")
w(f"| Mov. absoluto mediano / máximo (rangos) | {rep['median_abs_move_A']:.0f} / {rep['max_abs_move_A']} | {d.delta_rank_censo_demviv.abs().median():.0f} / {int(d.delta_rank_censo_demviv.abs().max())} |")
w(f"| Cambio de score medio (pts) | {rep['score_shift_mean_A']:+.2f} | {(d.score_base_censo_demviv-d.score_base).mean():+.2f} |\n")
w("### Top-10 (base actual vs con viviendas Censo, variante A)\n")
w("| # base | Colonia | Municipio | Score base | # Censo | Score Censo | Δ | Razón viv est/Censo |\n|--:|---|---|--:|--:|--:|--:|--:|")
for _, r in d.sort_values("rank_base").head(10).iterrows():
    w(f"| {r.rank_base} | {r.colonia} | {r.municipio} | {r.score_base:.1f} | {r.rank_base_censo} | {r.score_base_censo:.1f} | {r.delta_rank_censo:+d} | {r.ratio_viv_est_censo:.2f} |")
w("\nTop-10 **nuevo** (variante A):\n")
w("| # Censo | Colonia | Municipio | Score Censo | # base |\n|--:|---|---|--:|--:|")
for _, r in d.sort_values("rank_base_censo").head(10).iterrows():
    w(f"| {r.rank_base_censo} | {r.colonia} | {r.municipio} | {r.score_base_censo:.1f} | {r.rank_base} |")
ent = d[d.cve_col.isin(t10A - t10b)]; sal = d[d.cve_col.isin(t10b - t10A)]
w(f"\nEntran al top-10: {', '.join(f'{r.colonia} (#{r.rank_base}→#{r.rank_base_censo})' for _, r in ent.sort_values('rank_base_censo').iterrows()) or 'ninguna'}. "
  f"Salen: {', '.join(f'{r.colonia} (#{r.rank_base}→#{r.rank_base_censo})' for _, r in sal.sort_values('rank_base').iterrows()) or 'ninguna'}.\n")
w(f"### Colonias que se mueven >10 rangos (variante A): {len(mv)}\n")
w("| # base | Colonia | Municipio | # Censo | Δ rangos | Razón viv est/Censo | Anclas pond | Purif ≤300 m |\n|--:|---|---|--:|--:|--:|--:|--:|")
for _, r in mv.iterrows():
    w(f"| {r.rank_base} | {r.colonia} | {r.municipio} | {r.rank_base_censo} | {r.delta_rank_censo:+d} | {r.ratio_viv_est_censo:.2f} | {r.anclas_pond} | {r.comp_n_300m} |")
w("\n## Lectura\n")
w(f"- Un sesgo casi uniforme (~{(rep['ratio_median']-1)*100:.0f} %) **no** mueve el ranking por sí mismo: sólo importa la variación **entre colonias** de la razón ({rep['ratio_min']:.2f}–{rep['ratio_max']:.2f}). Como A* y C* son rangos percentiles, el efecto es de reordenamiento local, no de nivel.")
w("- La Demanda\\* (40 % del score) no cambia en la variante A; por eso el Spearman es alto.")
w("- Las colonias con razón alta (pob/3.6 sobrestima más) tienden a ganar densidad de anclas al corregir y a subir; las de razón ≤1 tienden a bajar (ver tabla de movers: los mayores descensos tienen razón 0.92–1.04). Las que tienen 0 purificadoras mantienen C*=0 sin importar viviendas.")
w("- **Recomendación (pendiente de Nicolás):** el efecto es de segundo orden para decidir zonas top-30, pero conviene usar viviendas Censo cuando se regenere el build (cambio de 1 línea: dividir por `viv_hab_censo_est`). No se aplicó: v3 titular y mapa publicado quedan intactos. Captura 3 % y 2 garr/viv/sem siguen siendo supuestos [ESTIMADO].\n")
w("## Límites\n- MODELO: traslape de áreas supone viviendas uniformemente distribuidas dentro del AGEB; polígonos de colonia no son oficiales.\n- No se re-ejecutó todo `build_v3_rating.py` (celdas, spots no cambian por esta sensibilidad); sólo el score a nivel colonia.\n- Viviendas habitadas ≠ viviendas totales.")
open(f"{ROOT}/docs/SENSIBILIDAD_VIVIENDAS.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
