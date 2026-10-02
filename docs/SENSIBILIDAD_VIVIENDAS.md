# Sensibilidad: viviendas Censo 2020 vs `pob/3.6` en el score v3 base

**Etiqueta: MODELO (traslape de áreas colonia↔AGEB, Censo 2020).** El Censo no publica viviendas por colonia; `viv_hab_censo_est` reparte las viviendas habitadas de cada AGEB por el área que se traslapa con la colonia. Es una **sensibilidad**, no un reemplazo del score titular. Nada de `colonias_v3.csv` ni del mapa publicado se modificó.

- Script: `scripts/sensibilidad_viviendas_censo.py` (sin red; reproducible). Salida: `v2/data/colonias_v3_sensibilidad_censo.csv` (167 filas; columnas nuevas `score_base_censo`, `rank_base_censo`, `delta_rank_censo`, y variante B `*_demviv`).
- Entrada: `v2/data/colonias_v3.csv` (conteos de anclas/competencia, D*), `data/colonias.geojson` (`demanda_raw`), y `inegi_purificador/datos/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv` (read-only, 381 AGEB, 167 colonias).

## Qué cambia y qué no

`score_base = 100·(0.40·D* + 0.30·A* + 0.30·(1−C*))`. Las **viviendas sólo entran como divisor** de Anclas/1 000 viv. y Competencia/1 000 viv. (`build_v3_rating.py` l.243-258). Los conteos (anclas ponderadas, purificadoras ≤300 m) no cambian.
**Demanda\* (D\*) no usa viviendas**: es `pob_eff · mezcla(OVHAC, OVSAE)` con población (walkshed), min-max. Además `pob_conapo` ≈ Censo (suma 742,016 vs 738,286 → razón 1.005, MODELO). Por eso:

- **Variante A (titular de la sensibilidad, `score_base_censo`)**: A* y C* con viviendas Censo; D\* idéntica.
- **Variante B (cota superior, `score_base_censo_demviv`)**: además supone demanda ∝ viviendas (`demanda_raw × viv_censo/viviendas_est`, re-min-max). Es un supuesto extremo, no la regla actual.

## Magnitud del sesgo de viviendas

- Σ `viviendas_est` (pob/3.6) = **206,119** vs Σ Censo-habitadas (MODELO) = **188,146** → razón global 1.096.
- Razón por colonia `viviendas_est / viv_censo`: mediana **1.102**, rango 0.89–1.45. Ocupantes/vivienda Censo (mediana): 3.97 (vs 3.6 supuesto).
- Ojo: el CSV de INEGI cuenta **viviendas particulares habitadas**; `pob/3.6` pretende viviendas totales servidas. Si se quisieran viviendas totales (incl. deshabitadas) la diferencia sería menor; no se calcula aquí por no estar en el CSV.

## Chequeo de reproducción

Recalcular el base con `pob_conapo/3.6` (exacto) reproduce `score_base` con diferencia máx. **0.005 pts** y **0** rangos distintos (redondeo de D_star a 4 decimales en el CSV). Procedimiento validado.

## Resultado

| Métrica | Variante A (A*,C* con viv Censo) | Variante B (+demanda ∝ viv) |
|---|--:|--:|
| Spearman rank_base vs rank censo | **0.9889** | 0.9916 |
| Top-10 en común (de 10) | **9** | 9 |
| Top-20 en común (de 20) | 18 | 18 |
| Top-30 en común (de 30) | 29 | 29 |
| Colonias que se mueven >10 rangos | **17** | 13 |
| Mov. absoluto mediano / máximo (rangos) | 3 / 29 | 2 / 27 |
| Cambio de score medio (pts) | -0.00 | +0.41 |

### Top-10 (base actual vs con viviendas Censo, variante A)

| # base | Colonia | Municipio | Score base | # Censo | Score Censo | Δ | Razón viv est/Censo |
|--:|---|---|--:|--:|--:|--:|--:|
| 1 | Ampliacion Municipal | Monterrey | 73.7 | 1 | 74.3 | +0 | 1.23 |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 69.5 | 2 | 72.3 | +0 | 1.21 |
| 3 | San Miguel Residencial | General Escobedo | 69.5 | 4 | 69.3 | -1 | 1.01 |
| 4 | Croc | Monterrey | 68.7 | 3 | 69.8 | +1 | 1.16 |
| 5 | Pueblo Nuevo 4To Sector | Apodaca | 67.0 | 6 | 67.2 | -1 | 1.12 |
| 6 | Pueblo Nuevo 1Er Sector | Apodaca | 66.8 | 8 | 66.8 | -2 | 1.11 |
| 7 | Fomerrey 24 | Monterrey | 66.3 | 7 | 66.8 | +0 | 1.25 |
| 8 | Gloria Mendiola | Monterrey | 65.7 | 5 | 67.3 | +3 | 1.19 |
| 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 65.7 | 12 | 65.5 | -3 | 1.10 |
| 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 65.2 | 9 | 66.6 | +1 | 1.14 |

