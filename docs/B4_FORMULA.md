# B4: fórmula de calificación de colonias (la competencia SUMA)

**Pedido (Nicolás, vía Yamil, 2026-10-03):** «la competencia es buena». En B4 la competencia deja de restar: suma como bonus con tope (estrategia: absorber clientes de la competencia con recarga a $12). Aplica **solo a `/b4/`**; el hub, `v2/`, `v3_espectaculares/` y Scout no cambian.

> **TODO lo de abajo marcado SUPUESTO es de juicio, no calibrado con ventas.** No hay datos de ventas que digan si más competidores a ≤300 m suben o bajan las ventas de una purificadora propia. Es una hipótesis de negocio de Nicolás convertida en fórmula.

## Fórmula

```text
score_base (B4) = 100 × ( 0.40 · Demanda*  +  0.30 · Anclas*  +  0.30 · Comp_bonus* )
Comp_bonus*     = min(P, 0.80) / 0.80
```

- **Demanda\*** y **Anclas\***: sin cambios (v3, `docs/RATING_V3.md`).
- **P** = percentil (0–1) de «purificadoras dentro del polígono +300 m **por 1,000 viviendas**» entre las 167 colonias. Es el mismo `C_star` de v3, con 0 competidores ⇒ P = 0.
- **Tope en p80 (SUPUESTO)**: desde el percentil 80 el bonus ya es 1.0 (30 puntos); más competidores no suman más. Evita premiar mercados saturados sin límite.
- **0 competidores ⇒ bonus 0** y marca **«sin verificar»** (`sin_verificar = true`, 58 colonias): DENUE y Places no ven las purificadoras informales, así que 0 es «no detectada», no «mercado libre».
- Pesos 0.40 / 0.30 / 0.30: **mismos** que v3 (el 0.30 de competencia pasó de restar a sumar). SUPUESTO.
- Con Scout (interruptor, apagado por defecto): misma fórmula con `A_star_scout` y `C_star_scout`.

## Qué cambia en los datos (`b4/data/colonias_b4.geojson`)

| Campo | Significado |
|---|---|
| `score_base`, `rank_base` | **Nuevos** (fórmula B4). Alimentan etiqueta, color, Top 10 y ranking. |
| `score_with_scout`, `rank_with_scout`, `scout_bonus`, `delta_rank_base_to_scout`, `delta_rank_v2_to_base` | Recalculados con la fórmula B4. |
| `Cb_star` | Comp_bonus\* (0–1). |
| `sin_verificar` | `comp_n_300m == 0`. |
| `score_prev`, `rank_prev` (y `score_with_scout_prev`, `rank_with_scout_prev`) | La fórmula anterior (`100·(0.40D+0.30A+0.30(1−C))`, competencia resta), para comparar. |
| `delta_rank_prev_to_b4` | `rank_prev − rank_base`. |
| `rank_p10/p50/p90`, `prob_top30*`, `ancho_banda` | **Sin recalcular**: son de la banda de confianza de la fórmula anterior (`docs/BANDA_CONFIANZA.md`). La UI lo indica. Pendiente de recalcular. |
| `cause_*` | Heredados de v2→v3; no se usan en la UI. |
| `est`, `n_est_sugeridas`, `pend_*`, `n_est_plana` | Sin cambio de lógica (estaciones salen de celdas de 100 m; la pendiente se agrega con `build_b4_topografia.py`). |

Reproducir: `python3 scripts/build_b4.py && python3 scripts/build_b4_topografia.py` (en ese orden).

## Efecto en el ranking (build 2026-10-03)

- Spearman de la calificación nueva vs la anterior (167 colonias): **−0.19** (es decir, casi invertida: antes ganaba quien tenía menos competencia).
- Top 10: **1 de 10** se mantiene (Croc, #4 → #8). Top 30: 1 de 30.
- Las **58 colonias «sin verificar»** (antes con los 30 puntos completos de «poca competencia», varias en el Top 10) pierden hasta 30 puntos: promedio 54.1 → 24.1. Esto es consecuencia directa de «0 ⇒ 0 bonus»; si Nicolás quiere que el 0 no castigue tanto (p. ej. dar un bonus neutro mientras se verifica en campo), es una sola constante.
- Sensibilidad al tope (cuántos del Top 10 coinciden con el de p80): tope p60 → 7; p70 → 8; p90 → 8; sin tope (p100) → 7. El Top 10 es moderadamente estable; el tope cambia sobre todo el orden medio.

## Cortes de etiqueta (60 / 50 / 40) — reevaluados

| | Excelente ≥60 | Buena 50–59.9 | Regular 40–49.9 | Baja <40 | Media / mediana / desv. |
|---|---:|---:|---:|---:|---|
| Fórmula anterior | 22 | 29 | 44 | 72 | 43.5 / 42.4 / 13.1 |
| **B4 (nueva)** | **31** | **33** | **26** | **77** | 42.4 / 43.5 / 17.3 |

Decisión: **se mantienen 60 / 50 / 40.** La media casi no se movió (−1.0) y la escala sigue siendo 0–100 absoluta; lo que cambió es la dispersión (más ancha: la competencia ahora separa más). Excelente pasa de 13 % a 19 % de las colonias y Baja de 43 % a 46 %, un cambio moderado. Alternativa descartada: cortes que reproduzcan los porcentajes anteriores (≈64 / 55 / 39), porque mover los cortes cada vez que cambia la fórmula quita comparabilidad con lo que Nicolás ya vio. Los cortes siguen siendo SUPUESTO de presentación.

## Limitaciones

- Más competidores a ≤300 m no implica más ventas propias: puede ser mercado saturado. El tope p80 es solo una mitigación.
- DENUE + Places subcuentan purificadoras; «sin verificar» no es «sin competencia».
- Hace falta validar en campo (Scout) o con ventas reales antes de usar esto para decidir dinero.
