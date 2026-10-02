# Gaps: rating v3 base vs densidad de viviendas por colonia

Etiqueta: **análisis con archivos locales** (script `scripts/analisis_gaps_rating_densidad.py`, sin red). **No altera ningún score** (`v2/data/colonias_v3.csv` intacto). CSV: `v2/data/gaps_rating_densidad.csv`.

## Método

- Densidad = viviendas habitadas (Censo 2020, modelo por traslape colonia-AGEB, `colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv`, columna `viv_hab_censo_est`) ÷ `area_km2` del polígono CONAPO (`colonias167_conapo_geom.geojson`). Se reportan también viv_est (CONAPO/3.6) y hab/km². **MODELO**: no es dato oficial por colonia.
- Brecha = percentil de densidad − percentil de `score_base` (167 colonias). Positivo = denso con score bajo (posible subvalorada); negativo = score alto con densidad baja (posible sobrevalorada).
- Razón por componente: puntos que aporta cada término a score_base (Demanda* ×40, Anclas* ×30, (1−Comp*) ×30) vs la mediana del 25 % más denso.
- Spearman con score_base: densidad viv Censo 0.05 · viv_est 0.12 · hab 0.12. Densidad vs Demanda* 0.13 · vs Anclas* -0.04 · vs Comp* -0.04.
- Mediana puntos (todas): D 10.3 · A 15.0 · (1−C) 15.0. Mediana del 25 % más denso (n=42): D 10.9 · A 13.8 · (1−C) 15.5.

## 1. Denso pero score bajo (posible subvalorada) — top 15

| # | Colonia | Mun. | Rank base | Score | Viv/km² (Censo) | pct dens | pct score | D·A·(1−C) pts | Componente clave y razón |
|--:|---|---|--:|--:|--:|--:|--:|---|---|
| 1 | Los Fresnos 1Er Sector | Apodaca | 167 | 7.6 | 4,938 | 0.98 | 0.00 | 0.0·1.6·6.0 | **Anclas***: Anclas* 1.6 pts vs mediana-denso 13.8; Demanda* 0.0 pts vs mediana-denso 10.9; anclas 14.3/1000 viv |
| 2 | Mirador del Parque | Juárez | 164 | 14.4 | 4,292 | 0.89 | 0.02 | 3.2·2.2·9.0 | **Anclas***: Anclas* 2.2 pts vs mediana-denso 13.8; Demanda* 3.2 pts vs mediana-denso 10.9; anclas 15.1/1000 viv |
| 3 | Martires de Cananea | Santa Catarina | 160 | 19.6 | 4,089 | 0.86 | 0.04 | 2.2·3.3·14.1 | **Anclas***: Anclas* 3.3 pts vs mediana-denso 13.8; Demanda* 2.2 pts vs mediana-denso 10.9; anclas 16.3/1000 viv |
| 4 | Sierra Ventana | Monterrey | 136 | 33.3 | 4,777 | 0.95 | 0.19 | 18.1·7.0·8.1 | **(1-Comp*)**: (1-Comp*) 8.1 pts vs mediana-denso 15.5; Anclas* 7.0 pts vs mediana-denso 13.8; 4 competidores<=300m |
| 5 | Constituyentes de Queretaro 4 Sec | San Nicolás de los Garza | 128 | 34.7 | 4,790 | 0.95 | 0.23 | 0.0·4.7·30.0 | **Demanda***: Demanda* 0.0 pts vs mediana-denso 10.9; Anclas* 4.7 pts vs mediana-denso 13.8; pob_eff 15,036, intensidad OVHAC/OVSAE 0.000 (mediana 0.414) |
| 6 | Fomerrey 51 | Monterrey | 152 | 29.1 | 3,928 | 0.80 | 0.09 | 9.4·16.6·3.1 | **(1-Comp*)**: (1-Comp*) 3.1 pts vs mediana-denso 15.5; Demanda* 9.4 pts vs mediana-denso 10.9; 2 competidores<=300m |
| 7 | Lomas del Poniente 1Er Sector | Santa Catarina | 153 | 28.3 | 3,863 | 0.75 | 0.08 | 8.2·19.3·0.7 | **(1-Comp*)**: (1-Comp*) 0.7 pts vs mediana-denso 15.5; Demanda* 8.2 pts vs mediana-denso 10.9; 3 competidores<=300m |
| 8 | Fray Servando Teresa de Mier (Fomerrey 6 ) | Monterrey | 121 | 35.6 | 4,690 | 0.93 | 0.28 | 8.3·23.1·4.2 | **(1-Comp*)**: (1-Comp*) 4.2 pts vs mediana-denso 15.5; Demanda* 8.3 pts vs mediana-denso 10.9; 1 competidores<=300m |
| 9 | Genaro Vazquez Rojas | Monterrey | 154 | 28.2 | 3,805 | 0.73 | 0.08 | 15.6·5.6·7.0 | **(1-Comp*)**: (1-Comp*) 7.0 pts vs mediana-denso 15.5; Anclas* 5.6 pts vs mediana-denso 13.8; 2 competidores<=300m |
| 10 | Francisco Villa | Monterrey | 119 | 35.6 | 4,419 | 0.92 | 0.29 | 20.1·12.1·3.4 | **(1-Comp*)**: (1-Comp*) 3.4 pts vs mediana-denso 15.5; Anclas* 12.1 pts vs mediana-denso 13.8; 4 competidores<=300m |
| 11 | Portal de Vaquerias | Juárez | 165 | 12.2 | 3,473 | 0.63 | 0.01 | 1.7·3.8·6.7 | **Anclas***: Anclas* 3.8 pts vs mediana-denso 13.8; Demanda* 1.7 pts vs mediana-denso 10.9; anclas 16.5/1000 viv |
| 12 | Puerta del Sol | General Escobedo | 100 | 38.6 | 5,131 | 0.99 | 0.40 | 5.7·2.9·30.0 | **Anclas***: Anclas* 2.9 pts vs mediana-denso 13.8; Demanda* 5.7 pts vs mediana-denso 10.9; anclas 15.5/1000 viv |
| 13 | Serranias | General Escobedo | 112 | 36.8 | 4,489 | 0.92 | 0.33 | 3.2·28.6·5.1 | **(1-Comp*)**: (1-Comp*) 5.1 pts vs mediana-denso 15.5; Demanda* 3.2 pts vs mediana-denso 10.9; 1 competidores<=300m |
| 14 | Hacienda Renacimiento | García | 114 | 36.5 | 4,391 | 0.90 | 0.32 | 2.5·4.0·30.0 | **Anclas***: Anclas* 4.0 pts vs mediana-denso 13.8; Demanda* 2.5 pts vs mediana-denso 10.9; anclas 16.5/1000 viv |
| 15 | Carmen Romano | San Nicolás de los Garza | 126 | 35.1 | 4,008 | 0.83 | 0.25 | 10.4·6.9·17.9 | **Anclas***: Anclas* 6.9 pts vs mediana-denso 13.8; Demanda* 10.4 pts vs mediana-denso 10.9; anclas 18.6/1000 viv |

