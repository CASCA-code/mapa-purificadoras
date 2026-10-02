#!/usr/bin/env python3
"""Compara ranking v2 (data/colonias.geojson, lo que muestra el hub) vs v3 base (v2/data/colonias_v3.csv) y vs colonias_v2_scored.csv (copia de caja, formula vieja).
Solo lectura de datos; escribe docs/V2_VS_V3.md y v2/data/comparacion_v2_vs_v3.csv. Sin red."""
import json, os, numpy as np, pandas as pd
from scipy.stats import spearmanr
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLDCSV = os.environ.get("V2_SCORED_CSV", "/workspace/colonias_v2_scored.csv")
g = pd.DataFrame([f["properties"] for f in json.load(open(f"{ROOT}/data/colonias.geojson"))["features"]])
v = pd.read_csv(f"{ROOT}/v2/data/colonias_v3.csv")
d = v.merge(g[["cve_col", "demanda_star", "comp_star", "anclas_star", "rank", "score_100", "comp_formal_v2", "comp_informal_v2"]], on="cve_col", validate="1:1")
assert len(d) == 167 and (d.D_star - d.demanda_star).abs().max() < 1e-3
d["pts_D"] = 40 * d.D_star
d["pts_A_v2"] = 20 * d.anclas_star; d["pts_C_v2"] = 25 * (1 - d.comp_star)
d["pts_A_v3"] = 30 * d.A_star; d["pts_C_v3"] = 30 * (1 - d.C_star)
sp = lambda a, b: spearmanr(a, b)[0]
res = {}
res["spearman_rank"] = sp(d["rank"], d.rank_base)
res["top10_common"] = sorted(set(d[d["rank"] <= 10].colonia) & set(d[d.rank_base <= 10].colonia))
res["top20_common"] = len(set(d[d["rank"] <= 20].cve_col) & set(d[d.rank_base <= 20].cve_col))
res["top30_common"] = len(set(d[d["rank"] <= 30].cve_col) & set(d[d.rank_base <= 30].cve_col))
res["v2_recompute_maxdiff"] = float((40 * d.demanda_star + 25 * (1 - d.comp_star) + 20 * d.anclas_star + 15 - d.score_100).abs().max())
# varianza efectiva de cada termino en el score (rango de score entre colonias)
def vs(t): tot = sum(x.var() for x in t); return [x.var() / tot for x in t]
res["varshare_v2"] = vs([d.pts_D, d.pts_C_v2, d.pts_A_v2]); res["varshare_v3"] = vs([d.pts_D, d.pts_C_v3, d.pts_A_v3])
res["sd_pts_v2"] = [d.pts_D.std(), d.pts_C_v2.std(), d.pts_A_v2.std()]; res["sd_pts_v3"] = [d.pts_D.std(), d.pts_C_v3.std(), d.pts_A_v3.std()]
res["sp_v2_D"] = sp(d.score_100, d.D_star); res["sp_v3_D"] = sp(d.score_base, d.D_star)
res["sp_v2_A"] = sp(d.score_100, d.anclas_star); res["sp_v2_C"] = sp(d.score_100, -d.comp_star)
res["sp_v3_A"] = sp(d.score_base, d.A_star); res["sp_v3_C"] = sp(d.score_base, -d.C_star)
res["sp_A2_A3"] = sp(d.anclas_star, d.A_star); res["sp_C2_C3"] = sp(d.comp_star, d.C_star)
res["sp_D_C2"] = sp(d.D_star, d.comp_star); res["sp_D_C3"] = sp(d.D_star, d.C_star)
# intercambio de un termino a la vez (ablacion)
b = lambda D, A, C: 100 * (.4 * D + .3 * A + .3 * (1 - C))
v2s = 40 * d.demanda_star + 25 * (1 - d.comp_star) + 20 * d.anclas_star + 15
res["abl_v2_con_A3"] = sp(d.score_100, 40 * d.demanda_star + 25 * (1 - d.comp_star) + 20 * d.A_star + 15)
res["abl_v2_con_C3"] = sp(d.score_100, 40 * d.demanda_star + 25 * (1 - d.C_star) + 20 * d.anclas_star + 15)
res["abl_v2_con_A3C3"] = sp(d.score_100, 40 * d.demanda_star + 25 * (1 - d.C_star) + 20 * d.A_star + 15)
res["abl_v3_con_A2"] = sp(d.score_base, b(d.D_star, d.anclas_star, d.C_star))
res["abl_v3_con_C2"] = sp(d.score_base, b(d.D_star, d.A_star, d.comp_star))
res["abl_v3_con_A2C2"] = sp(d.score_base, b(d.D_star, d.anclas_star, d.comp_star))
res["abl_v3_pesos_v2_mismo_A3C3"] = sp(d.score_base, 40 * d.D_star + 25 * (1 - d.C_star) + 20 * d.A_star)   # solo cambian los pesos
z = d[d.comp_n_300m == 0]
res["n_zero_v3"] = len(z); res["zero_v2_comp_median"] = float(z.comp_star.median()); res["all_v2_comp_median"] = float(d.comp_star.median())
res["zero_v2_comp_informal_median"] = float(z.comp_informal_v2.median())
res["share_C3_zero"] = float((d.C_star == 0).mean())
# Escobedo
E = d[d.municipio == "General Escobedo"]; O = d[d.municipio != "General Escobedo"]
res["esc"] = dict(n=len(E), mean_rank_v2=E["rank"].mean(), mean_rank_v3=E.rank_base.mean(), top20_v2=int((E["rank"] <= 20).sum()), top20_v3=int((E.rank_base <= 20).sum()),
                  top50_v2=int((E["rank"] <= 50).sum()), top50_v3=int((E.rank_base <= 50).sum()), viv_med=float(E.viviendas_est.median()), viv_med_otros=float(O.viviendas_est.median()),
                  D=float(E.D_star.mean()), D_o=float(O.D_star.mean()), A2=float(E.anclas_star.mean()), A2_o=float(O.anclas_star.mean()), A3=float(E.A_star.mean()), A3_o=float(O.A_star.mean()),
                  C2=float(E.comp_star.mean()), C2_o=float(O.comp_star.mean()), C3=float(E.C_star.mean()), C3_o=float(O.C_star.mean()),
                  zero=int((E.comp_n_300m == 0).sum()), adens=float(E.anclas_por_1000viv.median()), adens_o=float(O.anclas_por_1000viv.median()))
