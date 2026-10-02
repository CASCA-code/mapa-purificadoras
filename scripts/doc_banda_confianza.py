#!/usr/bin/env python3
"""Genera docs/BANDA_CONFIANZA.md a partir de v2/data/colonias_v3_banda_confianza.csv y colonias_v3_sensibilidad_densidad.csv (+ stats json). Sin red."""
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open("/workspace/downloads/banda_confianza_stats.json"))
B = pd.read_csv(f"{ROOT}/v2/data/colonias_v3_banda_confianza.csv")
X = pd.read_csv(f"{ROOT}/v2/data/colonias_v3_sensibilidad_densidad.csv")
nm = dict(zip(X.cve_col, X.colonia)); rb = dict(zip(X.cve_col, X.rank_base))
L = []; w = L.append
w("# Sensibilidad de densidad de viviendas + banda de confianza del ranking v3 base\n")
w("**Etiqueta: MODELO.** Es un análisis de sensibilidad del ranking, **no un pronóstico** ni un intervalo estadístico: los rangos p10–p90 sólo dicen cuánto se mueve una colonia si cambian los supuestos listados. No altera `colonias_v3.csv`, el hub ni el mapa. Fecha: 2026-10-02.\n")
w("- Scripts: `scripts/banda_confianza_densidad.py` (cálculo, semilla fija, sin red) y `scripts/doc_banda_confianza.py` (este documento).")
w("- Salidas nuevas: `v2/data/colonias_v3_sensibilidad_densidad.csv` (167 filas) y `v2/data/colonias_v3_banda_confianza.csv` (167 filas).")
w(f"- Entradas (sólo lectura): `v2/data/colonias_v3.csv`, `data/colonias.geojson` (pob exacta), `/home/box/geo/inegi_purificador/datos/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv` (viviendas habitadas Censo 2020 por traslape de área colonia–AGEB, MODELO), `…/colonias167_conapo_geom.geojson` (`area_km2` del polígono CONAPO).")
w(f"- Reproducción del base con `pob/3.6`: dif. máx. de score {S['repro']['max_dif']:.3f} pts y {S['repro']['rangos_distintos']} rangos distintos (procedimiento validado).\n")
w("## 1. Variante `score_base_dens`: término de densidad de viviendas\n")
w("`Dens*` = rango percentil (0–1, misma convención que A* y C*) de **viviendas habitadas Censo por hectárea** = `viv_hab_censo_est / (area_km2·100)`. Se añade con peso `w`:\n")
w("```text\nscore_dens = 100·( wD'·D* + wA'·A* + 0.30·(1−C*) + w·Dens* )\nmodo DA (principal): w sale de Demanda y Anclas en proporción a su peso:  wD' = 0.40 − w·0.40/0.70 ,  wA' = 0.30 − w·0.30/0.70 ;  Competencia queda en 0.30\nmodo ALL (robustez): w sale de los tres componentes en proporción (×(1−w))\n```\n")
w("A* y C* siguen con `pob/3.6` (idénticos al base); sólo cambia el término nuevo y el reparto de pesos.\n")
w("| Modo | w dens | pesos D′/A′/C′ | Spearman score | Spearman rango | Top-10 en común | Top-30 en común | Colonias que se mueven >10 rangos | Mov. mediano / máx. (rangos) |\n|---|--:|---|--:|--:|--:|--:|--:|--:|")
for k, r in S["dens"].items():
    w(f"| {r['modo']} | {r['w_dens']:.2f} | {r['w_D']:.3f}/{r['w_A']:.3f}/{r['w_C']:.3f} | {r['spearman_score']:.3f} | {r['spearman_rank']:.3f} | {r['top10_comun']}/10 | {r['top30_comun']}/30 | {r['mov_gt10']} | {r['mov_mediano']:.0f} / {r['mov_max']} |")
w(f"\nContexto: la densidad casi no se parece al score base (Spearman densidad vs `score_base` = {S['spearman_dens_vs_score']:.2f}); por eso un peso alto reordena mucho. Spearman bajo = la densidad *cambia* el ranking, no que sea «mejor» o «peor»: sin ventas reales no hay criterio para decir que más densidad = más recarga (SUPUESTO).\n")
for key in ("DA_10", "DA_20"):
    r = S["dens"][key]; col = f"rank_dens_{key}"
    w(f"### Top-10 con w={r['w_dens']:.2f} (modo DA): entran / salen\n")
    w("| Rango dens | Colonia | Rango base | Score dens | Viv/ha |\n|--:|---|--:|--:|--:|")
    for _, x in X.sort_values(col).head(10).iterrows():
        w(f"| {x[col]} | {x.colonia} ({x.municipio}) | {x.rank_base} | {x['score_dens_'+key]:.1f} | {x.viv_ha_censo:.1f} |")
    w("\n- Entran: " + (", ".join(f"{nm[c]} (#{rb[c]}→#{int(X.loc[X.cve_col==c, col].iloc[0])})" for c in r["entran10"]) or "ninguna") + ".")
    w("- Salen: " + (", ".join(f"{nm[c]} (#{rb[c]}→#{int(X.loc[X.cve_col==c, col].iloc[0])})" for c in r["salen10"]) or "ninguna") + ".\n")