## 2. Score alto pero densidad baja (posible sobrevalorada) — top 15

| # | Colonia | Mun. | Rank base | Score | Viv/km² (Censo) | pct dens | pct score | D·A·(1−C) pts | Componente clave y razón |
|--:|---|---|--:|--:|--:|--:|--:|---|---|
| 1 | Lazaro Cardenas | Monterrey | 17 | 62.4 | 1,150 | 0.07 | 0.90 | 5.3·27.1·30.0 | **(1-Comp*)**: (1-Comp*) 30.0 pts vs mediana-denso 15.5; Anclas* 27.1 pts vs mediana-denso 13.8; 0 competidores<=300m (Comp*=0 si 0) |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 2 | 69.5 | 2,022 | 0.19 | 0.99 | 17.9·21.7·30.0 | **(1-Comp*)**: (1-Comp*) 30.0 pts vs mediana-denso 15.5; Anclas* 21.7 pts vs mediana-denso 13.8; 0 competidores<=300m (Comp*=0 si 0) |
| 3 | Pueblo Nuevo 1Er Sector | Apodaca | 6 | 66.8 | 2,058 | 0.21 | 0.97 | 6.8·30.0·30.0 | **Anclas***: Anclas* 30.0 pts vs mediana-denso 13.8; (1-Comp*) 30.0 pts vs mediana-denso 15.5 |
| 4 | Union Modelo | Guadalupe | 24 | 59.7 | 1,653 | 0.14 | 0.86 | 3.7·26.0·30.0 | **(1-Comp*)**: (1-Comp*) 30.0 pts vs mediana-denso 15.5; Anclas* 26.0 pts vs mediana-denso 13.8; 0 competidores<=300m (Comp*=0 si 0) |
| 5 | Pueblo Nuevo 4To Sector | Apodaca | 5 | 67.0 | 2,162 | 0.26 | 0.98 | 7.9·29.1·30.0 | **Anclas***: Anclas* 29.1 pts vs mediana-denso 13.8; (1-Comp*) 30.0 pts vs mediana-denso 15.5 |
| 6 | Riveras del Rio | Monterrey | 33 | 54.8 | 1,415 | 0.09 | 0.81 | 34.0·5.1·15.7 | **Demanda***: Demanda* 34.0 pts vs mediana-denso 10.9; (1-Comp*) 15.7 pts vs mediana-denso 15.5 |
| 7 | Paseo de San Bernabe | Monterrey | 35 | 54.1 | 1,516 | 0.10 | 0.80 | 9.6·14.5·30.0 | **(1-Comp*)**: (1-Comp*) 30.0 pts vs mediana-denso 15.5; Anclas* 14.5 pts vs mediana-denso 13.8; 0 competidores<=300m (Comp*=0 si 0) |
| 8 | Croc | Monterrey | 4 | 68.7 | 2,318 | 0.30 | 0.98 | 40.0·11.2·17.5 | **Demanda***: Demanda* 40.0 pts vs mediana-denso 10.9; (1-Comp*) 17.5 pts vs mediana-denso 15.5 |
| 9 | Emiliano Zapata | Monterrey | 32 | 54.9 | 1,582 | 0.13 | 0.81 | 5.2·19.7·30.0 | **(1-Comp*)**: (1-Comp*) 30.0 pts vs mediana-denso 15.5; Anclas* 19.7 pts vs mediana-denso 13.8; 0 competidores<=300m (Comp*=0 si 0) |
| 10 | Monte Kristal | Juárez | 48 | 50.8 | 816 | 0.04 | 0.72 | 24.1·18.4·8.3 | **Demanda***: Demanda* 24.1 pts vs mediana-denso 10.9; Anclas* 18.4 pts vs mediana-denso 13.8 |
| 11 | San Miguel Residencial | General Escobedo | 3 | 69.5 | 2,485 | 0.36 | 0.99 | 35.1·4.3·30.0 | **Demanda***: Demanda* 35.1 pts vs mediana-denso 10.9; (1-Comp*) 30.0 pts vs mediana-denso 15.5 |
| 12 | La Playa | Guadalupe | 11 | 65.0 | 2,409 | 0.33 | 0.94 | 5.2·29.8·30.0 | **Anclas***: Anclas* 29.8 pts vs mediana-denso 13.8; (1-Comp*) 30.0 pts vs mediana-denso 15.5 |
| 13 | Niño Artillero | Monterrey | 53 | 49.6 | 1,464 | 0.10 | 0.69 | 13.4·26.2·9.9 | **Anclas***: Anclas* 26.2 pts vs mediana-denso 13.8; Demanda* 13.4 pts vs mediana-denso 10.9 |
| 14 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 9 | 65.7 | 2,527 | 0.37 | 0.95 | 6.0·29.6·30.0 | **Anclas***: Anclas* 29.6 pts vs mediana-denso 13.8; (1-Comp*) 30.0 pts vs mediana-denso 15.5 |
| 15 | Rancho Viejo | Juárez | 68 | 46.6 | 740 | 0.03 | 0.60 | 21.1·25.3·0.2 | **Anclas***: Anclas* 25.3 pts vs mediana-denso 13.8; Demanda* 21.1 pts vs mediana-denso 10.9 |