# archivo viejo vs hub
old = pd.read_csv(OLDCSV)
m = old.merge(g, on="cve_col", suffixes=("_csv", "_hub"), validate="1:1")
old_re = 40 * m.demanda_star_csv + 25 * (1 - m.comp_star_csv) + 20 * m.anclas_star_csv + 15 * (1 - m.canibal_star_csv)
hub_re = 40 * m.demanda_star_hub + 25 * (1 - m.comp_star_hub) + 20 * m.anclas_star_hub + 15 * (1 - m.canibal_star_hub)
res["old"] = dict(n_rank_differs=int((m.rank_csv != m.rank_hub).sum()), sp=sp(m.rank_csv, m.rank_hub), old_recompute=float((old_re - m.score_100_csv).abs().max()), hub_recompute=float((hub_re - m.score_100_hub).abs().max()),
                  comp_corr=sp(m.comp_star_csv, m.comp_star_hub), anclas_corr=sp(m.anclas_star_csv, m.anclas_star_hub))
cmpdf = m.sort_values("rank_hub")[["cve_col", "colonia_hub", "municipio_hub", "rank_hub", "score_100_hub", "rank_csv", "score_100_csv"]].rename(columns={"colonia_hub": "colonia", "municipio_hub": "municipio", "rank_hub": "rank_hub_geojson", "score_100_hub": "score_hub_geojson", "rank_csv": "rank_colonias_v2_scored_csv", "score_100_csv": "score_colonias_v2_scored_csv"})
d = d.merge(cmpdf[["cve_col", "rank_colonias_v2_scored_csv", "score_colonias_v2_scored_csv"]], on="cve_col")
d["delta_rank_v2hub_a_v3base"] = d["rank"] - d.rank_base
d.sort_values("rank")[["cve_col", "colonia", "municipio", "rank", "score_100", "rank_base", "score_base", "delta_rank_v2hub_a_v3base", "D_star", "anclas_star", "A_star", "comp_star", "C_star", "comp_n_300m", "anclas_por_1000viv",
    "pts_D", "pts_A_v2", "pts_C_v2", "pts_A_v3", "pts_C_v3", "rank_colonias_v2_scored_csv", "score_colonias_v2_scored_csv"]].rename(columns={"rank": "rank_v2_hub", "score_100": "score_v2_hub", "anclas_star": "A_star_v2", "comp_star": "C_star_v2", "A_star": "A_star_v3", "C_star": "C_star_v3"}).round(3).to_csv(f"{ROOT}/v2/data/comparacion_v2_vs_v3.csv", index=False)
