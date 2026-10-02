# Scout: top 30 celdas con carnicerías OSM (ancla extra) aún sin encuestar

Fecha: **2026-10-02**. Lista de **plan de campo para Nicolás**; no se hizo trabajo de campo ni se contactó a nadie. VERIFICADO = conteo en el archivo citado; SUPUESTO = inferencia. **No altera ningún score.** Scripts: `scripts/extract_osm_anchor_extra.py`, `scripts/analisis_scout_ancla_extra.py`, `scripts/doc_scout_ancla_extra.py`. Tabla: `v2/data/scout_top30_ancla_extra.csv` (30 filas).

## 1. Por qué carnicerías (`shop=butcher`)

`anclas_v3.geojson` ya trae parada, tortillería, escuela, farmacia, cerveza, Oxxo, express, iglesia y banco; la lista de Scout anterior (`SCOUT_TOP30_RETAIL.md`) cubrió `shop=supermarket|convenience`. Iglesia (`place_of_worship`) ya está en v3 (306 puntos OSM), así que se descartó. De los candidatos que quedaban conté puntos OSM y cuántos no están a ≤30 m de ningún punto de `anclas_v3` (misma regla de 30 m de v3):

| Tipo OSM | Puntos (tras dedupe 30 m) | Nuevos vs `anclas_v3` | Dentro de las 167 colonias | Nuevos dentro de las 167 |
|---|--:|--:|--:|--:|
| butcher | 101 | 81 | 5 | 2 |
| bakery | 52 | 44 | 0 | 0 |
| marketplace | 10 | 10 | 1 | 1 |
| greengrocer | 8 | 5 | 1 | 1 |

- **Carnicería gana por volumen:** 81 puntos nuevos, casi el doble que panaderías (44) y 16 veces las fruterías (5).
- **Mercado/tianguis (`amenity=marketplace`) tiene el vínculo más directo con flujo peatonal, pero solo hay 10 y el etiquetado es ruidoso:** entre los 10 nombres hay «Muebles Villareal», «Soriana Híper», «Penny Riel» y «Multicomercial Guadalupe» (VERIFICADO en el raw); solo cuatro llevan «Mercado» en el nombre («Mercado Popular No. 3 Francisco Villa», «Mercado La Florida», «Mercado Emiliano Zapata» y «Mercado»). No alcanza para 30 celdas.
- **Vínculo con la recarga: SUPUESTO.** Una carnicería de barrio se visita varias veces por semana a pie; quien compra ahí pasa por la calle donde podría haber una estación. No tengo dato de que ese flujo se convierta en compra de garrafón. Es el mismo tipo de supuesto de las anclas de barrio (`ANCLAS_BARRIO.md`).

## 2. Datos y método

- **Overpass no respondió** hoy. Probé `overpass.private.coffee`, `overpass-api.de`, `overpass.kumi.systems` y `lz4.overpass-api.de` con una petición cada uno y 3 s de espera entre ellos: los cuatro cerraron sin conexión (código 000, 0 bytes, timeout 40 s). Antes, `SCOUT_TOP30_RETAIL.md` documentó fallas en los mismos mirrors.
- **Fallback (público, mismo contenido OSM):** extracto Geofabrik `mexico-260929.osm.pbf` (2026-09-29) en la caja, leído con pyosmium: nodos y vías (centroide de sus nodos; relaciones omitidas) con `amenity=marketplace` o `shop=butcher|greengrocer|bakery` en el bbox lat 25.52..25.92, lon −100.70..−100.00. Raw (fuera del repo): `/workspace/downloads/osm_anchor_extra_raw.json`, **179 elementos** (carnicería 107, panadería 54, mercado 10, frutería 8). © OpenStreetMap contributors, ODbL.
- Dedupe interno a 30 m dentro del mismo tipo (8 duplicados). «Nuevo» = a más de 30 m de cualquier punto de `anclas_v3`. Quedan **81 carnicerías nuevas** en **71 celdas H3 r8** (≈0.74 km² cada una).
- «Sin encuestar» = 0 marcas de encuesta Scout en la celda (`scout_marks_v3.geojson`, sin pines favorito/lock). Las 71 celdas con carnicería tienen 0 marcas, así que este filtro no recorta nada aquí.
- **Orden:** carnicerías en la celda (máx. 2), luego panadería+frutería+mercado en la misma celda (complemento, columna `n_bakery/n_greengrocer/n_marketplace`), luego menor distancia a una de las 167 colonias. Solo hay dos niveles de carnicerías (2 y 1), así que **el orden fino dentro de cada nivel viene de los desempates y no mide demanda**.
- Colonia: la que más se solapa con la celda; si ninguna la toca, la más cercana (distancia en metros desde el centro de la celda, columna `dist_a_colonia_m`).

