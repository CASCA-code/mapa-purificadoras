#!/usr/bin/env python3
"""docs/DENUE_AGUA_VS_COMPETENCIA.md desde v2/data/denue_agua_vs_competencia.csv + /workspace/downloads/denue_agua_*.{json,csv}. Sin red."""
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open("/workspace/downloads/denue_agua_stats.json"))
R = pd.read_csv(f"{ROOT}/v2/data/denue_agua_vs_competencia.csv")
P = pd.read_csv("/workspace/downloads/denue_agua_puntos_detalle.csv")
L = []; w = L.append
w("# DENUE 05_2026: agua / purificadoras vs `competencia_v3` por colonia\n")
w("Fecha: **2026-10-02**. VERIFICADO = conteo reproducible en el archivo citado; SUPUESTO = inferencia. **No altera ningún score** (`colonias_v3.csv` intacto). Script: `scripts/analisis_denue_agua_vs_competencia.py` (sin red) + `scripts/doc_denue_agua.py`. Tabla: `v2/data/denue_agua_vs_competencia.csv` (167 filas).\n")
w("## 1. Fuente y filtros\n")
w("- Archivo local: `/home/box/geo/inegi_purificador/enlaces/denue_NL_2026-05_118MB.csv` (DENUE bulk NL, 211,349 filas; metadatos «DENUE 05_2026», mod. 2026-05-20, `fecha_alta` máx. 2026-04; ver `…/datos/denue_metadatos.txt`). Recorte a bbox ZMM lat 25.52..25.92, lon −100.70..−100.00 → 186,183 filas.")
w("- **Grupo A — SCIAN 312112** «Purificación y embotellado de agua»: **%d** establecimientos en el bbox (VERIFICADO). Personal: 0–5 p.: 68 · 6–10: 8 · 11–30: 5 · 31–50: 3 · 51+: 5. **Los 89 ya están en `data/compet.geojson`** (93 puntos; 4 más son de ese archivo sin pareja en el bulk dentro del bbox) → de ahí 75 puntos DENUE en `competencia_v3` tras los filtros de marcas/plantas de v3 (VERIFICADO: replicar `denue_ok` da 75 = los 75 `s=denue` de `competencia_v3.geojson`)." % S["n_bbox_312112"])
w("- **Grupo B — otros SCIAN con nombre de agua** (SCIAN 461213 bebidas/hielo, 431211 mayoreo bebidas, 461110, 462112, 461190, 312113): filtro sobre `nom_estab` con `purificad|garraf|recarga|agua purificada|agua pura|venta de agua|expendio de agua|despachadora|agua y hielo|aquaclyva`, descartando fritura/botana/fresca/nieve/paleta/CEDIS/Oxxo/7-Eleven/«Aguacate», etc. **%d** puntos. No se usa 464 (en DENUE es farmacia/óptica/ortopedia, 0 relevantes) ni 461110 genérico: «agua» en el nombre de abarrotes casi siempre es topónimo (Agua Fría, Ojo de Agua, Aguanaval). **SUPUESTO:** que el nombre implica recarga/venta de agua; un «Venta de agua» puede ser aguas frescas." % S["n_B"])
w("- Se excluyen a propósito 221312/221311 (organismos de agua: SADM/pozos, **no competidores**), 813210, lavanderías, etc.")
w("- Conteo por colonia = puntos en **polígono + 300 m** (misma regla y misma proyección que `build_v3_rating.py`). Chequeo: el conteo de `competencia_v3.geojson` en esa regla **reproduce `comp_n_300m` en las 167 colonias** (aserción en el script).\n")
w("## 2. Resultado\n")
w(f"- DENUE agua (A+B) en polígono+300 m suma {S['sum_denue_agua']} (con dobles conteos entre colonias vecinas) frente a {S['sum_v3']} de `competencia_v3` (v3 tiene 541 puntos únicos: 466 Places + 75 DENUE): la mayor parte de la competencia detectada por v3 **no** viene de DENUE. Colonias con ≥1 punto DENUE-agua: {(R.n_denue_agua_total>0).sum()} de 167; con ≥1 en v3: {(R.comp_n_v3_total>0).sum()}.")
w(f"- Colonias con **DENUE < v3**: {S['dens_menos']} (esperado: v3 suma Places) · igual: {S['dens_igual']} · **DENUE > v3**: {S['dens_mas']}.")
w(f"- **Los 89 de SCIAN 312112 no aportan nada nuevo a v3:** 0 candidatos «nuevos» (>30 m de cualquier punto de v3 y no excluidos por la regla de v3). Las únicas diferencias A-vs-v3-DENUE son 3 colonias con plantas/embotelladoras que v3 excluye a propósito (ver abajo).")
w(f"- **Grupo B aporta {S['B_nuevo']} puntos que v3 no tiene** (SUPUESTO por nombre; ≤10 personas; >30 m de cualquier punto v3), repartidos en **{S['colonias_con_nuevo']} colonias** de las 167 (los demás caen fuera del universo). **Ninguna de las 58 colonias con 0 competidores sale del cero** por DENUE: {S['ceros_con_algun_denue']} de las 58 tienen algún punto DENUE-agua ≤300 m, pero los 3 son plantas/empresas que v3 excluye (Intermex Apodaca, Pimsa Sur, y «Corporativo de Agua Purificada Gardel», 31–50 personas, en Miguel Hidalgo).\n")
w("### Colonias donde DENUE aporta puntos que v3 no tiene (4)\n")
w("| Rango base | Colonia | Municipio | DENUE nuevo (SUPUESTO por nombre) | SCIAN | Comp. v3 ≤300 m | Δ si se sumara |\n|--:|---|---|---|---|--:|--:|")
nu = P[P.nuevo_vs_v3]
for _, x in R[R.n_denue_nuevo_vs_v3 > 0].iterrows():
    nn = x.nuevos_nombres
    sc = ", ".join(sorted(set(str(int(c)) for c, n in zip(nu.codigo_act, nu.nom) if n.title()[:40] in str(nn))))
    w(f"| {x.rank_base} | {x.colonia} | {x.municipio} | {nn} | {sc} | {x.comp_n_v3_total} | +{x.n_denue_nuevo_vs_v3} |")
