# Cambios de ranking: v2 → v3 base → v3 con Scout

_Generado por `scripts/build_v3_rating.py` (build 2026-09-29T14:14:05Z). Todos los valores salen de `v2/data/colonias_v3.csv`._

- **v2** = ranking del mapa actual (`score_100`: 0.40 Demanda + 0.25 (1−Comp) + 0.20 Anclas + 0.15 (1−Canibal, constante)).
- **v3 base** = 0.40 Demanda + 0.30 Anclas + 0.30 (1−Comp) con **sólo DENUE + Places + OSM** (titular).
- **v3 con Scout** = misma fórmula sumando marcas Scout (anclas, competencia). Se muestra aparte; el bonus es evidencia de campo, no ranking base.

## Por qué se mueven las colonias

La **Demanda\*** es idéntica (mismo valor, mismo peso 0.40), así que **nunca** explica un cambio. Sólo cambian dos términos:

- **Anclas**: v2 `20·Anclas*_v2` (ponderación por tipo, por cercanía al centroide) → v3 `30·Anclas*` (conteo ponderado en polígono+100 m por 1 000 viv., percentil).
- **Competencia**: v2 `25·(1−Comp*_v2)` → v3 `30·(1−Comp*)` (purificadoras ≤300 m del polígono por 1 000 viv., percentil; 0 ⇒ máximo).
- El +15 de Canibal (v2) es igual para todas y no mueve ranks.
- Puntos por causa están **centrados** (se resta el desplazamiento medio: anclas +13.15, competencia -1.78) para que sólo reflejen movimiento relativo. `causa` = término con mayor |Δ|.

## Resumen por municipio: cuántas colonias en top 20 / top 50

| Municipio | Colonias | Top20 v2 | Top20 base | Top20 +Scout | Top50 v2 | Top50 base | Top50 +Scout |
|---|--:|--:|--:|--:|--:|--:|--:|
| Apodaca | 12 | 1 | 2 | 2 | 4 | 4 | 5 |
| García | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| General Escobedo | 26 | 6 | 1 | 2 | 12 | 4 | 4 |
| Guadalupe | 21 | 1 | 2 | 2 | 4 | 6 | 7 |
| Juárez | 13 | 2 | 0 | 0 | 3 | 2 | 3 |
| Monterrey | 60 | 8 | 10 | 9 | 21 | 23 | 20 |
| San Nicolás de los Garza | 11 | 0 | 2 | 2 | 0 | 3 | 3 |
| Santa Catarina | 17 | 2 | 3 | 3 | 6 | 8 | 8 |

## Top 10 v3 base

| # base | Colonia | Municipio | Score base | # v2 | # con Scout | Marcas Scout | Cobertura | Anclas/1000 viv | Purif. ≤300 m | Demanda* | Anclas* | Comp* |
|--:|---|---|--:|--:|--:|--:|---|--:|--:|--:|--:|--:|
| 1 | Ampliacion Municipal | Monterrey | 73.7 | 73 | 2 | 1 | parcial | 40.7 | 0 | 0.39 | 0.93 | 0.00 |
| 2 | Fomerrey 112 (San Bernabe 9) | Monterrey | 69.5 | 39 | 23 | 0 | sin encuesta | 30.1 | 0 | 0.45 | 0.72 | 0.00 |
| 3 | San Miguel Residencial | General Escobedo | 69.5 | 3 | 4 | 22 | encuestada | 16.8 | 0 | 0.88 | 0.14 | 0.00 |
| 4 | Croc | Monterrey | 68.7 | 1 | 1 | 88 | encuestada | 21.9 | 3 | 1.00 | 0.37 | 0.42 |
| 5 | Pueblo Nuevo 4To Sector | Apodaca | 67.0 | 51 | 7 | 0 | sin encuesta | 50.4 | 0 | 0.20 | 0.97 | 0.00 |
| 6 | Pueblo Nuevo 1Er Sector | Apodaca | 66.8 | 133 | 6 | 0 | sin encuesta | 64.7 | 0 | 0.17 | 1.00 | 0.00 |
| 7 | Fomerrey 24 | Monterrey | 66.3 | 121 | 90 | 1 | parcial | 41.0 | 0 | 0.20 | 0.94 | 0.00 |
| 8 | Gloria Mendiola | Monterrey | 65.7 | 15 | 3 | 6 | parcial | 21.0 | 0 | 0.63 | 0.36 | 0.00 |
| 9 | Floridos Bosques del Nogalar | San Nicolás de los Garza | 65.7 | 161 | 8 | 0 | sin encuesta | 51.8 | 0 | 0.15 | 0.99 | 0.00 |
| 10 | Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 65.2 | 48 | 11 | 0 | sin encuesta | 28.8 | 0 | 0.36 | 0.69 | 0.00 |