print(json.dumps(res, indent=1, default=float, ensure_ascii=False))

L = []; w = L.append
f2 = lambda x: f"{x:.2f}"; pc = lambda x: f"{100*x:.0f} %"
w("# v2 vs v3 base: por qué los rankings no coinciden (y cuál rige)\n")
w("Todo sale de `data/colonias.geojson` (lo que lee el hub), `v2/data/colonias_v3.csv` y `/workspace/colonias_v2_scored.csv`. Script reproducible: `scripts/analisis_v2_vs_v3.py` (sin red). Tabla por colonia: `v2/data/comparacion_v2_vs_v3.csv` (167 filas). No se tocó ningún ranking ni `index.html`.\n")
w("## 1. Resumen\n")
w(f"- Spearman rank v2 (hub) vs rank v3 base = **{res['spearman_rank']:.3f}**; top-10 en común: **{len(res['top10_common'])}** ({', '.join(res['top10_common'])}); top-20: {res['top20_common']}; top-30: {res['top30_common']}.")
w(f"- **Demanda\\* es idéntica** en ambos (dif. máx. {(d.D_star-d.demanda_star).abs().max():.4f}) → no es la causa. La diferencia viene de **Anclas\\*, Competencia\\* y del peso efectivo** de cada término.")
w(f"- Pesos nominales v2 40/25/20(+15 constante) vs v3 40/30/30 parecen cercanos, pero el **peso efectivo** (parte de la varianza del score entre colonias) cambia mucho: ver §2.")
w("- **Signo de competencia: igual** en ambos (más competidores = menos puntos; `1−Comp*`). No es un error de signo. Lo que cambia es *qué* mide Comp\\* y cómo trata el 0 (§3).")
w("- Escobedo cae porque sus colonias son grandes (anclas/1 000 viv. diluidas) y v2 premiaba su demanda (§5).\n")
w("## 2. Peso efectivo de cada término (el motivo principal)\n")
w("v2: cada término es min-max sobre su valor crudo; Anclas\\* v2 está muy sesgada a 0 (mediana 0, media 0.09) y Comp\\* v2 tiene dispersión chica (sd 0.15). v3: Anclas\\* y Comp\\* son **rangos percentiles** (distribución uniforme 0–1, sd ≈0.29–0.36) → pesan mucho más aunque el peso nominal sea parecido.\n")
w("| Término | Puntos v2: sd | Parte de la varianza v2 | Puntos v3: sd | Parte de la varianza v3 |\n|---|--:|--:|--:|--:|")
for i, nm in enumerate(["Demanda (40 pts, igual)", "Competencia", "Anclas"]):
    w(f"| {nm} | {res['sd_pts_v2'][i]:.2f} | **{pc(res['varshare_v2'][i])}** | {res['sd_pts_v3'][i]:.2f} | **{pc(res['varshare_v3'][i])}** |")