w("\nEfecto de sumarlos al conteo (simulado, no aplicado; VERIFICADO recalculando el base con +1 en esas 4 colonias): 53 colonias cambian de rango por reacomodo de percentiles, máx. 10 posiciones; el top-29 no cambia y sólo se intercambian #30 (Rene Alvarez) y #31 (Fomerrey 1 Reforma). Ningún cero cambia. Las 4 colonias están en rangos base 65, 87, 155, 158.\n")
w("### Otras diferencias DENUE ≠ v3 en SCIAN 312112 (plantas excluidas por v3)\n")
w("| Rango base | Colonia | 312112 en DENUE | de ellos no excluidos por v3 | DENUE en v3 |\n|--:|---|--:|--:|--:|")
for _, x in R[R.n_312112_total != R.n_v3_denue].iterrows():
    w(f"| {x.rank_base} | {x.colonia} | {x.n_312112_total} | {x.n_312112_no_excluido_v3} | {x.n_v3_denue} |")
w("\n### Colonias donde DENUE > v3 (conteo bruto)\n")
w("| Rango base | Colonia | DENUE agua (A+B) | v3 total | Motivo |\n|--:|---|--:|--:|---|")
mot = {"Miguel Hidalgo": "empresa 31–50 pers. (B, excluida por tamaño)", "Parque Industrial Intermex Industrial Campus Apodaca": "planta/industrial excluida por v3", "Agropecuaria Emiliano Zapata (Col Nueva Esperanza)": "plantas excluidas por v3", "Pimsa Sur": "planta/industrial excluida por v3", "Bella Vista": "Frreeling Purificadora (B) nuevo"}
for _, x in R[R.delta_denue_agua_vs_v3total > 0].iterrows():
    w(f"| {x.rank_base} | {x.colonia} | {x.n_denue_agua_total} | {x.comp_n_v3_total} | {mot.get(x.colonia, '')} |")
w("\n### Colonias donde DENUE < v3 con mayor diferencia (top 12; la diferencia son puntos de Places)\n")
w("| Rango base | Colonia | Municipio | DENUE agua | v3 DENUE | v3 Places | v3 total | Δ |\n|--:|---|---|--:|--:|--:|--:|--:|")
for _, x in R.sort_values(["delta_denue_agua_vs_v3total", "rank_base"]).head(12).iterrows():
    w(f"| {x.rank_base} | {x.colonia} | {x.municipio} | {x.n_denue_agua_total} | {x.n_v3_denue} | {x.n_v3_places} | {x.comp_n_v3_total} | {x.delta_denue_agua_vs_v3total} |")
w("\nColumnas completas (167 colonias): `v2/data/denue_agua_vs_competencia.csv`; detalle por punto DENUE (nombre, SCIAN, distancia al punto v3 más cercano): `/workspace/downloads/denue_agua_puntos_detalle.csv` (fuera del repo).\n")
w("## 3. Lectura\n")
w("- **VERIFICADO:** DENUE formal ya estaba integrado completo en v3; releerlo del bulk 05_2026 no cambia competencia. La brecha de los «ceros» (`docs/COMPETENCIA_CERO.md`) **no** se cierra con DENUE: lo que falta son informales sin registro (SUPUESTO consistente con `docs/OSM_AGUA_COMPETENCIA.md` y `docs/RATING_V3.md` §4).")
w("- **Hallazgo menor:** 7 establecimientos de comercio de bebidas/hielo o mayoreo con nombre de purificadora/venta de agua (SCIAN ≠ 312112) no estaban en `compet.geojson`; 4 caen en colonias del universo. Si Nicolás quiere, se pueden añadir como competidores «SUPUESTO por nombre» en un próximo build; impacto en ranking = nulo en top-30.")
w("- Cobertura temporal: DENUE 05_2026 tiene `fecha_alta` máx. 2026-04; altas de mayo–octubre no están. Un 312112 inscrito en DENUE ≠ abierto hoy (hay rezagos y bajas no actualizadas).")
w("- Fuera de alcance: no se llamó a la API DENUE (requiere token) ni a ningún servicio; no se contactó a ningún establecimiento.")
open(f"{ROOT}/docs/DENUE_AGUA_VS_COMPETENCIA.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