## Top 10 que suben (v2 → v3 base)

| Colonia | Municipio | # v2 | # base | Δ | Causa | Δ anclas (pts) | Δ comp. (pts) |
|---|---|--:|--:|--:|---|--:|--:|
| Floridos Bosques del Nogalar | San Nicolás de los Garza | 161 | 9 | +152 | competencia | +15.8 | +16.4 |
| Villas de San Jose 7 Sector | Juárez | 160 | 27 | +133 | competencia | +11.1 | +13.8 |
| Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 149 | 18 | +131 | competencia | +10.5 | +15.3 |
| Pueblo Nuevo 1Er Sector | Apodaca | 133 | 6 | +127 | anclas | +16.9 | +12.1 |
| Union Modelo | Guadalupe | 148 | 24 | +124 | competencia | +11.1 | +12.4 |
| Fomerrey 24 | Monterrey | 121 | 7 | +114 | anclas | +14.3 | +13.1 |
| Miguel Hidalgo | Guadalupe | 120 | 15 | +105 | anclas | +12.0 | +11.9 |
| Argentina | Monterrey | 147 | 43 | +104 | competencia | +4.7 | +11.3 |
| Paseo del Nogalar | San Nicolás de los Garza | 117 | 14 | +103 | competencia | +7.4 | +16.8 |
| Cerro de Las Mitras (Raul Salinas Lozano) | Santa Catarina | 140 | 39 | +101 | competencia | -1.2 | +16.6 |

## Top 10 que bajan (v2 → v3 base)

| Colonia | Municipio | # v2 | # base | Δ | Causa | Δ anclas (pts) | Δ comp. (pts) |
|---|---|--:|--:|--:|---|--:|--:|
| Gloria Mendiola | General Escobedo | 13 | 130 | -117 | anclas | -13.1 | -8.2 |
| Sierra Ventana | Monterrey | 28 | 136 | -108 | competencia | -6.9 | -9.1 |
| Genaro Vazquez Rojas | Monterrey | 56 | 154 | -98 | competencia | -7.5 | -9.3 |
| Valle Soleado | Guadalupe | 58 | 156 | -98 | competencia | -10.1 | -10.5 |
| Bosques de La Estanzuela | Monterrey | 43 | 134 | -91 | anclas | -7.2 | -6.7 |
| Unidad Pedreras ( Fomerrey 106 ) | Monterrey | 24 | 111 | -87 | competencia | +1.5 | -14.6 |
| Vicente Ferrer | Guadalupe | 61 | 146 | -85 | competencia | -2.7 | -11.1 |
| Rivera de Los Naranjos | General Escobedo | 22 | 106 | -84 | competencia | -5.9 | -7.9 |
| Puerta del Sol | Santa Catarina | 26 | 109 | -83 | competencia | +6.5 | -19.1 |
| Francisco Villa | Monterrey | 36 | 119 | -83 | competencia | -1.8 | -11.0 |

## Efecto Scout (base → con Scout): mayores subidas / bajadas

| Colonia | Municipio | # base | # con Scout | Δ | Marcas Scout | Bonus (pts) | Causa |
|---|---|--:|--:|--:|--:|--:|---|
| El Porvenir | Monterrey | 63 | 25 | +38 | 4 | +8.9 | anclas |
| Unidad Pedreras ( Fomerrey 106 ) | Monterrey | 111 | 85 | +26 | 5 | +5.2 | anclas |
| Rene Alvarez | Monterrey | 30 | 5 | +25 | 0 | +10.5 | anclas |
| Francisco Villa | Monterrey | 119 | 97 | +22 | 1 | +4.7 | anclas |
| Independencia | Monterrey | 65 | 51 | +14 | 0 | +1.6 | competencia |
| La Altamira | Monterrey | 89 | 77 | +12 | 0 | +1.6 | competencia |
| Gloria Mendiola | General Escobedo | 130 | 119 | +11 | 0 | +1.6 | competencia |
| Fomerrey 113 (San Bernabe 9) | Monterrey | 133 | 122 | +11 | 6 | +2.2 | anclas |
| Lazaro Cardenas | Monterrey | 17 | 103 | -86 | 0 | -23.9 | competencia |
| Fomerrey 24 | Monterrey | 7 | 90 | -83 | 1 | -24.6 | competencia |
| Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 18 | 74 | -56 | 5 | -17.3 | competencia |
| Libertadores de America | Monterrey | 50 | 79 | -29 | 0 | -7.6 | competencia |
| Unidad del Pueblo | Monterrey | 127 | 150 | -23 | 0 | -5.4 | competencia |