w("**Lectura (MODELO):** con w=0.05 el ranking casi no cambia (9/10 top-10); con 0.10 ya sale Croc del top-10 (#4→#12; su densidad está en el percentil ~0.30 de las 167, ver `docs/GAPS_RATING_DENSIDAD.md`), y con 0.20 el top-10 se queda con 5 de 10. Es decir, el top-10 del base **no es robusto a que Nicolás decida que la densidad importa**; el top-30 sí aguanta w≤0.10 (27/30). No se recomienda aplicar nada sin dato de ventas: ver `docs/GAPS_RATING_DENSIDAD.md` (no se repite aquí).\n")
w("## 2. Banda de confianza por colonia (Monte-Carlo de sensibilidad)\n")
w(f"**Método.** {S['ndraw']:,} sorteos (semilla {S['seed']}); en cada sorteo se recalcula el `score_base` de las 167 colonias y su rango (1 = mejor) con estas perturbaciones independientes:\n")
w("1. **Pesos** (0.40/0.30/0.30): cada uno × U(0.7, 1.3) y se renormaliza a suma 1 (±30 %).")
w("2. **Viviendas**: por colonia, `viv = viv_Censo + u·(viv_pob/3.6 − viv_Censo)`, u~U(0,1) (cubre el rango entre las dos estimaciones; afecta A* y C*, que van por 1 000 viv.).")
w("3. **Competencia = 0 tratada como desconocida** (58 colonias): su tasa de competidores/1 000 viv. se sortea de la distribución empírica de las tasas observadas en las 167 colonias (incluye ceros, SUPUESTO de que un 0 puede ser real o hueco de datos; ver `docs/COMPETENCIA_CERO.md`). Las colonias con ≥1 competidor no se perturban.")
w("- Salida por colonia: `rank_p10`, `rank_p50`, `rank_p90`, `ancho_banda = p90−p10`, `prob_top10`, `prob_top30` (fracción de sorteos). Columnas `*_estres`: misma simulación pero la tasa de los ceros se sortea sólo entre colonias con ≥1 competidor (supuesto más duro: «el 0 siempre es hueco»).")
w("- **Etiqueta `confianza`** (reglas fijas, definidas antes de ver resultados por colonia): banda **estrecha** ancho ≤30 rangos (2 pts), **media** 31–60 (1 pt), **ancha** >60 (0 pts); se resta 1 pt si **no hay ninguna marca Scout** en la colonia (`cobertura_campo = sin encuesta`). 2 pts = **alta**, 1 = **media**, 0 = **baja**. Los umbrales 30/60 son de juicio (~18 % y ~36 % de las 167 colonias), no estadísticos.\n")
w("### Resultado\n")
a = S["ancho"]; cf = S["confianza"]; bd = S["banda"]
w(f"- Ancho p90−p10: mediana **{a['mediana']:.0f}** rangos, media {a['media']:.0f}, rango {a['min']}–{a['max']}. Bandas: estrecha {bd.get('estrecha',0)}, media {bd.get('media',0)}, ancha {bd.get('ancha',0)}.")
w(f"- Confianza: **alta {cf.get('alta',0)}**, media {cf.get('media',0)}, **baja {cf.get('baja',0)}** (de 167). Alta exige banda estrecha **y** al menos 1 marca Scout; Scout cubre sólo 17 de 167 colonias, por eso casi todas caen en media/baja por cobertura, no sólo por sensibilidad.")
z0 = B[B.comp_cero_desconocido]; z1 = B[~B.comp_cero_desconocido]
w(f"- **Los 58 ceros de competencia dominan la incertidumbre:** ancho medio {z0.ancho_banda.mean():.0f} rangos (mediana {z0.ancho_banda.median():.0f}) en las 58 vs {z1.ancho_banda.mean():.0f} (mediana {z1.ancho_banda.median():.0f}) en las otras 109.")
fu = S["fuentes_ancho"]
w("- Qué fuente aporta más ancho (mismos sorteos, sólo una perturbación a la vez; ancho p90−p10 por colonia):\n")
w("| Perturbación activa | Ancho mediano | Ancho medio | Ancho máx. |\n|---|--:|--:|--:|")
for k, lab in (("solo_pesos", "sólo pesos ±30 %"), ("solo_viviendas", "sólo viviendas (Censo↔pob/3.6)"), ("solo_competencia_cero", "sólo competencia 0 = desconocida"), ("todo", "las tres")):
    w(f"| {lab} | {fu[k]['ancho_mediano']:.0f} | {fu[k]['ancho_medio']:.0f} | {fu[k]['ancho_max']:.0f} |")
