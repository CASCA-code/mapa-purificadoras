# Scout: top 30 celdas de comercio de barrio (OSM) aún sin encuestar

Fecha: **2026-10-02**. Lista de **plan de campo para Nicolás**; no se hizo trabajo de campo ni se contactó a nadie. VERIFICADO = conteo en el archivo citado; SUPUESTO = inferencia. **No altera ningún score.** Scripts: `scripts/analisis_scout_top30_retail.py`, `scripts/doc_scout_top30_retail.py`. Tabla: `v2/data/scout_top30_retail.csv` (30 filas).

## 1. Datos y método

- Consulta pedida: OSM `shop=supermarket|convenience`, bbox lat 25.52..25.92, lon −100.70..−100.00. **Overpass no respondió** hoy: `overpass.private.coffee` (2 intentos, timeout 120 s/100 s sin bytes), `overpass-api.de`, `lz4.overpass-api.de`, `overpass.kumi.systems`, `maps.mail.ru` (sin respuesta) y `overpass.openstreetmap.fr` (403 «only white-listed»). Se mantuvo ritmo bajo (≈1 petición por mirror, sin reintentos agresivos).
- **Fallback (público, mismo contenido OSM):** extracto Geofabrik `mexico-260929.osm.pbf` (2026-09-29) ya en la caja (`/home/box/geo/base_mty/raw/pbf/`), leído con pyosmium: nodos `shop=…` en el bbox + vías `shop=…` (centroide de sus nodos; relaciones omitidas). Raw: `/workspace/downloads/osm_retail_zmm_raw.json` (**1,792 elementos**: nodos 905 + vías 887 — VERIFICADO en el log). © OpenStreetMap contributors, ODbL.
- Dedupe: 113 duplicados internos a ≤30 m; **337 más a ≤30 m de un ancla v3 de categoría oxxo/express/cerveza** (`v2/data/anclas_v3.geojson`, misma regla de 30 m que v3) → quedan **1,342** puntos OSM (convenience 1,049, supermarket 293) que **no están en anclas_v3**. Los abarrotes DENUE no se restan (no están en anclas_v3).
- Celdas: **H3 resolución 8** (`h3` 4.5.0 instalado con pip en venv local; ≈0.74 km², lado ≈460 m): 621 celdas con ≥1 punto; mediana 2 puntos/celda, máx. 19. 173 celdas tocan una de las 167 colonias.
- «Sin encuestar» = **0 marcas de encuesta Scout** dentro de la celda (`scout_marks_v3.geojson`, excluidos pines favorito/lock). 16 celdas ya tienen marcas. La columna `scout_vecinos_ring1` muestra marcas en celdas vecinas (sólo informativa).
- Elegibles: sin marcas Scout, ≥15 % de la celda dentro de una colonia de las 167 (evita celdas que sólo rozan el polígono) → **73** celdas; se listan las 30 con más puntos (desempate por # supermercados). Con tan pocas elegibles, **de la posición ~13 en adelante hay empates en 2–4 puntos**: el orden fino no es significativo.

## 2. Lista de campo (top 30)

| # | Celda H3 r8 | Pts OSM (super/conv) | Colonia | Municipio | Rango base | Comp. v3 ≤300 m | Confianza banda | Mapa |
|--:|---|---|---|---|--:|--:|---|---|
| 1 | `8848a2073dfffff` | 8 (0/8) | Industrial | Monterrey | 87 | 3 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68631,-100.31937) |
| 2 | `8848a20e13fffff` | 7 (2/5) | Vicente Guerrero 3 Sector | San Nicolás de los Garza | 55 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.75335,-100.25501) |
| 3 | `8848a206cdfffff` | 6 (2/4) | Martires de Cananea | Santa Catarina | 160 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68653,-100.43420) |
| 4 | `8848a20e2dfffff` | 6 (2/4) | Noria Norte | Apodaca | 54 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.73349,-100.19849) |
| 5 | `8848a20739fffff` | 6 (1/5) | Industrial | Monterrey | 87 | 3 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68565,-100.32930) |
| 6 | `8848a2a937fffff` | 6 (1/5) | San Gilberto | Santa Catarina | 44 | 4 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.69268,-100.45968) |
| 7 | `8848a20191fffff` | 6 (0/6) | Nuevo San Rafael | Guadalupe | 116 | 1 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.69348,-100.21020) |
| 8 | `8848a20763fffff` | 6 (0/6) | Independencia | Monterrey | 65 | 6 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.66321,-100.31248) |
| 9 | `8848a20f49fffff` | 5 (4/1) | Valle Soleado | Guadalupe | 156 | 3 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.70420,-100.16618) |
| 10 | `8848a2a917fffff` | 5 (4/1) | Puerta del Sol | Santa Catarina | 109 | 3 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.68320,-100.48386) |
| 11 | `8848a20f53fffff` | 5 (1/4) | Noria Norte | Apodaca | 54 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.73414,-100.18857) |
| 12 | `8848a20559fffff` | 5 (0/5) | Niño Artillero | Monterrey | 53 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.70941,-100.32627) |
| 13 | `8848a20f5bfffff` | 4 (2/2) | Cañada Blanca | Guadalupe | 59 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.72601,-100.19290) |
| 14 | `8848a20287fffff` | 4 (1/3) | Sierra Ventana | Monterrey | 136 | 4 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.62581,-100.28446) |
| 15 | `8848a20f09fffff` | 4 (1/3) | Lomas del Pedregal | Apodaca | 162 | 4 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.72794,-100.16312) |
| 16 | `8848a200a7fffff` | 4 (0/4) | Vicente Guerrero | Guadalupe | 46 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.69218,-100.23005) |
| 17 | `8848a20565fffff` | 4 (0/4) | Constituyentes de Queretaro 4 Sec | San Nicolás de los Garza | 128 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.71333,-100.26670) |
| 18 | `8848a20f31fffff` | 4 (0/4) | Pueblo Nuevo 2Do Sector | Apodaca | 69 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.75981,-100.15573) |
| 19 | `8848a20095fffff` | 3 (0/3) | Venustiano Carranza | Monterrey | 139 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68958,-100.26974) |
| 20 | `8848a2023dfffff` | 3 (0/3) | Nueva Estanzuela | Monterrey | 131 | 1 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.58157,-100.24095) |
| 21 | `8848a206c9fffff` | 3 (0/3) | Martires de Cananea | Santa Catarina | 160 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68586,-100.44413) |
| 22 | `8848a206ddfffff` | 3 (0/3) | San Gilberto | Santa Catarina | 44 | 4 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.70082,-100.45537) |
| 23 | `8848a20567fffff` | 2 (1/1) | Azteca | San Nicolás de los Garza | 40 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.72081,-100.27231) |
| 24 | `8848a2061bfffff` | 2 (1/1) | Union de Colonos | Santa Catarina | 113 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.67905,-100.42859) |
| 25 | `8848a20f3bfffff` | 2 (1/1) | Pueblo Nuevo 5To Sector | Apodaca | 49 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.75917,-100.16566) |
| 26 | `8848a2a935fffff` | 2 (1/1) | Sarabia | Santa Catarina | 91 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.68520,-100.45406) |
| 27 | `8848a20037fffff` | 2 (0/2) | 2 de Mayo | Guadalupe | 102 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.65412,-100.21197) |
| 28 | `8848a20231fffff` | 2 (0/2) | Fomerrey 45 | Monterrey | 99 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.58905,-100.24655) |
| 29 | `8848a202a9fffff` | 2 (0/2) | San Angel Sur ( Los Remates ) | Monterrey | 85 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.61898,-100.26894) |
| 30 | `8848a206d9fffff` | 2 (0/2) | San Gilberto | Santa Catarina | 44 | 4 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.70015,-100.46530) |

