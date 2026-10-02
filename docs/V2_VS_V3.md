# v2 vs v3 base: por qué los rankings no coinciden (y cuál rige)

> **⚠ RECOMENDACIÓN PENDIENTE DE NICOLÁS (no es decisión):** «v3 base para ZMM; v2/estudio para foco de campo Escobedo» es solo una **recomendación** del análisis. Nicolás aún no la ha aprobado ni rechazado; ningún ranking, mapa ni `index.html` cambia hasta que él decida.

Todo sale de `data/colonias.geojson` (lo que lee el hub), `v2/data/colonias_v3.csv` y `/workspace/colonias_v2_scored.csv`. Script reproducible: `scripts/analisis_v2_vs_v3.py` (sin red). Tabla por colonia: `v2/data/comparacion_v2_vs_v3.csv` (167 filas). No se tocó ningún ranking ni `index.html`.

## 1. Resumen

- Spearman rank v2 (hub) vs rank v3 base = **0.336**; top-10 en común: **2** (Croc, San Miguel Residencial); top-20: 4; top-30: 8.
- **Demanda\* es idéntica** en ambos (dif. máx. 0.0000) → no es la causa. La diferencia viene de **Anclas\*, Competencia\* y del peso efectivo** de cada término.
- Pesos nominales v2 40/25/20(+15 constante) vs v3 40/30/30 parecen cercanos, pero el **peso efectivo** (parte de la varianza del score entre colonias) cambia mucho: ver §2.
- **Signo de competencia: igual** en ambos (más competidores = menos puntos; `1−Comp*`). No es un error de signo. Lo que cambia es *qué* mide Comp\* y cómo trata el 0 (§3).
- Escobedo cae porque sus colonias son grandes (anclas/1 000 viv. diluidas) y v2 premiaba su demanda (§5).

## 2. Peso efectivo de cada término (el motivo principal)

v2: cada término es min-max sobre su valor crudo; Anclas\* v2 está muy sesgada a 0 (mediana 0, media 0.09) y Comp\* v2 tiene dispersión chica (sd 0.15). v3: Anclas\* y Comp\* son **rangos percentiles** (distribución uniforme 0–1, sd ≈0.29–0.36) → pesan mucho más aunque el peso nominal sea parecido.

| Término | Puntos v2: sd | Parte de la varianza v2 | Puntos v3: sd | Parte de la varianza v3 |
|---|--:|--:|--:|--:|
| Demanda (40 pts, igual) | 7.41 | **69 %** | 7.41 | **22 %** |
| Competencia | 3.83 | **19 %** | 10.71 | **47 %** |
| Anclas | 3.09 | **12 %** | 8.74 | **31 %** |

- v2 es esencialmente un ranking de **demanda** (Spearman score v2 vs D\* = **0.82**). v3 base casi no lo es (score v3 vs D\* = **0.37**); lo mueve más la competencia (Spearman con (1−C\*) = -0.67).
- Anclas v2 vs v3 correlacionan poco (Spearman **0.24**): v2 = suma ponderada ≤250 m del **centroide** con decaimiento (jardines, iglesias, hospital, universidad…); v3 = conteo ponderado en polígono+100 m **por 1 000 viv.** (cerveza, tortillería, Oxxo, bancos, paradas…). Son dos definiciones distintas de «ancla».
- Competencia v2 vs v3: Spearman **0.11**. v2 = DENUE formal con decaimiento ~400 m + **proxy informal 1.0/1 000 viv.** (constante por vivienda); v3 = conteo ≤300 m del polígono por 1 000 viv., percentil.

### Ablación: cambiar un término a la vez (Spearman del score resultante contra el original)