Cobertura de campo: 150 colonias **sin encuesta** (0 marcas Scout), 14 parciales (1–9), 3 encuestadas (≥10).

## Tabla completa (167 colonias)

| Colonia | Municipio | # v2 | # base | # +Scout | Δ v2→base | Causa | Marcas Scout | Cobertura |
|---|---|--:|--:|--:|--:|---|--:|---|
| Ampliacion Municipal | Monterrey | 73 | 1 | 2 | +72 | competencia (+14.9/+16.3) | 1 | parcial |
| Fomerrey 112 (San Bernabe 9) | Monterrey | 39 | 2 | 23 | +37 | competencia (+4.8/+16.5) | 0 | sin encuesta |
| San Miguel Residencial | General Escobedo | 3 | 3 | 4 | +0 | competencia (-8.8/+10.2) | 22 | encuestada |
| Croc | Monterrey | 1 | 4 | 1 | -3 | anclas (-5.0/+0.9) | 88 | encuestada |
| Pueblo Nuevo 4To Sector | Apodaca | 51 | 5 | 7 | +46 | anclas (+11.4/+9.7) | 0 | sin encuesta |
| Pueblo Nuevo 1Er Sector | Apodaca | 133 | 6 | 6 | +127 | anclas (+16.9/+12.1) | 0 | sin encuesta |
| Fomerrey 24 | Monterrey | 121 | 7 | 90 | +114 | anclas (+14.3/+13.1) | 1 | parcial |
| Gloria Mendiola | Monterrey | 15 | 8 | 3 | +7 | competencia (-2.5/+13.1) | 6 | parcial |
| Floridos Bosques del Nogalar | San Nicolás de los Garza | 161 | 9 | 8 | +152 | competencia (+15.8/+16.4) | 0 | sin encuesta |
| Rincon de Las Mitras (Fomerrey 2) | Santa Catarina | 48 | 10 | 11 | +38 | competencia (+4.5/+14.4) | 0 | sin encuesta |
| La Playa | Guadalupe | 96 | 11 | 9 | +85 | competencia (+12.0/+12.0) | 0 | sin encuesta |
| San Bernabe 1Er Sector | Monterrey | 19 | 12 | 10 | +7 | competencia (-2.0/+14.3) | 0 | sin encuesta |
| Paseo de Las Minas | Santa Catarina | 38 | 13 | 12 | +25 | competencia (+1.7/+14.1) | 0 | sin encuesta |
| Paseo del Nogalar | San Nicolás de los Garza | 117 | 14 | 13 | +103 | competencia (+7.4/+16.8) | 0 | sin encuesta |
| Miguel Hidalgo | Guadalupe | 120 | 15 | 14 | +105 | anclas (+12.0/+11.9) | 0 | sin encuesta |
| Fomerrey 35 (Tierra Propia) | Monterrey | 46 | 16 | 15 | +30 | competencia (+3.7/+12.1) | 0 | sin encuesta |
| Lazaro Cardenas | Monterrey | 114 | 17 | 103 | +97 | anclas (+14.0/+9.0) | 0 | sin encuesta |
| Fomerrey 23 ( Laderas de Topo Chico) | Monterrey | 149 | 18 | 74 | +131 | competencia (+10.5/+15.3) | 5 | parcial |
| Fomerrey 115 (San Bernabe 12) | Monterrey | 88 | 19 | 17 | +69 | competencia (+0.2/+19.6) | 0 | sin encuesta |
| Indeco La Fama 1 | Santa Catarina | 81 | 20 | 18 | +61 | competencia (+4.0/+14.7) | 0 | sin encuesta |
| Fomerrey 114 (San Bernabe 13) | Monterrey | 89 | 21 | 19 | +68 | competencia (+1.8/+17.1) | 0 | sin encuesta |
| Unidad Piloto | Guadalupe | 29 | 22 | 21 | +7 | competencia (-0.7/+11.8) | 0 | sin encuesta |
| Villas de San Francisco | General Escobedo | 5 | 23 | 41 | -18 | anclas (-12.8/+10.3) | 1 | parcial |
| Union Modelo | Guadalupe | 148 | 24 | 22 | +124 | competencia (+11.1/+12.4) | 0 | sin encuesta |
| Nuevo Leon Estado de Progreso (Alianza Real) | General Escobedo | 8 | 25 | 16 | -17 | anclas (-9.0/+6.5) | 3 | parcial |
| Moctezuma | Monterrey | 111 | 26 | 20 | +85 | competencia (+5.5/+14.0) | 0 | sin encuesta |
| Villas de San Jose 7 Sector | Juárez | 160 | 27 | 24 | +133 | competencia (+11.1/+13.8) | 0 | sin encuesta |
| Topo Chico | Monterrey | 9 | 28 | 28 | -19 | anclas (-5.0/+1.9) | 18 | encuestada |
| 25 de Noviembre | Guadalupe | 60 | 29 | 27 | +31 | competencia (+1.5/+11.0) | 0 | sin encuesta |
| Rene Alvarez | Monterrey | 94 | 30 | 5 | +64 | competencia (+2.4/+13.0) | 0 | sin encuesta |
| Fomerrey 1 ( Reforma ) | Monterrey | 41 | 31 | 30 | +10 | anclas (+6.8/+1.4) | 5 | parcial |
| Emiliano Zapata | Monterrey | 132 | 32 | 32 | +100 | competencia (+6.5/+10.4) | 0 | sin encuesta |
| Riveras del Rio | Monterrey | 4 | 33 | 26 | -29 | anclas (-8.1/-1.1) | 0 | sin encuesta |
| Fomerrey 110 (San Bernabe 15) | Monterrey | 119 | 34 | 29 | +85 | anclas (+13.2/+2.2) | 0 | sin encuesta |
| Paseo de San Bernabe | Monterrey | 80 | 35 | 34 | +45 | competencia (+1.3/+10.6) | 0 | sin encuesta |
| Eugenio Canavati | Santa Catarina | 116 | 36 | 35 | +80 | competencia (-2.5/+17.1) | 0 | sin encuesta |
| Pueblo Nuevo 3Er Sector | Apodaca | 32 | 37 | 33 | -5 | competencia (-8.6/+13.9) | 0 | sin encuesta |
| Fama Iii | Santa Catarina | 23 | 38 | 31 | -15 | anclas (+2.3/+1.1) | 0 | sin encuesta |
| Cerro de Las Mitras (Raul Salinas Lozano) | Santa Catarina | 140 | 39 | 39 | +101 | competencia (-1.2/+16.6) | 0 | sin encuesta |
| Azteca | San Nicolás de los Garza | 87 | 40 | 38 | +47 | competencia (-2.3/+13.4) | 0 | sin encuesta |
| Constituyentes del 57 | Monterrey | 115 | 41 | 40 | +74 | competencia (+0.9/+12.3) | 0 | sin encuesta |
| Fernando Amilpa | General Escobedo | 20 | 42 | 37 | -22 | competencia (-10.4/+10.9) | 0 | sin encuesta |
| Argentina | Monterrey | 147 | 43 | 42 | +104 | competencia (+4.7/+11.3) | 0 | sin encuesta |
| San Gilberto | Santa Catarina | 2 | 44 | 36 | -42 | anclas (-15.1/-3.6) | 0 | sin encuesta |
| San Martin | Monterrey | 50 | 45 | 63 | +5 | anclas (+3.4/+2.2) | 0 | sin encuesta |
| Vicente Guerrero | Guadalupe | 143 | 46 | 45 | +97 | competencia (+3.9/+10.3) | 0 | sin encuesta |
| Cimas de Las Mitras (Ampl Raul Salinas Lozano) | Santa Catarina | 106 | 47 | 46 | +59 | competencia (-3.6/+14.4) | 0 | sin encuesta |
| Monte Kristal | Juárez | 11 | 48 | 43 | -37 | competencia (+5.3/-13.3) | 0 | sin encuesta |
| Pueblo Nuevo 5To Sector | Apodaca | 34 | 49 | 44 | -15 | anclas (+7.8/-5.6) | 0 | sin encuesta |
| Libertadores de America | Monterrey | 55 | 50 | 79 | +5 | competencia (-6.8/+11.9) | 0 | sin encuesta |
| Hector Caballero | Juárez | 53 | 51 | 49 | +2 | competencia (-4.1/+8.9) | 0 | sin encuesta |
| Los Valles 2Do Sector | Juárez | 104 | 52 | 56 | +52 | competencia (+0.2/+9.1) | 0 | sin encuesta |
| Niño Artillero | Monterrey | 122 | 53 | 47 | +69 | anclas (+13.1/-2.1) | 0 | sin encuesta |
| Noria Norte | Apodaca | 35 | 54 | 48 | -19 | competencia (-1.3/+2.3) | 0 | sin encuesta |
| Vicente Guerrero 3 Sector | San Nicolás de los Garza | 99 | 55 | 54 | +44 | competencia (-6.1/+14.9) | 0 | sin encuesta |
| Nuevo Almaguer | Guadalupe | 25 | 56 | 52 | -31 | anclas (-11.9/+11.1) | 0 | sin encuesta |
| Tierra Y Libertad | Monterrey | 40 | 57 | 60 | -17 | anclas (+12.5/-11.4) | 4 | parcial |
| Villas de San Francisco 2Do Sector | General Escobedo | 93 | 58 | 58 | +35 | competencia (-1.4/+9.2) | 0 | sin encuesta |
| Cañada Blanca | Guadalupe | 16 | 59 | 50 | -43 | anclas (-9.4/+3.1) | 0 | sin encuesta |
| Fomerrey 116 (San Bernabe 8) | Monterrey | 27 | 60 | 53 | -33 | anclas (-6.6/+5.8) | 0 | sin encuesta |
| Los Valles | Juárez | 45 | 61 | 57 | -16 | anclas (+13.8/-12.6) | 0 | sin encuesta |
| Fomerrey 109 (San Bernabe 14) | Monterrey | 128 | 62 | 55 | +66 | anclas (+10.4/-0.3) | 0 | sin encuesta |
| El Porvenir | Monterrey | 67 | 63 | 25 | +4 | anclas (+2.7/+1.4) | 4 | parcial |
| Alfonso Reyes | Monterrey | 42 | 64 | 59 | -22 | competencia (-12.4/+12.5) | 0 | sin encuesta |
| Independencia | Monterrey | 10 | 65 | 51 | -55 | anclas (-11.2/-0.2) | 0 | sin encuesta |
| Arboledas de San Roque | Juárez | 90 | 66 | 61 | +24 | competencia (-2.8/+9.2) | 0 | sin encuesta |
| Atoyac de Alvarez | Guadalupe | 59 | 67 | 64 | -8 | competencia (-9.1/+11.5) | 0 | sin encuesta |
| Rancho Viejo | Juárez | 17 | 68 | 65 | -51 | competencia (+12.2/-19.2) | 0 | sin encuesta |
| Pueblo Nuevo 2Do Sector | Apodaca | 63 | 69 | 62 | -6 | anclas (+1.9/+0.5) | 0 | sin encuesta |
| Const de Queretaro 1 Sec | San Nicolás de los Garza | 155 | 70 | 67 | +85 | competencia (-1.6/+12.7) | 0 | sin encuesta |
| Eulalio Villarreal | General Escobedo | 83 | 71 | 68 | +12 | anclas (+16.1/-12.8) | 0 | sin encuesta |
| Los Nogales | García | 101 | 72 | 66 | +29 | anclas (+13.8/-9.1) | 0 | sin encuesta |
| 10 de Marzo | Monterrey | 131 | 73 | 73 | +58 | anclas (+10.5/-3.4) | 0 | sin encuesta |
| Prados de La Cieneguita | Apodaca | 12 | 74 | 75 | -62 | competencia (-3.0/-10.8) | 0 | sin encuesta |
| Nueva Esperanza | General Escobedo | 49 | 75 | 72 | -26 | competencia (+1.1/-2.9) | 0 | sin encuesta |
| Lomas de La Fama | Santa Catarina | 6 | 76 | 69 | -70 | anclas (-18.7/+0.3) | 0 | sin encuesta |
| 18 de Octubre | General Escobedo | 21 | 77 | 70 | -56 | anclas (-7.7/-0.1) | 0 | sin encuesta |
| Revolucion Proletaria | Monterrey | 95 | 78 | 76 | +17 | anclas (+5.7/-3.1) | 0 | sin encuesta |
| Pedregal del Topo Chico [19021_0183] | General Escobedo | 33 | 79 | 71 | -46 | anclas (-3.9/-1.1) | 1 | parcial |
| Valle de Santa Lucia (Granja Sanitaria) | Monterrey | 30 | 80 | 83 | -50 | anclas (-5.6/-0.2) | 2 | parcial |
| Privadas de Camino Real Ii | General Escobedo | 109 | 81 | 81 | +28 | competencia (-9.5/+12.3) | 0 | sin encuesta |
| Ampl Los Nogales ( El Polvorin ) | García | 64 | 82 | 88 | -18 | competencia (+11.6/-13.2) | 0 | sin encuesta |
| Campestre La Silla | Guadalupe | 70 | 83 | 82 | -13 | competencia (+7.6/-8.6) | 0 | sin encuesta |
| Pedregal del Topo Chico [19021_0184] | General Escobedo | 47 | 84 | 87 | -37 | anclas (-12.4/+8.5) | 0 | sin encuesta |
| San Angel Sur ( Los Remates ) | Monterrey | 37 | 85 | 80 | -48 | anclas (-4.3/-1.9) | 0 | sin encuesta |
| Burocratas Municipales | Monterrey | 7 | 86 | 78 | -79 | anclas (-12.1/-7.8) | 0 | sin encuesta |
| Industrial | Monterrey | 68 | 87 | 86 | -19 | anclas (-4.7/+3.0) | 0 | sin encuesta |
| Josefa Zozaya 2Do Sector | Guadalupe | 144 | 88 | 91 | +56 | anclas (+13.8/-9.0) | 0 | sin encuesta |
| La Altamira | Monterrey | 14 | 89 | 77 | -75 | anclas (-9.7/-4.3) | 0 | sin encuesta |
| Colinas del Topo Chico | General Escobedo | 146 | 90 | 92 | +56 | anclas (+14.1/-9.4) | 0 | sin encuesta |
| Sarabia | Santa Catarina | 84 | 91 | 93 | -7 | anclas (-10.8/+10.2) | 0 | sin encuesta |
| La Unidad | General Escobedo | 18 | 92 | 84 | -74 | anclas (-9.5/-2.4) | 0 | sin encuesta |
| Parque Industrial Intermex Industrial Campus Apodaca | Apodaca | 74 | 93 | 95 | -19 | anclas (-13.0/+11.3) | 0 | sin encuesta |
| Nuevo Escobedo | General Escobedo | 77 | 94 | 94 | -17 | competencia (-0.3/-1.7) | 0 | sin encuesta |
| Balcones de Santa Catarina ( Fomerrey 134) | Santa Catarina | 85 | 95 | 96 | -10 | competencia (+3.7/-5.4) | 0 | sin encuesta |
| San Angel Norte | Monterrey | 153 | 96 | 89 | +57 | anclas (+14.7/-10.6) | 0 | sin encuesta |
| Arboledas de Los Naranjos | Juárez | 52 | 97 | 104 | -45 | competencia (+9.8/-16.4) | 0 | sin encuesta |
| 31 de Diciembre | Guadalupe | 123 | 98 | 98 | +25 | anclas (+9.6/-9.4) | 0 | sin encuesta |
| Fomerrey 45 | Monterrey | 79 | 99 | 99 | -20 | competencia (+2.8/-6.2) | 0 | sin encuesta |
| Puerta del Sol | General Escobedo | 152 | 100 | 101 | +52 | competencia (-10.3/+13.1) | 0 | sin encuesta |
| Fomerrey 9 (Solidaridad Social) | General Escobedo | 135 | 101 | 107 | +34 | anclas (+6.4/-5.9) | 0 | sin encuesta |
| 2 de Mayo | Guadalupe | 108 | 102 | 100 | +6 | competencia (+4.8/-6.7) | 0 | sin encuesta |
| Fomerrey 36 | General Escobedo | 31 | 103 | 112 | -72 | competencia (-2.0/-9.0) | 0 | sin encuesta |
| Santa Lucia | General Escobedo | 130 | 104 | 111 | +26 | competencia (+15.8/-16.0) | 0 | sin encuesta |
| Agropecuaria Emiliano Zapata (Col Nueva Esperanza) | General Escobedo | 54 | 105 | 106 | -51 | anclas (-4.7/-3.1) | 0 | sin encuesta |
| Rivera de Los Naranjos | General Escobedo | 22 | 106 | 102 | -84 | competencia (-5.9/-7.9) | 0 | sin encuesta |
| Portal de San Francisco Sector 20 de Noviembre | General Escobedo | 113 | 107 | 110 | +6 | anclas (-10.4/+8.3) | 0 | sin encuesta |
| Carmen Serdan | Monterrey | 91 | 108 | 105 | -17 | competencia (+9.2/-13.0) | 0 | sin encuesta |
| Puerta del Sol | Santa Catarina | 26 | 109 | 114 | -83 | competencia (+6.5/-19.1) | 0 | sin encuesta |
| Fomerrey 129 (Mirador San Nicolas) | San Nicolás de los Garza | 76 | 110 | 108 | -34 | competencia (+1.5/-6.7) | 0 | sin encuesta |
| Unidad Pedreras ( Fomerrey 106 ) | Monterrey | 24 | 111 | 85 | -87 | competencia (+1.5/-14.6) | 5 | parcial |
| Serranias | General Escobedo | 158 | 112 | 117 | +46 | anclas (+15.4/-12.9) | 0 | sin encuesta |
| Union de Colonos | Santa Catarina | 118 | 113 | 113 | +5 | anclas (-12.6/+10.1) | 0 | sin encuesta |
| Hacienda Renacimiento | García | 100 | 114 | 115 | -14 | anclas (-12.6/+8.6) | 0 | sin encuesta |
| Monte Kristal 4To Sector | Juárez | 98 | 115 | 118 | -17 | competencia (+9.3/-13.3) | 0 | sin encuesta |
| Nuevo San Rafael | Guadalupe | 44 | 116 | 109 | -72 | anclas (-11.0/+0.2) | 0 | sin encuesta |
| Garza Melo | Guadalupe | 97 | 117 | 121 | -20 | competencia (+11.7/-16.2) | 0 | sin encuesta |
| Arboledas de Las Mitras (Carlos Salinas de Gortari) | Santa Catarina | 65 | 118 | 124 | -53 | competencia (+0.8/-8.7) | 0 | sin encuesta |
| Francisco Villa | Monterrey | 36 | 119 | 97 | -83 | competencia (-1.8/-11.0) | 1 | parcial |
| Paseo del Vergel 1Er Sector | Monterrey | 138 | 120 | 126 | +18 | anclas (-12.1/+10.1) | 0 | sin encuesta |
| Fray Servando Teresa de Mier (Fomerrey 6 ) | Monterrey | 137 | 121 | 129 | +16 | competencia (+8.2/-10.2) | 0 | sin encuesta |
| La Condesa | Monterrey | 92 | 122 | 123 | -30 | competencia (+2.2/-7.8) | 0 | sin encuesta |
| Pimsa Sur | Apodaca | 126 | 123 | 127 | +3 | anclas (-12.2/+9.5) | 0 | sin encuesta |
| La Campana | Monterrey | 62 | 124 | 116 | -62 | anclas (-4.7/-4.4) | 0 | sin encuesta |
| Hacienda Santa Catarina (Fomerrey 29) | Santa Catarina | 78 | 125 | 132 | -47 | competencia (+10.7/-17.8) | 0 | sin encuesta |
| Carmen Romano | San Nicolás de los Garza | 105 | 126 | 120 | -21 | anclas (-11.2/+6.1) | 0 | sin encuesta |
| Unidad del Pueblo | Monterrey | 71 | 127 | 150 | -56 | competencia (-1.8/-6.5) | 0 | sin encuesta |
| Constituyentes de Queretaro 4 Sec | San Nicolás de los Garza | 86 | 128 | 130 | -42 | anclas (-19.5/+12.4) | 0 | sin encuesta |
| Garza Nieto | Monterrey | 167 | 129 | 133 | +38 | anclas (+8.2/+3.0) | 0 | sin encuesta |
| Gloria Mendiola | General Escobedo | 13 | 130 | 119 | -117 | anclas (-13.1/-8.2) | 0 | sin encuesta |
| Nueva Estanzuela | Monterrey | 57 | 131 | 125 | -74 | anclas (-5.6/-5.1) | 0 | sin encuesta |
| Valles del Sol | Guadalupe | 136 | 132 | 134 | +4 | competencia (+5.4/-8.9) | 0 | sin encuesta |
| Fomerrey 113 (San Bernabe 9) | Monterrey | 72 | 133 | 122 | -61 | anclas (-6.0/-3.2) | 6 | parcial |
| Bosques de La Estanzuela | Monterrey | 43 | 134 | 128 | -91 | anclas (-7.2/-6.7) | 0 | sin encuesta |
| Fomerrey 25 | Monterrey | 150 | 135 | 137 | +15 | anclas (-2.4/-0.1) | 0 | sin encuesta |
| Sierra Ventana | Monterrey | 28 | 136 | 131 | -108 | competencia (-6.9/-9.1) | 0 | sin encuesta |
| Ignacio Zaragoza | Guadalupe | 156 | 137 | 135 | +19 | competencia (+5.2/-6.8) | 0 | sin encuesta |
| Santa Martha | General Escobedo | 82 | 138 | 139 | -56 | competencia (+3.3/-12.5) | 0 | sin encuesta |
| Venustiano Carranza | Monterrey | 145 | 139 | 140 | +6 | competencia (+10.6/-14.8) | 0 | sin encuesta |
| Alvaro Obregon | Monterrey | 159 | 140 | 138 | +19 | anclas (-3.4/+1.9) | 0 | sin encuesta |
| Valle del Mezquital | San Nicolás de los Garza | 127 | 141 | 136 | -14 | anclas (-8.4/+2.6) | 0 | sin encuesta |
| Lagos de Chapultepec | San Nicolás de los Garza | 124 | 142 | 142 | -18 | competencia (+4.0/-10.2) | 0 | sin encuesta |
| Brisas Residencial | García | 69 | 143 | 141 | -74 | competencia (+4.3/-15.9) | 0 | sin encuesta |
| America 2 | Monterrey | 129 | 144 | 143 | -15 | competencia (+6.9/-13.1) | 0 | sin encuesta |
| Ampliacion Cerritos | García | 110 | 145 | 149 | -35 | competencia (+11.6/-20.6) | 0 | sin encuesta |
| Vicente Ferrer | Guadalupe | 61 | 146 | 144 | -85 | competencia (-2.7/-11.1) | 0 | sin encuesta |
| Nogales de La Sierra | Monterrey | 112 | 147 | 148 | -35 | competencia (+5.8/-15.4) | 0 | sin encuesta |
| Tierra Propia 2Do Sector | Guadalupe | 102 | 148 | 145 | -46 | anclas (-6.5/-4.1) | 0 | sin encuesta |
| Renacimiento | García | 66 | 149 | 147 | -83 | competencia (-2.3/-11.8) | 0 | sin encuesta |
| Los Encinos | Juárez | 107 | 150 | 153 | -43 | competencia (+6.1/-16.9) | 0 | sin encuesta |
| Riberas de La Silla | Guadalupe | 75 | 151 | 146 | -76 | anclas (-10.6/-2.7) | 0 | sin encuesta |
| Fomerrey 51 | Monterrey | 163 | 152 | 152 | +11 | competencia (+3.5/-5.1) | 0 | sin encuesta |
| Lomas del Poniente 1Er Sector | Santa Catarina | 125 | 153 | 154 | -28 | competencia (+4.5/-14.6) | 0 | sin encuesta |
| Genaro Vazquez Rojas | Monterrey | 56 | 154 | 151 | -98 | competencia (-7.5/-9.3) | 0 | sin encuesta |
| Novapodaca | Apodaca | 134 | 155 | 157 | -21 | competencia (+3.8/-16.3) | 0 | sin encuesta |
| Valle Soleado | Guadalupe | 58 | 156 | 155 | -98 | competencia (-10.1/-10.5) | 0 | sin encuesta |
| Hacienda San Miguel, Sector Palmiras | General Escobedo | 139 | 157 | 156 | -18 | competencia (-2.1/-12.4) | 0 | sin encuesta |
| Bella Vista | Monterrey | 165 | 158 | 158 | +7 | anclas (-8.3/+6.4) | 0 | sin encuesta |
| Joaquin Garza Y Garza | Juárez | 142 | 159 | 159 | -17 | competencia (-7.4/-8.6) | 0 | sin encuesta |
| Martires de Cananea | Santa Catarina | 154 | 160 | 160 | -6 | anclas (-16.6/+0.7) | 0 | sin encuesta |
| Las Malvinas | General Escobedo | 162 | 161 | 161 | +1 | competencia (-0.1/-12.9) | 0 | sin encuesta |
| Lomas del Pedregal | Apodaca | 141 | 162 | 164 | -21 | competencia (-4.8/-16.8) | 0 | sin encuesta |
| Los Encinos Residencial | García | 103 | 163 | 162 | -60 | competencia (-8.1/-16.8) | 0 | sin encuesta |
| Mirador del Parque | Juárez | 157 | 164 | 163 | -7 | anclas (-11.0/-9.0) | 0 | sin encuesta |
| Portal de Vaquerias | Juárez | 151 | 165 | 165 | -14 | competencia (-9.4/-14.2) | 0 | sin encuesta |
| Nogalar | San Nicolás de los Garza | 166 | 166 | 167 | +0 | anclas (-13.0/-3.5) | 0 | sin encuesta |
| Los Fresnos 1Er Sector | Apodaca | 164 | 167 | 166 | -3 | anclas (-12.7/-7.9) | 0 | sin encuesta |