w("\nLas viviendas (Censo vs pob/3.6) son la fuente menor; pesos pesan más; el 0 de competencia es la mayor (media 39, máx. 120 rangos; sólo afecta a las 58 colonias con 0).\n")
t = B[B.rank_base <= 30]
w(f"### Top-30 del base: banda y confianza ({(t.confianza=='alta').sum()} alta · {(t.confianza=='media').sum()} media · {(t.confianza=='baja').sum()} baja)\n")
w("| Rango base | Colonia | Municipio | p10 | p50 | p90 | P(top-30) | P(top-30) estrés | Competidores ≤300 m | Marcas Scout | Confianza |\n|--:|---|---|--:|--:|--:|--:|--:|--:|--:|---|")
for _, x in t.iterrows():
    w(f"| {x.rank_base} | {x.colonia} | {x.municipio} | {x.rank_p10} | {x.rank_p50} | {x.rank_p90} | {x.prob_top30:.2f} | {x.prob_top30_estres:.2f} | {x.comp_n_300m} | {x.scout_marks} | {x.confianza} |")
w("\n### Colonias con confianza alta (8)\n")
w("«Alta» = el **rango es estable** bajo estos supuestos y hay algo de campo; **no** significa que la colonia sea buena (p. ej. Fomerrey 113 es estable en el rango ~93–122).\n")
w("| Rango base | Colonia | Municipio | p10–p90 | Marcas Scout | Competidores ≤300 m |\n|--:|---|---|---|--:|--:|")
for _, x in B[B.confianza == "alta"].iterrows():
    w(f"| {x.rank_base} | {x.colonia} | {x.municipio} | {x.rank_p10}–{x.rank_p90} | {x.scout_marks} | {x.comp_n_300m} |")
w("\n### Top-12 por mediana de rango (p50) bajo los supuestos\n")
w("| p50 | Colonia | Municipio | Rango base | p10–p90 | Competidores ≤300 m | Marcas Scout | Confianza |\n|--:|---|---|--:|---|--:|--:|---|")
for _, x in B.sort_values(["rank_p50", "rank_base"]).head(12).iterrows():
    w(f"| {x.rank_p50} | {x.colonia} | {x.municipio} | {x.rank_base} | {x.rank_p10}–{x.rank_p90} | {x.comp_n_300m} | {x.scout_marks} | {x.confianza} |")
w("\nLectura: si los ceros de competencia son inciertos, suben las colonias que ya tienen ≥1 competidor *medido* y buen resto de componentes (Croc, San Bernabe 1er Sector, Alianza Real, Topo Chico…); las del top-10 base con 0 competidores bajan en la mediana pero conservan p10 alto (pueden seguir siendo top si el 0 es real). MODELO; no es veredicto.")
w("\n## 3. Lectura y límites\n")
n_top10_lo = int(((B.rank_base <= 10) & (B.confianza == "baja")).sum())
w(f"- De los 10 primeros del base, **{n_top10_lo}** tienen confianza **baja**: están arriba justamente por tener 0 competidores detectados (Comp\\*=0 → 30 pts). Si ese 0 fuera un hueco de datos, bajo estos supuestos su p90 llega a los rangos ~50–90. Sólo Croc (#4, 88 marcas Scout, 3 competidores ≤300 m) es sólido: p10–p90 = 1–2.")
w("- Esto **refuerza** lo ya dicho en `docs/COMPETENCIA_CERO.md` y `docs/V2_VS_V3.md`: el top del v3 base es un filtro para decidir dónde mirar, no un orden fino. Sirve para priorizar visitas Scout (mayor ancho × mejor p50 = más valor de verificar), no para elegir sitio.")
w("- `prob_*` es la fracción de sorteos bajo estos supuestos, **no una probabilidad de éxito comercial**. Captura 3 % y 2 garr/viv/sem siguen siendo supuestos aparte.")
w("- No se perturbaron: anclas ponderadas, pesos por categoría de ancla, Demanda\\* (CONAPO/IMC), ni la geometría (traslape colonia–AGEB, buffers 100/300 m). La banda real es por tanto un **piso**.")
w("- Rangos p10/p50/p90 se redondean a entero; el rango base usa desempate estable por fila.")
open(f"{ROOT}/docs/BANDA_CONFIANZA.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
