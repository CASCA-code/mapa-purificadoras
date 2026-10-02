# Sensibilidad de densidad de viviendas + banda de confianza del ranking v3 base

**Etiqueta: MODELO.** Es un análisis de sensibilidad del ranking, **no un pronóstico** ni un intervalo estadístico: los rangos p10–p90 sólo dicen cuánto se mueve una colonia si cambian los supuestos listados. No altera `colonias_v3.csv`, el hub ni el mapa. Fecha: 2026-10-02.

- Scripts: `scripts/banda_confianza_densidad.py` (cálculo, semilla fija, sin red) y `scripts/doc_banda_confianza.py` (este documento).
- Salidas nuevas: `v2/data/colonias_v3_sensibilidad_densidad.csv` (167 filas) y `v2/data/colonias_v3_banda_confianza.csv` (167 filas).
- Entradas (sólo lectura): `v2/data/colonias_v3.csv`, `data/colonias.geojson` (pob exacta), `/home/box/geo/inegi_purificador/datos/colonias167_viv_censo_ponderado_por_AGEB_MODELO.csv` (viviendas habitadas Censo 2020 por traslape de área colonia–AGEB, MODELO), `…/colonias167_conapo_geom.geojson` (`area_km2` del polígono CONAPO).
- Reproducción del base con `pob/3.6`: dif. máx. de score 0.005 pts y 0 rangos distintos (procedimiento validado).

## 1. Variante `score_base_dens`: término de densidad de viviendas

`Dens*` = rango percentil (0–1, misma convención que A* y C*) de **viviendas habitadas Censo por hectárea** = `viv_hab_censo_est / (area_km2·100)`. Se añade con peso `w`:

```text
score_dens = 100·( wD'·D* + wA'·A* + 0.30·(1−C*) + w·Dens* )
modo DA (principal): w sale de Demanda y Anclas en proporción a su peso:  wD' = 0.40 − w·0.40/0.70 ,  wA' = 0.30 − w·0.30/0.70 ;  Competencia queda en 0.30
modo ALL (robustez): w sale de los tres componentes en proporción (×(1−w))
```

A* y C* siguen con `pob/3.6` (idénticos al base); sólo cambia el término nuevo y el reparto de pesos.

| Modo | w dens | pesos D′/A′/C′ | Spearman score | Spearman rango | Top-10 en común | Top-30 en común | Colonias que se mueven >10 rangos | Mov. mediano / máx. (rangos) |
|---|--:|---|--:|--:|--:|--:|--:|--:|
| DA | 0.05 | 0.371/0.279/0.300 | 0.989 | 0.989 | 9/10 | 29/30 | 21 | 4 / 24 |
| DA | 0.10 | 0.343/0.257/0.300 | 0.964 | 0.964 | 6/10 | 27/30 | 64 | 8 / 40 |
| DA | 0.20 | 0.286/0.214/0.300 | 0.880 | 0.880 | 5/10 | 24/30 | 109 | 16 / 71 |
| DA | 0.30 | 0.229/0.171/0.300 | 0.757 | 0.757 | 3/10 | 18/30 | 128 | 21 / 100 |
| ALL | 0.10 | 0.360/0.270/0.270 | 0.965 | 0.965 | 7/10 | 26/30 | 71 | 9 / 34 |
| ALL | 0.20 | 0.320/0.240/0.240 | 0.865 | 0.865 | 4/10 | 24/30 | 115 | 17 / 59 |

Contexto: la densidad casi no se parece al score base (Spearman densidad vs `score_base` = 0.05); por eso un peso alto reordena mucho. Spearman bajo = la densidad *cambia* el ranking, no que sea «mejor» o «peor»: sin ventas reales no hay criterio para decir que más densidad = más recarga (SUPUESTO).

### Top-10 con w=0.10 (modo DA): entran / salen