| Experimento | Spearman |
|---|--:|
| v2 con Anclas\* de v3 | 0.62 |
| v2 con Comp\* de v3 | 0.58 |
| v2 con Anclas\* y Comp\* de v3 (pesos v2) | 0.43 |
| v3 con Anclas\* de v2 | 0.77 |
| v3 con Comp\* de v2 | 0.51 |
| v3 con Anclas\* y Comp\* de v2 (pesos v3) | 0.31 |
| v3 con los **términos v3** pero **pesos v2** (40/25/20) | 0.98 |

Lectura: (1) los **pesos nominales casi no importan**: con términos v3 y pesos v2 la correlación con v3 es 0.98. (2) Lo que cambia el ranking es **cómo se define y escala Anclas\* y Comp\***: cambiar Comp\* pesa más que cambiar Anclas\* (v3 con Comp\* v2 → 0.51; con Anclas\* v2 → 0.77); cambiar ambos → 0.31, es decir, casi todo el 0.34 de Spearman se explica por esos dos términos.

## 3. Competencia: signo y el «0»

- Mismo signo: en ambos, más competencia resta puntos. Verificado recalculando v2 = 40·D\*+25·(1−Comp\*)+20·Anclas\*+15 contra `score_100` (dif. máx. 0.008).
- En v3, **58 colonias (35 %) tienen 0 purificadoras detectadas ≤300 m** y reciben Comp\*=0 → los 30 pts completos. En v2 esas mismas colonias **no** tienen competencia cero: Comp\* v2 mediana **0.21** (todas: 0.23) porque v2 siempre suma el proxy informal (mediana 0.84).
- Consecuencia: v3 premia la **ausencia de datos** de competencia (DENUE/Places no ven informales; ver `docs/COMPETENCIA_CERO.md`). Eso explica los saltos grandes (Ampliación Municipal #73→#1, Floridos Bosques del Nogalar #161→#9: ambos con 0 competidores).
- Además, v2 Comp\* correlaciona **positivo** con Demanda\* (Spearman 0.26: más gente ⇒ más competencia estimada), así que v2 se compensa a sí mismo; en v3 la correlación es -0.04 (no se compensa).

## 4. Top-20 de cada ranking

### Top-20 v2 (hub)

| # v2 | # v3 | Colonia | Municipio | D* | Anclas* v2 | Anclas* v3 | Comp* v2 | Comp* v3 | Purif ≤300 m | Score v2 | Score v3 |
|--:|--:|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | 4 | Croc | Monterrey | 1.00 | 0.15 | 0.37 | 0.26 | 0.42 | 3 | 76.5 | 68.7 |
| 2 | 44 | San Gilberto | Santa Catarina | 0.57 | 1.00 | 0.60 | 0.33 | 0.62 | 4 | 74.5 | 52.2 |
| 3 | 3 | San Miguel Residencial | General Escobedo | 0.88 | 0.00 | 0.14 | 0.14 | 0.00 | 0 | 71.7 | 69.5 |
| 4 | 33 | Riveras del Rio | Monterrey | 0.85 | 0.00 | 0.17 | 0.26 | 0.48 | 2 | 67.6 | 54.8 |
| 5 | 23 | Villas de San Francisco | General Escobedo | 0.74 | 0.00 | 0.01 | 0.14 | 0.00 | 0 | 66.1 | 60.0 |
| 6 | 76 | Lomas de La Fama | Santa Catarina | 0.47 | 0.78 | 0.34 | 0.34 | 0.50 | 1 | 65.9 | 43.9 |
| 7 | 86 | Burocratas Municipales | Monterrey | 0.65 | 0.32 | 0.25 | 0.26 | 0.70 | 4 | 65.7 | 42.1 |
| 8 | 25 | Nuevo Leon Estado de Progreso (Alianza Real) | General Escobedo | 0.90 | 0.00 | 0.14 | 0.41 | 0.35 | 1 | 65.6 | 59.5 |
| 9 | 28 | Topo Chico | Monterrey | 0.52 | 0.47 | 0.58 | 0.23 | 0.36 | 1 | 64.6 | 57.8 |
| 10 | 65 | Independencia | Monterrey | 0.73 | 0.00 | 0.07 | 0.26 | 0.45 | 6 | 62.7 | 47.7 |
| 11 | 48 | Monte Kristal | Juárez | 0.60 | 0.00 | 0.61 | 0.07 | 0.72 | 5 | 62.5 | 50.8 |
| 12 | 74 | Prados de La Cieneguita | Apodaca | 0.55 | 0.51 | 0.67 | 0.39 | 0.91 | 6 | 62.3 | 44.8 |
| 13 | 130 | Gloria Mendiola | General Escobedo | 0.54 | 0.00 | 0.00 | 0.09 | 0.57 | 1 | 59.5 | 34.5 |
| 14 | 89 | La Altamira | Monterrey | 0.62 | 0.00 | 0.11 | 0.23 | 0.56 | 2 | 59.2 | 41.6 |
| 15 | 8 | Gloria Mendiola | Monterrey | 0.63 | 0.00 | 0.36 | 0.25 | 0.00 | 0 | 58.8 | 65.7 |
| 16 | 59 | Cañada Blanca | Guadalupe | 0.51 | 0.31 | 0.33 | 0.32 | 0.39 | 2 | 58.7 | 48.7 |
| 17 | 68 | Rancho Viejo | Juárez | 0.53 | 0.00 | 0.84 | 0.16 | 0.99 | 7 | 57.2 | 46.6 |
| 18 | 92 | La Unidad | General Escobedo | 0.43 | 0.21 | 0.26 | 0.19 | 0.46 | 2 | 56.5 | 41.0 |
| 19 | 12 | San Bernabe 1Er Sector | Monterrey | 0.84 | 0.06 | 0.41 | 0.76 | 0.38 | 2 | 56.0 | 64.6 |
| 20 | 42 | Fernando Amilpa | General Escobedo | 0.43 | 0.12 | 0.17 | 0.16 | 0.00 | 0 | 55.5 | 52.4 |

### Top-20 v3 base

| # v2 | # v3 | Colonia | Municipio | D* | Anclas* v2 | Anclas* v3 | Comp* v2 | Comp* v3 | Purif ≤300 m | Score v2 | Score v3 |
|--:|--:|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 73 | 1 | Ampliacion Municipal | Monterrey | 0.39 | 0.00 | 0.93 | 0.38 | 0.00 | 0 | 46.2 | 73.7 |
| 39 | 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 0.45 | 0.18 | 0.72 | 0.39 | 0.00 | 0 | 51.9 | 69.5 |
| 3 | 3 | San Miguel Residencial | General Escobedo | 0.88 | 0.00 | 0.14 | 0.14 | 0.00 | 0 | 71.7 | 69.5 |
| 1 | 4 | Croc | Monterrey | 1.00 | 0.15 | 0.37 | 0.26 | 0.42 | 3 | 76.5 | 68.7 |
| 51 | 5 | Pueblo Nuevo 4To Sector | Apodaca | 0.20 | 0.23 | 0.97 | 0.12 | 0.00 | 0 | 49.6 | 67.0 |
| 133 | 6 | Pueblo Nuevo 1Er Sector | Apodaca | 0.17 | 0.00 | 1.00 | 0.21 | 0.00 | 0 | 41.5 | 66.8 |
| 121 | 7 | Fomerrey 24 | Monterrey | 0.20 | 0.04 | 0.94 | 0.25 | 0.00 | 0 | 42.6 | 66.3 |
| 15 | 8 | Gloria Mendiola | Monterrey | 0.63 | 0.00 | 0.36 | 0.25 | 0.00 | 0 | 58.8 | 65.7 |
| 161 | 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 0.15 | 0.04 | 0.99 | 0.38 | 0.00 | 0 | 37.2 | 65.7 |
| 48 | 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 0.36 | 0.15 | 0.69 | 0.30 | 0.00 | 0 | 49.9 | 65.2 |
| 96 | 11 | La Playa | Guadalupe | 0.13 | 0.23 | 0.99 | 0.21 | 0.00 | 0 | 44.5 | 65.0 |
| 19 | 12 | San Bernabe 1Er Sector | Monterrey | 0.84 | 0.06 | 0.41 | 0.76 | 0.38 | 2 | 56.0 | 64.6 |
| 38 | 13 | Paseo de Las Minas | Santa Catarina | 0.48 | 0.00 | 0.49 | 0.29 | 0.00 | 0 | 51.9 | 64.0 |
| 117 | 14 | Paseo del Nogalar | San Nicolás de los Garza | 0.24 | 0.18 | 0.80 | 0.40 | 0.00 | 0 | 43.0 | 63.5 |
| 120 | 15 | Miguel Hidalgo | Guadalupe | 0.20 | 0.00 | 0.84 | 0.20 | 0.00 | 0 | 42.7 | 63.0 |
| 46 | 16 | Fomerrey 35 (Tierra Propia) | Monterrey | 0.35 | 0.09 | 0.62 | 0.21 | 0.00 | 0 | 50.5 | 62.6 |
| 114 | 17 | Lazaro Cardenas | Monterrey | 0.13 | 0.00 | 0.90 | 0.09 | 0.00 | 0 | 43.1 | 62.4 |
| 149 | 18 | Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 0.16 | 0.09 | 0.85 | 0.34 | 0.00 | 0 | 39.7 | 61.8 |
| 88 | 19 | Fomerrey 115 (San Bernabe 12) | Monterrey | 0.39 | 0.12 | 0.52 | 0.51 | 0.00 | 0 | 45.3 | 61.5 |
| 81 | 20 | Indeco La Fama 1 | Santa Catarina | 0.08 | 0.52 | 0.92 | 0.32 | 0.00 | 0 | 45.7 | 60.8 |

Cada fila lleva los dos rangos y los componentes para ver qué término la mueve. Columnas completas (167 colonias, puntos por término): `v2/data/comparacion_v2_vs_v3.csv`.

## 5. Por qué cae General Escobedo

| Indicador | Escobedo (26) | Resto (141) |
|---|--:|--:|
| Colonias en top-20 v2 → v3 | 6 → **1** | — |
| Colonias en top-50 v2 → v3 | 12 → 4 | — |
| Rango medio v2 → v3 | 73 → 89 | — |
| Demanda\* media | 0.34 | 0.28 |
| Anclas\* v2 media | 0.05 | 0.10 |
| Anclas\* v3 media | 0.39 | 0.52 |
| Comp\* v2 media | 0.20 | 0.27 |
| Comp\* v3 media | 0.45 | 0.44 |
| Viviendas est. (mediana) | 1115 | 863 |
| Anclas ponderadas/1 000 viv. (mediana) | 20.8 | 24.6 |
| Colonias con 0 purificadoras ≤300 m | 8 de 26 | 50 de 141 |

- Escobedo tiene **mayor demanda** (0.34 vs 0.28) y **menos competencia v2** (0.20 vs 0.27) → v2 lo favorece (peso efectivo de demanda 69 %).
- En v3 el peso se traslada a Anclas/1 000 viv. y Comp/1 000 viv.: sus colonias son **más grandes** (más viviendas) → la densidad de anclas baja (Anclas\* v3 0.39 vs 0.52), la competencia ya no las distingue (Comp\* v3 0.45 vs 0.44, antes 0.20 vs 0.27 en v2) y la ventaja de demanda pesa 22 %, no 69 %.
- La caída es por **método**, no por evidencia de campo nueva. El Scout apoya a Escobedo en las colonias encuestadas: San Miguel Residencial (22 marcas) sigue #3–#4 en v3 base/con Scout.

## 6. Hub vs `colonias_v2_scored.csv` (#5/#18 vs #8/#19)

- **El hub muestra el rank de `data/colonias.geojson`** (`p.rank`, `index.html` l.2045/2146; la lista se ordena por `score_100` del mismo archivo). Ahí: Villas de San Francisco **#5**, La Unidad **#18**, San Bernabé 1er Sector #19, Riveras del Río #4.
- `/workspace/colonias_v2_scored.csv` (idéntico a `/home/box/purificadoras/workspace/colonias_v2_scored.csv`, md5 d7fe8f6f…) da Villas **#8**, La Unidad **#19**, San Bernabé #24, Riveras #6; rank distinto en **161 de 167** colonias (Spearman 0.883); Croc 81.6 (#2) vs hub 76.5 (#1); San Gilberto #1 (82.69) vs hub #2 (74.53).
- Causa (evidencia): el CSV es de la **fórmula anterior** al update del 2026-09-12 (nota `version2_formula_update_nota.md`: Comp\* = formal + informal 1.0/1 000 viv.; pesos de anclas nuevos). Sus columnas `comp_star`/`anclas_star` difieren de las del hub (Spearman comp 0.60, anclas 0.92); recalculado con sus propios componentes cada archivo es auto-consistente (dif. máx. CSV 0.01, hub 0.01). No es un bug del hub: **el CSV de la caja está desactualizado** (el de OneDrive en la PC de Nicolás es el regenerado, según esa nota; no accesible desde la caja).
- **Qué lee la rutina diaria:** la automatización `reporte-diario-purificadoras` (cron 08:18 CDMX) **no nombra ningún archivo de ranking**; su prompt dice «mapa/repo CASCA-code/mapa-purificadoras y site https://casca-code.github.io/mapa-purificadoras/» → en la práctica `data/colonias.geojson` / hub (top-5 Croc 76.5 · San Gilberto 74.5 · San Miguel Residencial 71.7 · Riveras 67.6 · Villas 66.1, coincide con el hub). La receta A de `purif-sitios` manda comparar contra `colonias_v2_scored.csv` de la caja: **esa comparación produce el falso «el hub miente»**. Recomendación: no usar el CSV de la caja como referencia hasta regenerarlo/sincronizarlo con la PC [pendiente de Nicolás/Sitios]. (No se pudo leer el texto de ejecuciones pasadas del reporte; sólo su prompt.)
- El rank del hub y `v2_rank` en `colonias_v3.csv` son el mismo (`data/colonias.geojson`).

## 7. Recomendación (PENDIENTE DE NICOLÁS — no es decisión tomada)

1. **ZMM completo (lista larga / dónde mirar primero): v3 base** como filtro, porque tiene cobertura uniforme (DENUE+Places+OSM), anclas por vivienda y celdas de 100 m, **pero** tratando las 58 colonias con 0 competidores como *no verificadas* hasta confirmar en campo (§3).
2. **Foco de campo en Escobedo: mantener v2 / estudio** (San Miguel Residencial, Villas de San Francisco, Alianza Real): es el criterio de Purificador vigente (demanda D+/D) y v3 las baja por método, no por evidencia. San Miguel Residencial está en el top-4 de ambos rankings (#3 v2, #3 v3).
3. Colonias en **ambos** top-30 son las más robustas (ver CSV `comparacion_v2_vs_v3.csv`, filtrar `rank_v2_hub<=30` y `rank_base<=30`): Croc, Gloria Mendiola, Nuevo Leon Estado de Progreso (Alianza Real), San Bernabe 1Er Sector, San Miguel Residencial, Topo Chico, Unidad Piloto, Villas de San Francisco.
4. Antes de formalizar cualquiera: calibrar con 10–15 conteos de esquina y ventas reales (pesos son de juicio).
5. Si se quiere un solo ranking, probar v3 con Comp\* que no regale puntos máximos al 0 (p. ej. piso mediano para colonias sin Scout) — **sólo como propuesta, no implementada**.