w(f"\n- v2 es esencialmente un ranking de **demanda** (Spearman score v2 vs D\\* = **{res['sp_v2_D']:.2f}**). v3 base casi no lo es (score v3 vs D\\* = **{res['sp_v3_D']:.2f}**); lo mueve más la competencia (Spearman con (1−C\\*) = {-res['sp_v3_C']:.2f}).")
w(f"- Anclas v2 vs v3 correlacionan poco (Spearman **{res['sp_A2_A3']:.2f}**): v2 = suma ponderada ≤250 m del **centroide** con decaimiento (jardines, iglesias, hospital, universidad…); v3 = conteo ponderado en polígono+100 m **por 1 000 viv.** (cerveza, tortillería, Oxxo, bancos, paradas…). Son dos definiciones distintas de «ancla».")
w(f"- Competencia v2 vs v3: Spearman **{res['sp_C2_C3']:.2f}**. v2 = DENUE formal con decaimiento ~400 m + **proxy informal 1.0/1 000 viv.** (constante por vivienda); v3 = conteo ≤300 m del polígono por 1 000 viv., percentil.\n")
w("### Ablación: cambiar un término a la vez (Spearman del score resultante contra el original)\n")
w("| Experimento | Spearman |\n|---|--:|")
w(f"| v2 con Anclas\\* de v3 | {res['abl_v2_con_A3']:.2f} |\n| v2 con Comp\\* de v3 | {res['abl_v2_con_C3']:.2f} |\n| v2 con Anclas\\* y Comp\\* de v3 (pesos v2) | {res['abl_v2_con_A3C3']:.2f} |")
w(f"| v3 con Anclas\\* de v2 | {res['abl_v3_con_A2']:.2f} |\n| v3 con Comp\\* de v2 | {res['abl_v3_con_C2']:.2f} |\n| v3 con Anclas\\* y Comp\\* de v2 (pesos v3) | {res['abl_v3_con_A2C2']:.2f} |")
w(f"| v3 con los **términos v3** pero **pesos v2** (40/25/20) | {res['abl_v3_pesos_v2_mismo_A3C3']:.2f} |")
w(f"\nLectura: (1) los **pesos nominales casi no importan**: con términos v3 y pesos v2 la correlación con v3 es {res['abl_v3_pesos_v2_mismo_A3C3']:.2f}. (2) Lo que cambia el ranking es **cómo se define y escala Anclas\\* y Comp\\***: cambiar Comp\\* pesa más que cambiar Anclas\\* (v3 con Comp\\* v2 → {res['abl_v3_con_C2']:.2f}; con Anclas\\* v2 → {res['abl_v3_con_A2']:.2f}); cambiar ambos → {res['abl_v3_con_A2C2']:.2f}, es decir, casi todo el 0.34 de Spearman se explica por esos dos términos.\n")
w("## 3. Competencia: signo y el «0»\n")
w(f"- Mismo signo: en ambos, más competencia resta puntos. Verificado recalculando v2 = 40·D\\*+25·(1−Comp\\*)+20·Anclas\\*+15 contra `score_100` (dif. máx. {res['v2_recompute_maxdiff']:.3f}).")
w(f"- En v3, **{res['n_zero_v3']} colonias ({100*res['n_zero_v3']/167:.0f} %) tienen 0 purificadoras detectadas ≤300 m** y reciben Comp\\*=0 → los 30 pts completos. En v2 esas mismas colonias **no** tienen competencia cero: Comp\\* v2 mediana **{res['zero_v2_comp_median']:.2f}** (todas: {res['all_v2_comp_median']:.2f}) porque v2 siempre suma el proxy informal (mediana {res['zero_v2_comp_informal_median']:.2f}).")
w("- Consecuencia: v3 premia la **ausencia de datos** de competencia (DENUE/Places no ven informales; ver `docs/COMPETENCIA_CERO.md`). Eso explica los saltos grandes (Ampliación Municipal #73→#1, Floridos Bosques del Nogalar #161→#9: ambos con 0 competidores).")
w(f"- Además, v2 Comp\\* correlaciona **positivo** con Demanda\\* (Spearman {res['sp_D_C2']:.2f}: más gente ⇒ más competencia estimada), así que v2 se compensa a sí mismo; en v3 la correlación es {res['sp_D_C3']:.2f} (no se compensa).\n")
w("## 4. Top-20 de cada ranking\n")
def tab(df, key):
    w("| # v2 | # v3 | Colonia | Municipio | D* | Anclas* v2 | Anclas* v3 | Comp* v2 | Comp* v3 | Purif ≤300 m | Score v2 | Score v3 |\n|--:|--:|---|---|--:|--:|--:|--:|--:|--:|--:|--:|")
    for _, r in df.sort_values(key).head(20).iterrows():
        w(f"| {r['rank']} | {r.rank_base} | {r.colonia} | {r.municipio} | {r.D_star:.2f} | {r.anclas_star:.2f} | {r.A_star:.2f} | {r.comp_star:.2f} | {r.C_star:.2f} | {r.comp_n_300m} | {r.score_100:.1f} | {r.score_base:.1f} |")