## 3. Lectura

- **Score y densidad casi no se parecen** (Spearman 0.05): el score no premia densidad por diseño. Demanda* = `pob_eff` × intensidad (0.85·OVHAC + 0.15·OVSAE, min-max) y Anclas*/Comp* están por 1 000 viv. del colonia, no por km².
- Subvaloradas: 12/15 tienen Demanda* bajo la mediana del cuartil denso. De esas, 10 tienen `pob_eff` < mediana de las 167 (colonia chica en habitantes) y 12 tienen intensidad OVHAC/OVSAE < mediana (hogares con poco hacinamiento / agua entubada). Es decir: densidad alta en polígonos pequeños + intensidad baja. Si Nicolás cree que densidad ≈ recarga (SUPUESTO, sin dato de ventas), son candidatas a revisar en campo; **no** se cambia el score.
- Sobrevaloradas: 10/15 tienen 0 competidores ≤300 m (reciben 30/30 pts de (1−Comp*)) — ver `docs/COMPETENCIA_CERO.md`: el 0 es poco confiable; varias tienen además Anclas* alta (por 1 000 viv.; SUPUESTO: un denominador de viviendas chico infla la razón).
- Limitación: viviendas/km² usa el área total del polígono CONAPO (incluye lotes baldíos/industria/cerros); colonias pequeñas tienen densidad ruidosa. Viv. Censo = MODELO por traslape de áreas con AGEB.
