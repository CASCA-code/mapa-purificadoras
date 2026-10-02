# Competencia cero: 58 colonias sin competidores ≤300 m

Etiqueta: **heurística con evidencia** (conteos de archivos locales); no es verdad de campo y **no altera ningún score** (`v2/data/colonias_v3.csv` intacto). Script: `scripts/analisis_competencia_cero.py` (sin red). Tabla completa: `v2/data/colonias_competencia_cero.csv` (58 filas).

## 1. Qué es el «0»

- v3 base cuenta purificadoras dentro del polígono+300 m (DENUE 312112 filtrado + Places, dedupe 30 m). **58 de 167** colonias dan 0 → Comp\*=0 → reciben los 30 pts completos de «(1−Comp)». Con marcas Scout bajan a **51**: Scout encontró competidores ≤300 m en **7** de estas 58 que DENUE/Places no veían (esa es la evidencia directa de brecha de datos).
- Tasa media de detección (todas las colonias): **1.00 competidores ≤300 m por 1 000 viv.** Si una colonia tuviera esa tasa, la probabilidad de observar 0 es `exp(−tasa×viv/1000)` (columna `p_cero_si_tasa_media`). Para colonias grandes, un 0 es poco creíble.
- **Chequeo global:** con esa tasa homogénea se esperarían **65** colonias con 0 y se observan **58**. Es decir, el número de ceros **no es mayor** que el que produce una detección escasa pero pareja: no hay prueba estadística de que el conjunto sea un hueco de datos; el problema es que la tasa misma (1 por 1 000 viv.) es un piso (informales invisibles), así que los 0 individuales no son confiables.
- DENUE ve 93 formales; informales no se ven; Places trae máx. 60 por búsqueda/tile (ver `docs/RATING_V3.md` §4).

## 2. Regla de clasificación (transparente)

1. **brecha_confirmada_por_scout**: Scout marcó purificadora ≤300 m.
2. **brecha_probable**: ≥3 señales de brecha y más que las de «real». Señales de brecha: p(0)≤0.15; comercio de barrio (abarrotes+Oxxo+tortillerías)/1 000 viv ≥ mediana de las 167 (38); competidor a ≤600 m del borde; puntos DENUE/Places ≤300 m descartados (industrial/marca); sin puntos de Places o DENUE en la zona.
3. **cero_real_probable**: ≥3 señales de «real»: p(0)≥0.40; ningún competidor ≤1 km; Scout ≥10 marcas sin purificadora; comercio bajo con cobertura DENUE+Places.
4. **indeterminado_inclina_brecha / _inclina_real**: 2 señales de un lado y más que del otro. **indeterminado**: el resto → verificar en campo.

«Real» sólo significa «sin evidencia de que falte dato»; ninguna categoría prueba que no haya competencia informal.

## 3. Resultado

| Clasificación | Colonias |
|---|--:|
| brecha_confirmada_por_scout | 7 |
| brecha_probable | 4 |
| indeterminado_inclina_brecha | 21 |
| indeterminado | 13 |
| indeterminado_inclina_real | 12 |
| cero_real_probable | 1 |