Por municipio: Monterrey 9, Santa Catarina 8, Apodaca 5, Guadalupe 5, San Nicolás de los Garza 3. Confianza de banda de la colonia: media 19, baja 11. Ninguna de las 30 está en el top-30 del rango base (`top30_rank_base_le30 = 0`): esta lista **no** persigue las mismas colonias que el ranking; mide comercio de paso aún no verificado.

## 3. Lectura y límites

- **Hallazgo (VERIFICADO en los archivos):** OSM trae **1,342 comercios de barrio que no están en `anclas_v3`** (sólo 337 coinciden con Oxxo/Express/cerveza de v3). Es consistente con el hueco de Google Places (máx. 60 por búsqueda/tile, `docs/RATING_V3.md` §4). Si se integrara OSM retail al ancla «oxxo/express» el Anclas\* cambiaría; **no se probó ni se aplicó** (pendiente de Nicolás).
- 12 de las 30 celdas más densas de toda la ZMM caen en las 167 colonias; las más densas (19 y 11 puntos) están fuera de las 167 colonias y 2 del top-30 global ya tienen Scout.
- `n_nombre_cadena` usa una regex amplia sobre `name`/`brand` (Oxxo, 7-Eleven, Six, Extra, Super City, Soriana, Aurrera, HEB…): **1165 de 1,342** puntos coinciden, o sea casi todo el «convenience» OSM es cadena; no distingue tienda de barrio independiente. Supuesto: más tiendas = más flujo peatonal (mismo supuesto de anclas v3, sin dato de ventas).
- Cobertura OSM desigual (voluntaria); una celda con pocos puntos puede ser mapeo incompleto, no ausencia de comercio. «Sin encuestar» ≠ «sin comercio».
- Qué hacer en campo (cuando Nicolás decida): recorrer la celda ~15 min, contar clientes/peatones 10 min en la esquina comercial, anotar en Scout (kind `express`/`otro`/`purificadora`), y revisar recargas informales (`docs/COMPETENCIA_CERO.md`).
