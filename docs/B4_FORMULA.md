# B4: fórmula de calificación de colonias (competencia: solo suma, nunca resta)

**Pedidos (Nicolás, 2026-10-03):** (1) «la competencia es buena» (absorber clientes con recarga a $12), pero no debe pesar mucho y **solo suma, nunca resta**; (2) el ranking de e7d1ecc quedó mal (Spearman −0.19, Croc #4→#8, subían colonias lejanas de Juárez/García); (3) **sin competencia no debe bajar el ranking** («mercado virgen»). Aplica **solo a `/b4/`**; el hub, `v2/`, `v3_espectaculares/` y Scout no cambian.

> **Todo lo marcado SUPUESTO es de juicio, no calibrado con ventas.** No hay datos de ventas que digan si más competidores a ≤300 m suben o bajan las ventas de una purificadora propia. **No se asume absorción del 100 %**: el bono es chico y con tope.

## Fórmula (build 2026-10-03, reemplaza a e7d1ecc)

```text
base_renorm = 100 × (0.45·Demanda* + 0.45·Anclas*) / 0.90          # = 50·(D*+A*)

0 competidores detectados  ⇒  score = base_renorm                  # competencia EXCLUIDA («mercado sin atender»); no resta, no hay valor neutro
con competidores           ⇒  score = max( base_renorm ,  100 × (0.45·D* + 0.45·A* + 0.10·Comp_bonus*) )
Comp_bonus*                = min(P, 0.80) / 0.80                   # P = percentil (0–1) de purificadoras ≤300 m por 1,000 viviendas (= C_star de v3)
```

- Con competidores, `100×(0.45D+0.45A+0.10Cb) = 0.9·base_renorm + 10·Cb`. El `max(...)` garantiza que **nunca baja de `base_renorm`** (si Cb es bajo, el bono es 0). Bono = `score − base_renorm`, **máximo 10 puntos** y en la práctica ≤ 9.73 (mediana 4.0, p90 6.1; 103 de 109 colonias con competencia reciben bono > 0; 6 reciben 0, entre ellas Croc).
- **Pesos 0.45 / 0.45 / 0.10** (pedido de Nicolás). Demanda\* y Anclas\* sin cambio (v3, `docs/RATING_V3.md`).
- **Tope p80 (SUPUESTO):** desde el percentil 80 el bono ya es 1.0. Más competidores no suman más. P se calcula con las 167 colonias (los 58 ceros ocupan los percentiles bajos, de modo que una colonia con 1 competidor de tasa baja tiene Cb ≈ 0.44 y su bono puede quedar en 0).
- **Absorción alta pero poco peso:** el 0.10 es la única forma en que entra la absorción; no se modela cuánto cliente se capta (SUPUESTO que sí hay alguno; no hay dato).
- **«Mercado sin atender» (`mercado_sin_atender = sin_verificar = comp_n_300m == 0`, 58 colonias):** significa **0 detectadas por DENUE + Places**; las purificadoras informales no se ven, así que 0 es «no detectada», no «mercado libre» (`docs/COMPETENCIA_CERO.md`). La UI lo marca así y la competencia queda fuera de su score.
- Con Scout (interruptor, apagado por defecto): misma fórmula con `A_star_scout`, `C_star_scout` y `comp_n_300m_with_scout`.
- Sensibilidad al bono: sin bono (`score_sin_comp`) el Top 10 coincide 9/10 y el Top 30 25/30 con el ranking final; Spearman 0.986. **Ojo Rancho Viejo (7 competidores):** sin bono ya sería #2 (68.55) por Demanda/Anclas; el bono (+3.14) lo pasa a #1 por 3.0 pts sobre Croc (68.67 sin bono, 0.12 de diferencia: empate técnico). Con banda p10–p90 de #1 a #3 para ambas.

## Campos de `b4/data/colonias_b4.geojson`

| Campo | Significado |
|---|---|
| `score_base`, `rank_base` | **Fórmula nueva.** Alimentan etiqueta, color, Top 10 y ranking. |
| `score_sin_comp` | `base_renorm` (Demanda + Anclas reescaladas a 100, sin competencia). |
| `bono_comp_pts` | `score_base − score_sin_comp` (≥ 0, ≤ 10). |
| `Cb_star` | Comp_bonus\* (0–1); `null` si 0 competidores (componente excluido). |
| `sin_verificar`, `mercado_sin_atender` | `comp_n_300m == 0`. |
| `score_prev2`, `rank_prev2` (y `score_with_scout_prev2`, `rank_with_scout_prev2`) | **Fórmula previa (commit e7d1ecc):** `100·(0.40D+0.30A+0.30·Cb)`, 0 comp ⇒ bonus 0. Reproduce exactamente los rangos de e7d1ecc (167/167). |
| `score_prev`, `rank_prev` (y `*_with_scout_prev`) | v3 original (916576d): `100·(0.40D+0.30A+0.30(1−C))`, la competencia resta. |
| `delta_rank_prev2_to_b4`, `delta_rank_prev_to_b4` | rango anterior − rango nuevo. |
| `rank_p10/p50/p90`, `ancho_banda`, `banda`, `confianza`, `prob_top10`, `prob_top30`, `prob_top30_estres` | **Recalculados con esta fórmula** (ver abajo). |
| `dist_casa_km`, `cen_lat`, `cen_lon` | Distancia en línea recta (haversine) de la casa al **centroide del polígono** de la colonia; informativo, **no entra al score**. |
| `est`, `n_est_sugeridas`, `pend_*`, `n_est_plana` | Sin cambio de lógica (estaciones salen de celdas de 100 m; pendiente con `build_b4_topografia.py`). |

## Banda de confianza recalculada (p10 / p50 / p90, prob_top30)

`scripts/banda_confianza_b4.py` (offline, semilla 20261002, 4,000 sorteos; la corre `build_b4.py`; salida `b4/data/colonias_b4_banda.csv`). **Misma metodología que `docs/BANDA_CONFIANZA.md`**, aplicada a la fórmula nueva: pesos ±30 % (0.45/0.45/0.10 renormalizados), viviendas entre Censo 2020 y pob/3.6, y los 58 ceros tratados como competencia desconocida (su tasa se sortea de la empírica; si sale > 0 solo **suma** bono; versión «estrés»: sorteada solo entre colonias con competencia). Reglas de `confianza` sin cambio (ancho ≤30 estrecha / ≤60 media / >60 ancha; −1 si no hay Scout). Es **MODELO de sensibilidad, no pronóstico ni intervalo estadístico.** Resultado: confianza alta 10 / media 119 / baja 38; ancho mediano 22 puestos. Se quitó de la UI el aviso de «banda de la fórmula anterior».

## Cortes de etiqueta (60 / 50 / 40) — se mantienen, conteos

| | Excelente ≥60 | Buena 50–59.9 | Regular 40–49.9 | Baja <40 |
|---|---:|---:|---:|---:|
| v3 original (916576d) | 22 | 29 | 44 | 72 |
| e7d1ecc | 31 | 33 | 26 | 77 |
| **Nueva** | **19** | **38** | **41** | **69** |

Se mantienen 60/50/40 (SUPUESTO de presentación) para comparar con lo que Nicolás ya vio. La media casi no cambia (42.2 vs 42.4) y la desviación baja (15.0 vs 17.3 en e7d1ecc).

## Efecto en el ranking

- Spearman del ranking nuevo vs e7d1ecc: **0.79**; vs 916576d: **0.38** (no es una vuelta al v3: ahora sin competencia no baja, pero la competencia ya no resta). Top 10 en común con e7d1ecc: 7/10; con 916576d: 2/10. Top 30: 24/30 con e7d1ecc; 6/30 con 916576d.
- Las 58 colonias «mercado sin atender» pasan de promedio 24.1 (e7d1ecc) a 35.9.
- **Colonias lejanas:** Juárez 4 de 13 en el Top 30 (mejor #1, Rancho Viejo); García 2 de 7 (mejor #12). Siguen apareciendo porque sus Demanda/Anclas son altas, no por competencia; el Top 30 ya no es dominado por ellas, pero es el modelo, no una instrucción de ir a campo (para eso `dist_casa_km` y el filtro «Cerca de mí»).
- Diagnóstico de Croc: `docs/B4_CROC.md`.

## Distancia a casa y filtro «Cerca de mí»

- Casa: Violeta 116, Los Colorines, San Pedro Garza García. Coordenada usada: **25.63028, −100.34602** (la misma de `index.html` y `docs/RUTA_CAMPO.md`; pin aproximado en calle Violeta según OSM, **no** geocodificación exacta del número 116; SUPUESTO ±unos cientos de metros). Sin API.
- Colonia: **centroide del polígono** (shapely). Para 12 colonias el centroide difiere > 300 m del `lat/lon` que trae el dato (punto de referencia v3); la distancia usa el centroide.
- Línea recta (haversine), **no** distancia por calles ni tiempo de manejo. Rango 4.0–35.2 km (25 colonias ≤10 km; 83 ≤15 km).
- UI: se muestra en el ranking y en la ficha (popup). Filtro opcional **«Cerca de mí (casa) ≤ X km»** en Más opciones → Orden y filtros (apagado por defecto); solo oculta filas del ranking y atenúa el polígono, **no cambia score ni rank**.

## Limitaciones

- Más competidores a ≤300 m no implica más ventas propias (mercado saturado vs. clientes por absorber). El tope p80 y el peso 0.10 son una mitigación, no una calibración.
- DENUE + Places subcuentan purificadoras; «mercado sin atender» no es «sin competencia».
- Falta validar en campo (Scout) o con ventas reales antes de decidir dinero con esto.

Reproducir: `python3 scripts/build_b4.py && python3 scripts/build_b4_topografia.py` (en ese orden; `build_b4.py` ejecuta antes `scripts/banda_confianza_b4.py`; constantes en `scripts/b4_formula.py`).