En el **top-30 del ranking base** hay **26** de estas colonias: Ampliacion Municipal (#1, indeterminado_inclina_brecha), Fomerrey 112 (San Bernabe 9) (#2, brecha_confirmada_por_scout), San Miguel Residencial (#3, brecha_confirmada_por_scout), Pueblo Nuevo 4To Sector (#5, indeterminado_inclina_brecha), Pueblo Nuevo 1Er Sector (#6, indeterminado_inclina_brecha), Fomerrey 24 (#7, brecha_confirmada_por_scout), Gloria Mendiola (#8, indeterminado_inclina_brecha), Floridos Bosques del Nogalar (#9, indeterminado_inclina_brecha), Rincon de Las Mitras (Fomerrey 2) (#10, indeterminado), La Playa (#11, indeterminado_inclina_brecha), Paseo de Las Minas (#13, brecha_probable), Paseo del Nogalar (#14, indeterminado_inclina_brecha), Miguel Hidalgo (#15, indeterminado_inclina_brecha), Fomerrey 35 (Tierra Propia) (#16, brecha_probable), Lazaro Cardenas (#17, brecha_confirmada_por_scout), Fomerrey 23 ( Laderas de Topo Chico) (#18, brecha_confirmada_por_scout), Fomerrey 115 (San Bernabe 12) (#19, indeterminado_inclina_brecha), Indeco La Fama 1 (#20, indeterminado_inclina_brecha), Fomerrey 114 (San Bernabe 13) (#21, brecha_probable), Unidad Piloto (#22, indeterminado), Villas de San Francisco (#23, brecha_confirmada_por_scout), Union Modelo (#24, indeterminado_inclina_brecha), Moctezuma (#26, indeterminado_inclina_brecha), Villas de San Jose 7 Sector (#27, indeterminado), 25 de Noviembre (#29, indeterminado_inclina_real), Rene Alvarez (#30, indeterminado).

Cobertura de fuentes (puntos en polígono+100 m): sin ningún punto DENUE: 0; sin Places: 11; sin OSM: 16. Colonias con competidor a ≤600 m del borde: 35; sin competidor ≤1 km: 5.

## 4. Las 58 colonias

| # base | Colonia | Municipio | Viv. | Anclas pond. | Abarr./Oxxo/Tort. | DENUE / Places / OSM (pts) | Comp. más cercano (m) | p(0) | Scout (marcas · comp.) | Clasificación |
|--:|---|---|--:|--:|---|---|--:|--:|---|---|
| 1 | Ampliacion Municipal | Monterrey | 534 | 21.8 | 30/0/7 | 45 / 9 / 0 | 442 | 0.59 | 1 · 0 | indeterminado_inclina_brecha |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 1055 | 31.8 | 52/0/4 | 76 / 0 / 4 | 528 | 0.35 | 0 · 1 | brecha_confirmada_por_scout |
| 3 | San Miguel Residencial | General Escobedo | 3443 | 58.0 | 88/1/6 | 108 / 32 / 3 | 389 | 0.03 | 22 · 3 | brecha_confirmada_por_scout |
| 5 | Pueblo Nuevo 4To Sector | Apodaca | 805 | 40.5 | 42/0/8 | 62 / 20 / 23 | 311 | 0.45 | 0 · 0 | indeterminado_inclina_brecha |
| 6 | Pueblo Nuevo 1Er Sector | Apodaca | 438 | 28.3 | 37/0/8 | 50 / 13 / 1 | 555 | 0.65 | 0 · 0 | indeterminado_inclina_brecha |
| 7 | Fomerrey 24 | Monterrey | 481 | 19.7 | 33/1/2 | 43 / 1 / 2 | 594 | 0.62 | 1 · 1 | brecha_confirmada_por_scout |
| 8 | Gloria Mendiola | Monterrey | 1902 | 39.9 | 74/0/7 | 98 / 7 / 0 | 680 | 0.15 | 6 · 0 | indeterminado_inclina_brecha |
| 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 484 | 25.1 | 37/0/5 | 50 / 4 / 4 | 462 | 0.62 | 0 · 0 | indeterminado_inclina_brecha |
| 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 1063 | 30.6 | 41/0/6 | 58 / 13 / 2 | 764 | 0.35 | 0 · 0 | indeterminado |
| 11 | La Playa | Guadalupe | 421 | 25.1 | 31/1/5 | 41 / 12 / 4 | 361 | 0.66 | 0 · 0 | indeterminado_inclina_brecha |
| 13 | Paseo de Las Minas | Santa Catarina | 696 | 16.6 | 36/0/1 | 42 / 0 / 1 | 535 | 0.50 | 0 · 0 | brecha_probable |
| 14 | Paseo del Nogalar | San Nicolás de los Garza | 1087 | 34.4 | 44/0/9 | 62 / 8 / 5 | 423 | 0.34 | 0 · 0 | indeterminado_inclina_brecha |
| 15 | Miguel Hidalgo | Guadalupe | 690 | 23.4 | 33/0/4 | 43 / 5 / 3 | 541 | 0.50 | 0 · 0 | indeterminado_inclina_brecha |
| 16 | Fomerrey 35 (Tierra Propia) | Monterrey | 1996 | 52.5 | 78/0/6 | 103 / 12 / 4 | 341 | 0.14 | 0 · 0 | brecha_probable |
| 17 | Lazaro Cardenas | Monterrey | 507 | 19.1 | 24/1/5 | 33 / 9 / 0 | 1116 | 0.60 | 0 · 1 | brecha_confirmada_por_scout |
| 18 | Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 561 | 19.6 | 27/1/3 | 36 / 4 / 2 | 592 | 0.57 | 5 · 1 | brecha_confirmada_por_scout |
| 19 | Fomerrey 115 (San Bernabe 12) | Monterrey | 1115 | 27.1 | 44/0/3 | 61 / 9 / 2 | 320 | 0.33 | 0 · 0 | indeterminado_inclina_brecha |
| 20 | Indeco La Fama 1 | Santa Catarina | 463 | 18.4 | 18/0/3 | 24 / 13 / 5 | 426 | 0.63 | 0 · 0 | indeterminado_inclina_brecha |
| 21 | Fomerrey 114 (San Bernabe 13) | Monterrey | 798 | 20.1 | 36/0/3 | 47 / 0 / 2 | 598 | 0.45 | 0 · 0 | brecha_probable |
| 22 | Unidad Piloto | Guadalupe | 979 | 22.0 | 45/0/1 | 55 / 3 / 1 | 627 | 0.38 | 0 · 0 | indeterminado |
| 23 | Villas de San Francisco | General Escobedo | 3656 | 42.0 | 62/2/6 | 83 / 26 / 1 | 862 | 0.03 | 1 · 1 | brecha_confirmada_por_scout |
| 24 | Union Modelo | Guadalupe | 489 | 17.4 | 16/0/4 | 22 / 7 / 4 | 579 | 0.61 | 0 · 0 | indeterminado_inclina_brecha |
| 26 | Moctezuma | Monterrey | 671 | 20.8 | 27/2/1 | 32 / 7 / 5 | 313 | 0.51 | 0 · 0 | indeterminado_inclina_brecha |
| 27 | Villas de San Jose 7 Sector | Juárez | 465 | 15.1 | 17/2/4 | 25 / 8 / 0 | 746 | 0.63 | 0 · 0 | indeterminado |
| 29 | 25 de Noviembre | Guadalupe | 809 | 21.1 | 22/1/2 | 27 / 11 / 2 | 604 | 0.45 | 0 · 0 | indeterminado_inclina_real |
| 30 | Rene Alvarez | Monterrey | 448 | 10.8 | 24/0/1 | 28 / 2 / 0 | 615 | 0.64 | 0 · 0 | indeterminado |
| 32 | Emiliano Zapata | Monterrey | 596 | 16.6 | 17/2/4 | 29 / 9 / 0 | 623 | 0.55 | 0 · 0 | indeterminado |
| 35 | Paseo de San Bernabe | Monterrey | 567 | 13.6 | 22/0/0 | 23 / 7 / 1 | 466 | 0.57 | 0 · 0 | indeterminado_inclina_brecha |
| 36 | Eugenio Canavati | Santa Catarina | 453 | 10.6 | 22/0/0 | 27 / 2 / 1 | 749 | 0.64 | 0 · 0 | indeterminado |
| 37 | Pueblo Nuevo 3Er Sector | Apodaca | 1680 | 28.6 | 42/0/5 | 54 / 5 / 4 | 455 | 0.19 | 0 · 0 | indeterminado |
| 39 | Cerro de Las Mitras (Raul Salinas Lozano) | Santa Catarina | 438 | 10.2 | 23/0/0 | 27 / 0 / 1 | 792 | 0.65 | 0 · 0 | indeterminado_inclina_brecha |
| 40 | Azteca | San Nicolás de los Garza | 899 | 22.1 | 29/0/3 | 38 / 0 / 8 | 318 | 0.41 | 0 · 0 | indeterminado_inclina_brecha |
| 41 | Constituyentes del 57 | Monterrey | 832 | 19.5 | 30/0/3 | 42 / 1 / 4 | 320 | 0.43 | 0 · 0 | indeterminado_inclina_brecha |
| 42 | Fernando Amilpa | General Escobedo | 2497 | 43.3 | 62/1/7 | 84 / 16 / 2 | 925 | 0.08 | 0 · 0 | indeterminado |
| 43 | Argentina | Monterrey | 462 | 11.8 | 20/0/1 | 25 / 0 / 3 | 358 | 0.63 | 0 · 0 | brecha_probable |
| 46 | Vicente Guerrero | Guadalupe | 649 | 17.4 | 21/0/3 | 26 / 4 / 6 | 474 | 0.52 | 0 · 0 | indeterminado_inclina_real |
| 47 | Cimas de Las Mitras (Ampl Raul Salinas Lozano) | Santa Catarina | 522 | 10.4 | 23/0/1 | 28 / 0 / 0 | 897 | 0.59 | 0 · 0 | indeterminado_inclina_brecha |
| 50 | Libertadores de America | Monterrey | 710 | 12.8 | 29/0/1 | 32 / 2 / 0 | 765 | 0.49 | 0 · 1 | brecha_confirmada_por_scout |
| 51 | Hector Caballero | Juárez | 1144 | 22.6 | 36/1/2 | 41 / 10 / 0 | 527 | 0.32 | 0 · 0 | indeterminado |
| 52 | Los Valles 2Do Sector | Juárez | 474 | 11.0 | 20/0/0 | 24 / 2 / 0 | 327 | 0.62 | 0 · 0 | indeterminado_inclina_brecha |
| 55 | Vicente Guerrero 3 Sector | San Nicolás de los Garza | 2053 | 40.1 | 54/0/6 | 77 / 6 / 7 | 334 | 0.13 | 0 · 0 | indeterminado_inclina_brecha |
| 56 | Nuevo Almaguer | Guadalupe | 1545 | 20.4 | 46/0/0 | 61 / 1 / 1 | 512 | 0.21 | 0 · 0 | indeterminado |
| 58 | Villas de San Francisco 2Do Sector | General Escobedo | 680 | 15.2 | 26/1/2 | 33 / 3 / 0 | 1396 | 0.51 | 0 · 0 | indeterminado_inclina_real |
| 64 | Alfonso Reyes | Monterrey | 973 | 13.8 | 32/0/0 | 37 / 0 / 1 | 398 | 0.38 | 0 · 0 | indeterminado_inclina_brecha |
| 66 | Arboledas de San Roque | Juárez | 1073 | 22.1 | 27/0/2 | 39 / 19 / 0 | 1325 | 0.34 | 0 · 0 | indeterminado_inclina_real |
| 67 | Atoyac de Alvarez | Guadalupe | 546 | 10.6 | 17/0/1 | 21 / 3 / 1 | 542 | 0.58 | 0 · 0 | indeterminado_inclina_real |
| 70 | Const de Queretaro 1 Sec | San Nicolás de los Garza | 764 | 18.8 | 20/0/1 | 23 / 2 / 15 | 476 | 0.47 | 0 · 0 | indeterminado_inclina_real |
| 81 | Privadas de Camino Real Ii | General Escobedo | 1578 | 25.9 | 36/2/3 | 40 / 17 / 1 | 1206 | 0.21 | 0 · 0 | indeterminado_inclina_real |
| 84 | Pedregal del Topo Chico [19021_0184] | General Escobedo | 431 | 5.2 | 13/0/0 | 13 / 0 / 0 | 540 | 0.65 | 0 · 0 | indeterminado_inclina_brecha |
| 91 | Sarabia | Santa Catarina | 846 | 12.9 | 23/1/1 | 28 / 2 / 0 | 391 | 0.43 | 0 · 0 | indeterminado_inclina_real |
| 93 | Parque Industrial Intermex Industrial Campus Apodaca | Apodaca | 955 | 10.6 | 17/0/1 | 18 / 6 / 1 | 835 | 0.39 | 0 · 0 | indeterminado |
| 100 | Puerta del Sol | General Escobedo | 486 | 7.5 | 12/0/1 | 13 / 4 / 0 | 1452 | 0.61 | 0 · 0 | cero_real_probable |
| 107 | Portal de San Francisco Sector 20 de Noviembre | General Escobedo | 479 | 7.3 | 14/0/1 | 16 / 0 / 0 | 752 | 0.62 | 0 · 0 | indeterminado |
| 113 | Union de Colonos | Santa Catarina | 500 | 5.9 | 6/0/0 | 6 / 8 / 2 | 957 | 0.61 | 0 · 0 | indeterminado_inclina_real |
| 114 | Hacienda Renacimiento | García | 863 | 14.2 | 25/0/0 | 29 / 9 / 1 | 534 | 0.42 | 0 · 0 | indeterminado_inclina_real |
| 120 | Paseo del Vergel 1Er Sector | Monterrey | 457 | 5.8 | 10/0/0 | 11 / 2 / 1 | 328 | 0.63 | 0 · 0 | indeterminado_inclina_real |
| 123 | Pimsa Sur | Apodaca | 419 | 5.0 | 7/0/0 | 8 / 2 / 4 | 992 | 0.66 | 0 · 0 | indeterminado_inclina_real |
| 128 | Constituyentes de Queretaro 4 Sec | San Nicolás de los Garza | 821 | 13.9 | 23/0/0 | 26 / 0 / 8 | 671 | 0.44 | 0 · 0 | indeterminado |

## 5. Prioridad Scout (top 15)

Criterio: colonias de esta lista con cobertura Scout **no completa** (<10 marcas; incluye 1 sola marca), que no sean ya «brecha confirmada», «cero real probable» ni «inclina real», ordenadas por rank base (donde verificar puede cambiar una decisión de zona). Sólo orden de visita; no cambia scores.

| Prioridad | # base | Colonia | Municipio | Clasificación | Evidencia |
|--:|--:|---|---|---|---|
| 1 | 1 | Ampliacion Municipal | Monterrey | indeterminado_inclina_brecha | comercio de barrio 69/1000 viv ≥ mediana 38; competidor a 442 m del borde (vecino) |
| 2 | 5 | Pueblo Nuevo 4To Sector | Apodaca | indeterminado_inclina_brecha | comercio de barrio 62/1000 viv ≥ mediana 38; competidor a 311 m del borde (vecino) |
| 3 | 6 | Pueblo Nuevo 1Er Sector | Apodaca | indeterminado_inclina_brecha | comercio de barrio 103/1000 viv ≥ mediana 38; competidor a 555 m del borde (vecino) |
| 4 | 8 | Gloria Mendiola | Monterrey | indeterminado_inclina_brecha | p(0)≈0.15 con tasa media (1.9 esperados); comercio de barrio 43/1000 viv ≥ mediana 38 |
| 5 | 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | indeterminado_inclina_brecha | comercio de barrio 87/1000 viv ≥ mediana 38; competidor a 462 m del borde (vecino) |
| 6 | 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | indeterminado | comercio de barrio 44/1000 viv ≥ mediana 38 |
| 7 | 11 | La Playa | Guadalupe | indeterminado_inclina_brecha | comercio de barrio 88/1000 viv ≥ mediana 38; competidor a 361 m del borde (vecino) |
| 8 | 13 | Paseo de Las Minas | Santa Catarina | brecha_probable | comercio de barrio 53/1000 viv ≥ mediana 38; competidor a 535 m del borde (vecino); sin puntos de Places en la zona (cobertura débil) |
| 9 | 14 | Paseo del Nogalar | San Nicolás de los Garza | indeterminado_inclina_brecha | comercio de barrio 49/1000 viv ≥ mediana 38; competidor a 423 m del borde (vecino) |
| 10 | 15 | Miguel Hidalgo | Guadalupe | indeterminado_inclina_brecha | comercio de barrio 54/1000 viv ≥ mediana 38; competidor a 541 m del borde (vecino) |
| 11 | 16 | Fomerrey 35 (Tierra Propia) | Monterrey | brecha_probable | p(0)≈0.14 con tasa media (2.0 esperados); comercio de barrio 42/1000 viv ≥ mediana 38; competidor a 341 m del borde (vecino) |
| 12 | 19 | Fomerrey 115 (San Bernabe 12) | Monterrey | indeterminado_inclina_brecha | comercio de barrio 42/1000 viv ≥ mediana 38; competidor a 320 m del borde (vecino) |
| 13 | 20 | Indeco La Fama 1 | Santa Catarina | indeterminado_inclina_brecha | comercio de barrio 45/1000 viv ≥ mediana 38; competidor a 426 m del borde (vecino) |
| 14 | 21 | Fomerrey 114 (San Bernabe 13) | Monterrey | brecha_probable | comercio de barrio 49/1000 viv ≥ mediana 38; competidor a 598 m del borde (vecino); sin puntos de Places en la zona (cobertura débil) |
| 15 | 22 | Unidad Piloto | Guadalupe | indeterminado | comercio de barrio 47/1000 viv ≥ mediana 38 |

Qué verificar en campo (10–15 min por colonia): recorrer las calles comerciales; contar recargas/purificadoras informales (sin letrero), precio de recarga y garrafón; anotar en Scout (kind `purificadora`). Una brecha confirmada ya baja el score «con Scout» (ver `docs/CAMBIOS_RANKING_V3.md`).

## 6. Límites
- Heurística sobre los mismos datos que generan el 0: no puede ver competidores que ninguna fuente tiene; sólo detecta incoherencias (comercio alto/colonia grande/vecinos cercanos).
- `p(0)` supone tasa homogénea (Poisson); la densidad real de recargas varía por NSE y zona.
- Viviendas = pob/3.6 (ver `docs/SENSIBILIDAD_VIVIENDAS.md`: sobrestima ~10 %; el efecto en p(0) es pequeño).
- Cada señal es débil por separado (p. ej. «comercio ≥ mediana» lo cumple la mitad de las colonias por construcción; «competidor a ≤600 m» es común). La clasificación sólo ordena dónde mirar primero.
- Scout cubre 17 de 167 colonias; «sin encuesta» ≠ «sin competencia».