w("### Top-20 v2 (hub)\n"); tab(d, "rank")
w("\n### Top-20 v3 base\n"); tab(d, "rank_base")
w("\nCada fila lleva los dos rangos y los componentes para ver qué término la mueve. Columnas completas (167 colonias, puntos por término): `v2/data/comparacion_v2_vs_v3.csv`.\n")
e = res["esc"]
w("## 5. Por qué cae General Escobedo\n")
w("| Indicador | Escobedo (26) | Resto (141) |\n|---|--:|--:|")
w(f"| Colonias en top-20 v2 → v3 | {e['top20_v2']} → **{e['top20_v3']}** | — |\n| Colonias en top-50 v2 → v3 | {e['top50_v2']} → {e['top50_v3']} | — |\n| Rango medio v2 → v3 | {e['mean_rank_v2']:.0f} → {e['mean_rank_v3']:.0f} | — |")
w(f"| Demanda\\* media | {e['D']:.2f} | {e['D_o']:.2f} |\n| Anclas\\* v2 media | {e['A2']:.2f} | {e['A2_o']:.2f} |\n| Anclas\\* v3 media | {e['A3']:.2f} | {e['A3_o']:.2f} |\n| Comp\\* v2 media | {e['C2']:.2f} | {e['C2_o']:.2f} |\n| Comp\\* v3 media | {e['C3']:.2f} | {e['C3_o']:.2f} |")
w(f"| Viviendas est. (mediana) | {e['viv_med']:.0f} | {e['viv_med_otros']:.0f} |\n| Anclas ponderadas/1 000 viv. (mediana) | {e['adens']:.1f} | {e['adens_o']:.1f} |\n| Colonias con 0 purificadoras ≤300 m | {e['zero']} de 26 | {res['n_zero_v3']-e['zero']} de 141 |")
w("\n- Escobedo tiene **mayor demanda** (0.34 vs 0.28) y **menos competencia v2** (0.20 vs 0.27) → v2 lo favorece (peso efectivo de demanda 69 %).")
w("- En v3 el peso se traslada a Anclas/1 000 viv. y Comp/1 000 viv.: sus colonias son **más grandes** (más viviendas) → la densidad de anclas baja (Anclas\\* v3 0.39 vs 0.52), la competencia ya no las distingue (Comp\\* v3 0.45 vs 0.44, antes 0.20 vs 0.27 en v2) y la ventaja de demanda pesa 22 %, no 69 %.")
w("- La caída es por **método**, no por evidencia de campo nueva. El Scout apoya a Escobedo en las colonias encuestadas: San Miguel Residencial (22 marcas) sigue #3–#4 en v3 base/con Scout.\n")
w("## 6. Hub vs `colonias_v2_scored.csv` (#5/#18 vs #8/#19)\n")
o = res["old"]
w(f"- **El hub muestra el rank de `data/colonias.geojson`** (`p.rank`, `index.html` l.2045/2146; la lista se ordena por `score_100` del mismo archivo). Ahí: Villas de San Francisco **#5**, La Unidad **#18**, San Bernabé 1er Sector #19, Riveras del Río #4.")
w(f"- `/workspace/colonias_v2_scored.csv` (idéntico a `/home/box/purificadoras/workspace/colonias_v2_scored.csv`, md5 d7fe8f6f…) da Villas **#8**, La Unidad **#19**, San Bernabé #24, Riveras #6; rank distinto en **{o['n_rank_differs']} de 167** colonias (Spearman {o['sp']:.3f}); Croc 81.6 (#2) vs hub 76.5 (#1); San Gilberto #1 (82.69) vs hub #2 (74.53).")
w(f"- Causa (evidencia): el CSV es de la **fórmula anterior** al update del 2026-09-12 (nota `version2_formula_update_nota.md`: Comp\\* = formal + informal 1.0/1 000 viv.; pesos de anclas nuevos). Sus columnas `comp_star`/`anclas_star` difieren de las del hub (Spearman comp {o['comp_corr']:.2f}, anclas {o['anclas_corr']:.2f}); recalculado con sus propios componentes cada archivo es auto-consistente (dif. máx. CSV {o['old_recompute']:.2f}, hub {o['hub_recompute']:.2f}). No es un bug del hub: **el CSV de la caja está desactualizado** (el de OneDrive en la PC de Nicolás es el regenerado, según esa nota; no accesible desde la caja).")
w("- **Qué lee la rutina diaria:** la automatización `reporte-diario-purificadoras` (cron 08:18 CDMX) **no nombra ningún archivo de ranking**; su prompt dice «mapa/repo CASCA-code/mapa-purificadoras y site https://casca-code.github.io/mapa-purificadoras/» → en la práctica `data/colonias.geojson` / hub (top-5 Croc 76.5 · San Gilberto 74.5 · San Miguel Residencial 71.7 · Riveras 67.6 · Villas 66.1, coincide con el hub). La receta A de `purif-sitios` manda comparar contra `colonias_v2_scored.csv` de la caja: **esa comparación produce el falso «el hub miente»**. Recomendación: no usar el CSV de la caja como referencia hasta regenerarlo/sincronizarlo con la PC [pendiente de Nicolás/Sitios]. (No se pudo leer el texto de ejecuciones pasadas del reporte; sólo su prompt.)")
w("- El rank del hub y `v2_rank` en `colonias_v3.csv` son el mismo (`data/colonias.geojson`).\n")
w("## 7. Recomendación (PENDIENTE DE NICOLÁS — no es decisión tomada)\n")
w("1. **ZMM completo (lista larga / dónde mirar primero): v3 base** como filtro, porque tiene cobertura uniforme (DENUE+Places+OSM), anclas por vivienda y celdas de 100 m, **pero** tratando las 58 colonias con 0 competidores como *no verificadas* hasta confirmar en campo (§3).")
w("2. **Foco de campo en Escobedo: mantener v2 / estudio** (San Miguel Residencial, Villas de San Francisco, Alianza Real): es el criterio de Purificador vigente (demanda D+/D) y v3 las baja por método, no por evidencia. San Miguel Residencial está en el top-4 de ambos rankings (#3 v2, #3 v3).")
w("3. Colonias en **ambos** top-30 son las más robustas (ver CSV `comparacion_v2_vs_v3.csv`, filtrar `rank_v2_hub<=30` y `rank_base<=30`): " + ", ".join(sorted(d[(d["rank"] <= 30) & (d.rank_base <= 30)].colonia)) + ".")
w("4. Antes de formalizar cualquiera: calibrar con 10–15 conteos de esquina y ventas reales (pesos son de juicio).")
w("5. Si se quiere un solo ranking, probar v3 con Comp\\* que no regale puntos máximos al 0 (p. ej. piso mediano para colonias sin Scout) — **sólo como propuesta, no implementada**.\n")
open(f"{ROOT}/docs/V2_VS_V3.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