| Rango dens | Colonia | Rango base | Score dens | Viv/ha |
|--:|---|--:|--:|--:|
| 1 | Ampliacion Municipal (Monterrey) | 1 | 76.8 | 45.1 |
| 2 | Gloria Mendiola (Monterrey) | 8 | 69.3 | 41.5 |
| 3 | Paseo de Las Minas (Santa Catarina) | 13 | 67.5 | 40.3 |
| 4 | San Miguel Residencial (General Escobedo) | 3 | 67.4 | 24.9 |
| 5 | Paseo del Nogalar (San Nicolás de los Garza) | 14 | 66.9 | 39.7 |
| 6 | Rincon de Las Mitras (Fomerrey 2) (Santa Catarina) | 10 | 66.7 | 35.8 |
| 7 | Fomerrey 35 (Tierra Propia) (Monterrey) | 16 | 66.2 | 39.8 |
| 8 | Fomerrey 24 (Monterrey) | 7 | 66.1 | 30.6 |
| 9 | Fomerrey 112 (San Bernabe 9) (Monterrey) | 2 | 65.8 | 20.2 |
| 10 | Villas de San Francisco (General Escobedo) | 23 | 64.8 | 43.9 |

- Entran: Villas de San Francisco (#23→#10), Fomerrey 35 (Tierra Propia) (#16→#7), Paseo del Nogalar (#14→#5), Paseo de Las Minas (#13→#3).
- Salen: Pueblo Nuevo 1Er Sector (#6→#15), Pueblo Nuevo 4To Sector (#5→#13), Croc (#4→#12), Floridos Bosques del Nogalar (#9→#14).

### Top-10 con w=0.20 (modo DA): entran / salen

| Rango dens | Colonia | Rango base | Score dens | Viv/ha |
|--:|---|--:|--:|--:|
| 1 | Ampliacion Municipal (Monterrey) | 1 | 79.8 | 45.1 |
| 2 | Gloria Mendiola (Monterrey) | 8 | 72.9 | 41.5 |
| 3 | Paseo de Las Minas (Santa Catarina) | 13 | 71.0 | 40.3 |
| 4 | Paseo del Nogalar (San Nicolás de los Garza) | 14 | 70.3 | 39.7 |
| 5 | Fomerrey 35 (Tierra Propia) (Monterrey) | 16 | 69.8 | 39.8 |
| 6 | Villas de San Francisco (General Escobedo) | 23 | 69.6 | 43.9 |
| 7 | Rincon de Las Mitras (Fomerrey 2) (Santa Catarina) | 10 | 68.3 | 35.8 |
| 8 | Fomerrey 23 ( Laderas de Topo Chico) (Monterrey) | 18 | 67.5 | 38.5 |
| 9 | Fomerrey 24 (Monterrey) | 7 | 65.9 | 30.6 |
| 10 | San Miguel Residencial (General Escobedo) | 3 | 65.3 | 24.9 |

- Entran: Villas de San Francisco (#23→#6), Fomerrey 23 ( Laderas de Topo Chico) (#18→#8), Fomerrey 35 (Tierra Propia) (#16→#5), Paseo del Nogalar (#14→#4), Paseo de Las Minas (#13→#3).
- Salen: Pueblo Nuevo 1Er Sector (#6→#28), Pueblo Nuevo 4To Sector (#5→#22), Croc (#4→#30), Fomerrey 112 (San Bernabe 9) (#2→#21), Floridos Bosques del Nogalar (#9→#17).

**Lectura (MODELO):** con w=0.05 el ranking casi no cambia (9/10 top-10); con 0.10 ya sale Croc del top-10 (#4→#12; su densidad está en el percentil ~0.30 de las 167, ver `docs/GAPS_RATING_DENSIDAD.md`), y con 0.20 el top-10 se queda con 5 de 10. Es decir, el top-10 del base **no es robusto a que Nicolás decida que la densidad importa**; el top-30 sí aguanta w≤0.10 (27/30). No se recomienda aplicar nada sin dato de ventas: ver `docs/GAPS_RATING_DENSIDAD.md` (no se repite aquí).

## 2. Banda de confianza por colonia (Monte-Carlo de sensibilidad)

**Método.** 4,000 sorteos (semilla 20261002); en cada sorteo se recalcula el `score_base` de las 167 colonias y su rango (1 = mejor) con estas perturbaciones independientes:

1. **Pesos** (0.40/0.30/0.30): cada uno × U(0.7, 1.3) y se renormaliza a suma 1 (±30 %).
2. **Viviendas**: por colonia, `viv = viv_Censo + u·(viv_pob/3.6 − viv_Censo)`, u~U(0,1) (cubre el rango entre las dos estimaciones; afecta A* y C*, que van por 1 000 viv.).
3. **Competencia = 0 tratada como desconocida** (58 colonias): su tasa de competidores/1 000 viv. se sortea de la distribución empírica de las tasas observadas en las 167 colonias (incluye ceros, SUPUESTO de que un 0 puede ser real o hueco de datos; ver `docs/COMPETENCIA_CERO.md`). Las colonias con ≥1 competidor no se perturban.
- Salida por colonia: `rank_p10`, `rank_p50`, `rank_p90`, `ancho_banda = p90−p10`, `prob_top10`, `prob_top30` (fracción de sorteos). Columnas `*_estres`: misma simulación pero la tasa de los ceros se sortea sólo entre colonias con ≥1 competidor (supuesto más duro: «el 0 siempre es hueco»).
- **Etiqueta `confianza`** (reglas fijas, definidas antes de ver resultados por colonia): banda **estrecha** ancho ≤30 rangos (2 pts), **media** 31–60 (1 pt), **ancha** >60 (0 pts); se resta 1 pt si **no hay ninguna marca Scout** en la colonia (`cobertura_campo = sin encuesta`). 2 pts = **alta**, 1 = **media**, 0 = **baja**. Los umbrales 30/60 son de juicio (~18 % y ~36 % de las 167 colonias), no estadísticos.

### Resultado

- Ancho p90−p10: mediana **32** rangos, media 48, rango 1–120. Bandas: estrecha 78, media 37, ancha 52.
- Confianza: **alta 8**, media 74, **baja 85** (de 167). Alta exige banda estrecha **y** al menos 1 marca Scout; Scout cubre sólo 17 de 167 colonias, por eso casi todas caen en media/baja por cobertura, no sólo por sensibilidad.
- **Los 58 ceros de competencia dominan la incertidumbre:** ancho medio 97 rangos (mediana 102) en las 58 vs 22 (mediana 21) en las otras 109.
- Qué fuente aporta más ancho (mismos sorteos, sólo una perturbación a la vez; ancho p90−p10 por colonia):

| Perturbación activa | Ancho mediano | Ancho medio | Ancho máx. |
|---|--:|--:|--:|
| sólo pesos ±30 % | 19 | 21 | 54 |
| sólo viviendas (Censo↔pob/3.6) | 6 | 7 | 35 |
| sólo competencia 0 = desconocida | 10 | 39 | 120 |
| las tres | 32 | 49 | 121 |

Las viviendas (Censo vs pob/3.6) son la fuente menor; pesos pesan más; el 0 de competencia es la mayor (media 39, máx. 120 rangos; sólo afecta a las 58 colonias con 0).

### Top-30 del base: banda y confianza (3 alta · 2 media · 25 baja)

| Rango base | Colonia | Municipio | p10 | p50 | p90 | P(top-30) | P(top-30) estrés | Competidores ≤300 m | Marcas Scout | Confianza |
|--:|---|---|--:|--:|--:|--:|--:|--:|--:|---|
| 1 | Ampliacion Municipal | Monterrey | 1 | 7 | 52 | 0.77 | 0.70 | 0 | 1 | media |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 2 | 12 | 62 | 0.71 | 0.61 | 0 | 0 | baja |
| 3 | San Miguel Residencial | General Escobedo | 3 | 15 | 77 | 0.65 | 0.54 | 0 | 22 | baja |
| 4 | Croc | Monterrey | 1 | 1 | 2 | 1.00 | 1.00 | 3 | 88 | alta |
| 5 | Pueblo Nuevo 4To Sector | Apodaca | 3 | 19 | 84 | 0.60 | 0.47 | 0 | 0 | baja |
| 6 | Pueblo Nuevo 1Er Sector | Apodaca | 4 | 19 | 86 | 0.60 | 0.46 | 0 | 0 | baja |
| 7 | Fomerrey 24 | Monterrey | 4 | 19 | 87 | 0.60 | 0.44 | 0 | 1 | baja |
| 8 | Gloria Mendiola | Monterrey | 5 | 21 | 89 | 0.58 | 0.46 | 0 | 6 | baja |
| 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 5 | 22 | 92 | 0.57 | 0.40 | 0 | 0 | baja |
| 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 5 | 21 | 90 | 0.59 | 0.44 | 0 | 0 | baja |
| 11 | La Playa | Guadalupe | 6 | 23 | 93 | 0.56 | 0.39 | 0 | 0 | baja |
| 12 | San Bernabe 1Er Sector | Monterrey | 2 | 3 | 5 | 1.00 | 1.00 | 2 | 0 | media |
| 13 | Paseo de Las Minas | Santa Catarina | 6 | 23 | 96 | 0.57 | 0.41 | 0 | 0 | baja |
| 14 | Paseo del Nogalar | San Nicolás de los Garza | 7 | 27 | 99 | 0.53 | 0.36 | 0 | 0 | baja |
| 15 | Miguel Hidalgo | Guadalupe | 9 | 29 | 108 | 0.51 | 0.32 | 0 | 0 | baja |
| 16 | Fomerrey 35 (Tierra Propia) | Monterrey | 8 | 29 | 106 | 0.51 | 0.34 | 0 | 0 | baja |
| 17 | Lazaro Cardenas | Monterrey | 9 | 32 | 110 | 0.49 | 0.31 | 0 | 0 | baja |
| 18 | Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 8 | 32 | 108 | 0.49 | 0.33 | 0 | 5 | baja |
| 19 | Fomerrey 115 (San Bernabe 12) | Monterrey | 10 | 35 | 111 | 0.47 | 0.30 | 0 | 0 | baja |
| 20 | Indeco La Fama 1 | Santa Catarina | 11 | 38 | 119 | 0.45 | 0.23 | 0 | 0 | baja |
| 21 | Fomerrey 114 (San Bernabe 13) | Monterrey | 10 | 35 | 116 | 0.47 | 0.29 | 0 | 0 | baja |
| 22 | Unidad Piloto | Guadalupe | 10 | 35 | 114 | 0.47 | 0.27 | 0 | 0 | baja |
| 23 | Villas de San Francisco | General Escobedo | 12 | 42 | 126 | 0.41 | 0.23 | 0 | 1 | baja |
| 24 | Union Modelo | Guadalupe | 14 | 46 | 127 | 0.40 | 0.18 | 0 | 0 | baja |
| 25 | Nuevo Leon Estado de Progreso (Alianza Real) | General Escobedo | 3 | 5 | 13 | 1.00 | 1.00 | 1 | 3 | alta |
| 26 | Moctezuma | Monterrey | 16 | 45 | 128 | 0.40 | 0.19 | 0 | 0 | baja |
| 27 | Villas de San Jose 7 Sector | Juárez | 16 | 48 | 131 | 0.37 | 0.16 | 0 | 0 | baja |
| 28 | Topo Chico | Monterrey | 6 | 9 | 14 | 1.00 | 1.00 | 1 | 18 | alta |
| 29 | 25 de Noviembre | Guadalupe | 18 | 53 | 134 | 0.34 | 0.14 | 0 | 0 | baja |
| 30 | Rene Alvarez | Monterrey | 19 | 56 | 136 | 0.32 | 0.12 | 0 | 0 | baja |

### Colonias con confianza alta (8)

«Alta» = el **rango es estable** bajo estos supuestos y hay algo de campo; **no** significa que la colonia sea buena (p. ej. Fomerrey 113 es estable en el rango ~93–122).

| Rango base | Colonia | Municipio | p10–p90 | Marcas Scout | Competidores ≤300 m |
|--:|---|---|---|--:|--:|
| 4 | Croc | Monterrey | 1–2 | 88 | 3 |
| 25 | Nuevo Leon Estado de Progreso (Alianza Real) | General Escobedo | 3–13 | 3 | 1 |
| 28 | Topo Chico | Monterrey | 6–14 | 18 | 1 |
| 31 | Fomerrey 1 ( Reforma ) | Monterrey | 7–14 | 5 | 1 |
| 63 | El Porvenir | Monterrey | 27–42 | 4 | 1 |
| 79 | Pedregal del Topo Chico [19021_0183] | General Escobedo | 34–57 | 1 | 1 |
| 80 | Valle de Santa Lucia (Granja Sanitaria) | Monterrey | 46–70 | 2 | 5 |
| 133 | Fomerrey 113 (San Bernabe 9) | Monterrey | 93–122 | 6 | 3 |

### Top-12 por mediana de rango (p50) bajo los supuestos

| p50 | Colonia | Municipio | Rango base | p10–p90 | Competidores ≤300 m | Marcas Scout | Confianza |
|--:|---|---|--:|---|--:|--:|---|
| 1 | Croc | Monterrey | 4 | 1–2 | 3 | 88 | alta |
| 3 | San Bernabe 1Er Sector | Monterrey | 12 | 2–5 | 2 | 0 | media |
| 5 | Nuevo Leon Estado de Progreso (Alianza Real) | General Escobedo | 25 | 3–13 | 1 | 3 | alta |
| 7 | Ampliacion Municipal | Monterrey | 1 | 1–52 | 0 | 1 | media |
| 9 | Topo Chico | Monterrey | 28 | 6–14 | 1 | 18 | alta |
| 10 | Fomerrey 1 ( Reforma ) | Monterrey | 31 | 7–14 | 1 | 5 | alta |
| 12 | Fomerrey 112 (San Bernabe 9) | Monterrey | 2 | 2–62 | 0 | 0 | baja |
| 15 | San Miguel Residencial | General Escobedo | 3 | 3–77 | 0 | 22 | baja |
| 15 | Riveras del Rio | Monterrey | 33 | 6–26 | 2 | 0 | media |
| 15 | Fama Iii | Santa Catarina | 38 | 11–21 | 1 | 0 | media |
| 16 | Fomerrey 110 (San Bernabe 15) | Monterrey | 34 | 11–22 | 1 | 0 | media |
| 19 | Pueblo Nuevo 4To Sector | Apodaca | 5 | 3–84 | 0 | 0 | baja |

Lectura: si los ceros de competencia son inciertos, suben las colonias que ya tienen ≥1 competidor *medido* y buen resto de componentes (Croc, San Bernabe 1er Sector, Alianza Real, Topo Chico…); las del top-10 base con 0 competidores bajan en la mediana pero conservan p10 alto (pueden seguir siendo top si el 0 es real). MODELO; no es veredicto.

## 3. Lectura y límites

- De los 10 primeros del base, **8** tienen confianza **baja**: están arriba justamente por tener 0 competidores detectados (Comp\*=0 → 30 pts). Si ese 0 fuera un hueco de datos, bajo estos supuestos su p90 llega a los rangos ~50–90. Sólo Croc (#4, 88 marcas Scout, 3 competidores ≤300 m) es sólido: p10–p90 = 1–2.
- Esto **refuerza** lo ya dicho en `docs/COMPETENCIA_CERO.md` y `docs/V2_VS_V3.md`: el top del v3 base es un filtro para decidir dónde mirar, no un orden fino. Sirve para priorizar visitas Scout (mayor ancho × mejor p50 = más valor de verificar), no para elegir sitio.
- `prob_*` es la fracción de sorteos bajo estos supuestos, **no una probabilidad de éxito comercial**. Captura 3 % y 2 garr/viv/sem siguen siendo supuestos aparte.
- No se perturbaron: anclas ponderadas, pesos por categoría de ancla, Demanda\* (CONAPO/IMC), ni la geometría (traslape colonia–AGEB, buffers 100/300 m). La banda real es por tanto un **piso**.
- Rangos p10/p50/p90 se redondean a entero; el rango base usa desempate estable por fila.