## 3. Lista de campo (top 30)

Columna «Panad/frut/merc» = panaderías / fruterías / mercados nuevos en la misma celda.

| # | Celda H3 r8 | Carnic. | Panad/frut/merc | Colonia (cercana) | Municipio | Rango base | Comp. v3 ≤300 m | Confianza banda | Mapa |
|--:|---|--:|---|---|---|--:|--:|---|---|
| 1 | `8848a20e13fffff` | 2 | 0/0/0 | Vicente Guerrero 3 Sector | San Nicolás de los Garza | 55 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.75335,-100.25501) |
| 2 | `8848a20f59fffff` | 2 | 0/0/0 | Cañada Blanca | Guadalupe | 59 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.71852,-100.18730) |
| 3 | `8848a20f5dfffff` | 2 | 0/0/0 | Josefa Zozaya 2Do Sector | Guadalupe | 88 | 1 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.71917,-100.17737) |
| 4 | `8848a20a3bfffff` | 2 | 0/0/0 | Villas de San Jose 7 Sector (a 665 m) | Juárez | 27 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.65437,-100.08736) |
| 5 | `8848a204a9fffff` | 2 | 0/0/0 | Fomerrey 115 (San Bernabe 12) (a 672 m) | Monterrey | 19 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.77607,-100.38672) |
| 6 | `8848a20ee1fffff` | 2 | 0/0/0 | Los Fresnos 1Er Sector (a 918 m) | Apodaca | 167 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.76961,-100.24636) |
| 7 | `8848a20e0bfffff` | 2 | 0/0/0 | Valle del Mezquital (a 1,018 m) | San Nicolás de los Garza | 141 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.73090,-100.23820) |
| 8 | `8848a2051dfffff` | 2 | 0/0/0 | Topo Chico (a 1,019 m) | Monterrey | 28 | 1 | alta | [ver](https://www.google.com/maps/search/?api=1&query=25.73382,-100.31331) |
| 9 | `8848a205b9fffff` | 2 | 0/0/0 | Fomerrey 9 (Solidaridad Social) (a 1,053 m) | General Escobedo | 101 | 3 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.79497,-100.33834) |
| 10 | `8848a232c1fffff` | 2 | 0/0/0 | Los Nogales (a 1,207 m) | García | 72 | 1 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.79400,-100.58815) |
| 11 | `8848a20701fffff` | 1 | 2/0/0 | Independencia | Monterrey | 65 | 6 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.67003,-100.32801) |
| 12 | `8848a20e67fffff` | 1 | 2/0/0 | Noria Norte (a 970 m) | Apodaca | 54 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.72536,-100.20282) |
| 13 | `8848a232e1fffff` | 1 | 1/1/0 | Los Encinos Residencial (a 3,161 m) | García | 163 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.80349,-100.56395) |
| 14 | `8848a206c9fffff` | 1 | 1/0/0 | Martires de Cananea | Santa Catarina | 160 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.68586,-100.44413) |
| 15 | `8848a20e8dfffff` | 1 | 1/0/0 | Prados de La Cieneguita | Apodaca | 74 | 6 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.77644,-100.26190) |
| 16 | `8848a20f4dfffff` | 1 | 1/0/0 | Valle Soleado | Guadalupe | 156 | 3 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.70484,-100.15626) |
| 17 | `8848a20ec7fffff` | 1 | 1/0/0 | Los Fresnos 1Er Sector (a 605 m) | Apodaca | 167 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.76831,-100.26623) |
| 18 | `8848a201c5fffff` | 1 | 1/0/0 | Valles del Sol (a 1,294 m) | Guadalupe | 132 | 3 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.65606,-100.18221) |
| 19 | `8848a20e0dfffff` | 1 | 1/0/0 | Valle del Mezquital (a 2,461 m) | San Nicolás de los Garza | 141 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.72406,-100.22267) |
| 20 | `8848a20663fffff` | 1 | 1/0/0 | Fama Iii (a 4,564 m) | Santa Catarina | 38 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.65860,-100.38196) |
| 21 | `8848a20037fffff` | 1 | 0/0/0 | 2 de Mayo | Guadalupe | 102 | 1 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.65412,-100.21197) |
| 22 | `8848a20151fffff` | 1 | 0/0/0 | Rancho Viejo | Juárez | 68 | 7 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.61735,-100.17408) |
| 23 | `8848a20157fffff` | 1 | 0/0/0 | Rancho Viejo | Juárez | 68 | 7 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.62548,-100.16976) |
| 24 | `8848a201c3fffff` | 1 | 0/0/0 | La Playa | Guadalupe | 11 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.66290,-100.19773) |
| 25 | `8848a201cbfffff` | 1 | 0/0/0 | La Playa | Guadalupe | 11 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.65477,-100.20205) |
| 26 | `8848a2055bfffff` | 1 | 0/0/0 | Niño Artillero | Monterrey | 53 | 2 | media | [ver](https://www.google.com/maps/search/?api=1&query=25.71689,-100.33188) |
| 27 | `8848a20565fffff` | 1 | 0/0/0 | Constituyentes de Queretaro 4 Sec | San Nicolás de los Garza | 128 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.71333,-100.26670) |
| 28 | `8848a205abfffff` | 1 | 0/0/0 | Fomerrey 9 (Solidaridad Social) | General Escobedo | 101 | 3 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.78815,-100.32279) |
| 29 | `8848a20611fffff` | 1 | 0/0/0 | Indeco La Fama 1 | Santa Catarina | 20 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.67971,-100.41866) |
| 30 | `8848a2061bfffff` | 1 | 0/0/0 | Union de Colonos | Santa Catarina | 113 | 0 | baja | [ver](https://www.google.com/maps/search/?api=1&query=25.67905,-100.42859) |

Por municipio: Guadalupe 7, San Nicolás de los Garza 4, Monterrey 4, Apodaca 4, Santa Catarina 4, Juárez 3, General Escobedo 2, García 2. Confianza de banda de la colonia: baja 16, media 13, alta 1.

## 4. Lectura y límites

- **Solo 15 de las 30 celdas tocan una de las 167 colonias**, y 17 están a ≤500 m de una (VERIFICADO en el CSV). Las otras caen en zonas de comercio fuera de las colonias de marginación media-alta; sirven como señal de dónde hay comercio de paso, no como candidatas directas. Antes de ir, mirar `dist_a_colonia_m`: la más lejana está a 4,564 m.
- **Cobertura OSM desigual (voluntaria).** 81 carnicerías para toda la ZMM es una fracción del comercio real; DENUE las trae por SCIAN y probablemente muchas más (no lo consulté aquí). Una celda sin punto no es una celda sin carnicería.
- Muchas son cadenas de descuento (SuKarne, El Ofertón de Cantú, Carnes San Juan; 9 de las 30 celdas traen SuKarne o El Ofertón de Cantú): atraen volumen de compra semanal. SUPUESTO que ese volumen cruce con un punto de recarga.
- Solapamiento con la lista anterior (`SCOUT_TOP30_RETAIL.md`): **5 celdas** están en las dos listas (tienda de conveniencia y carnicería juntas); son las más baratas de visitar primero.
- El rango base de la colonia es de contexto; esta lista no persigue el ranking: 6 de las 30 celdas tienen como colonia más cercana una del top 30 base.
- Qué hacer en campo (cuando Nicolás decida): caminar la celda ~15 min, contar peatones y clientes 10 min frente a la carnicería, anotar en Scout (kind `otro`) y revisar recargas informales (`docs/COMPETENCIA_CERO.md`).
- Si se quisiera sumar esto a Anclas\*: no se probó ni se aplicó; requiere decisión de Nicolás.