Top-10 **nuevo** (variante A):

| # Censo | Colonia | Municipio | Score Censo | # base |
|--:|---|---|--:|--:|
| 1 | Ampliacion Municipal | Monterrey | 74.3 | 1 |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 72.3 | 2 |
| 3 | Croc | Monterrey | 69.8 | 4 |
| 4 | San Miguel Residencial | General Escobedo | 69.3 | 3 |
| 5 | Gloria Mendiola | Monterrey | 67.3 | 8 |
| 6 | Pueblo Nuevo 4To Sector | Apodaca | 67.2 | 5 |
| 7 | Fomerrey 24 | Monterrey | 66.8 | 7 |
| 8 | Pueblo Nuevo 1Er Sector | Apodaca | 66.8 | 6 |
| 9 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 66.6 | 10 |
| 10 | Paseo de Las Minas | Santa Catarina | 66.4 | 13 |

Entran al top-10: Paseo de Las Minas (#13→#10). Salen: Floridos Bosques del Nogalar (#9→#12).

### Colonias que se mueven >10 rangos (variante A): 17

| # base | Colonia | Municipio | # Censo | Δ rangos | Razón viv est/Censo | Anclas pond | Purif ≤300 m |
|--:|---|---|--:|--:|--:|--:|--:|
| 32 | Emiliano Zapata | Monterrey | 50 | -18 | 0.96 | 16.55 | 0 |
| 41 | Constituyentes del 57 | Monterrey | 55 | -14 | 0.97 | 19.5 | 0 |
| 43 | Argentina | Monterrey | 72 | -29 | 0.92 | 11.75 | 0 |
| 46 | Vicente Guerrero | Guadalupe | 66 | -20 | 0.99 | 17.4 | 0 |
| 48 | Monte Kristal | Juárez | 63 | -15 | 1.04 | 82.9 | 5 |
| 50 | Libertadores de America | Monterrey | 37 | +13 | 1.32 | 12.85 | 0 |
| 58 | Villas de San Francisco 2Do Sector | General Escobedo | 71 | -13 | 0.96 | 15.15 | 0 |
| 60 | Fomerrey 116 (San Bernabe 8) | Monterrey | 45 | +15 | 1.26 | 36.2 | 1 |
| 67 | Atoyac de Alvarez | Guadalupe | 38 | +29 | 1.45 | 10.55 | 0 |
| 70 | Const de Queretaro 1 Sec | San Nicolás de los Garza | 97 | -27 | 0.90 | 18.75 | 0 |
| 99 | Fomerrey 45 | Monterrey | 86 | +13 | 1.29 | 24.3 | 1 |
| 111 | Unidad Pedreras ( Fomerrey 106 ) | Monterrey | 92 | +19 | 1.24 | 30.5 | 3 |
| 114 | Hacienda Renacimiento | García | 129 | -15 | 0.89 | 14.25 | 0 |
| 115 | Monte Kristal 4To Sector | Juárez | 127 | -12 | 1.04 | 17.35 | 1 |
| 127 | Unidad del Pueblo | Monterrey | 106 | +21 | 1.26 | 17.7 | 1 |
| 137 | Ignacio Zaragoza | Guadalupe | 151 | -14 | 0.94 | 23.55 | 1 |
| 151 | Riberas de La Silla | Guadalupe | 140 | +11 | 1.12 | 19.4 | 1 |

## Lectura

- Un sesgo casi uniforme (~10 %) **no** mueve el ranking por sí mismo: sólo importa la variación **entre colonias** de la razón (0.89–1.45). Como A* y C* son rangos percentiles, el efecto es de reordenamiento local, no de nivel.
- La Demanda\* (40 % del score) no cambia en la variante A; por eso el Spearman es alto.
- Las colonias con razón alta (pob/3.6 sobrestima más) tienden a ganar densidad de anclas al corregir y a subir; las de razón ≤1 tienden a bajar (ver tabla de movers: los mayores descensos tienen razón 0.92–1.04). Las que tienen 0 purificadoras mantienen C*=0 sin importar viviendas.
- **Recomendación (pendiente de Nicolás):** el efecto es de segundo orden para decidir zonas top-30, pero conviene usar viviendas Censo cuando se regenere el build (cambio de 1 línea: dividir por `viv_hab_censo_est`). No se aplicó: v3 titular y mapa publicado quedan intactos. Captura 3 % y 2 garr/viv/sem siguen siendo supuestos [ESTIMADO].

## Límites
- MODELO: traslape de áreas supone viviendas uniformemente distribuidas dentro del AGEB; polígonos de colonia no son oficiales.
- No se re-ejecutó todo `build_v3_rating.py` (celdas, spots no cambian por esta sensibilidad); sólo el score a nivel colonia.
- Viviendas habitadas ≠ viviendas totales.
