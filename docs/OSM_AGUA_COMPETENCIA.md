# OSM agua (drinking_water / shop=water) vs competencia_v3 + mapa de calor interno

Fecha: **2026-10-02**. Etiquetas: VERIFICADO = visto en el archivo citado; SUPUESTO = inferencia. **No altera ningún score.** Scripts: `scripts/analisis_osm_agua_zmm.py`, `scripts/build_heat_competencia_300m.py` (ambos sin red; la descarga fue manual con curl).

## 1. Descarga (Overpass, pública, ODbL)

- bbox lat 25.52..25.92, lon −100.70..−100.00. Mirrors: `overpass-api.de` (sin respuesta/timeout) y `overpass.kumi.systems` (504) fallaron; **`overpass.private.coffee` respondió 200** (2 consultas, 1 por vez, pausa >15 s, User-Agent propio). Timestamp de datos OSM del mirror: **2026-07-15T15:22Z** (VERIFICADO en el JSON).
- Consulta 1: `amenity=drinking_water`, `shop=water|water_purification|water_refill`, `amenity=water_point`, `craft=water_purification`, nombres con «purificad|garraf|agua pura|aqua|hielo». Consulta 2: `vending=water`, `vending_machine` con nombre de agua, tiendas con nombre «agua purificada/purificadora/garrafón/agua pura/agua y hielo».
- Raw (fuera del repo): `/workspace/downloads/osm_agua_zmm_raw.json` (30 elementos únicos; también `_q1.json`, `_q2.json`). Procesado: `v2/data/osm_agua_zmm.geojson`.
- **Resultado (VERIFICADO):** 30 elementos = **6 competidores**, **16 bebederos públicos** (`amenity=drinking_water`: fuentes/grifos de parques, Chipinque… **no son competidores**), **8 descartados** (nombre con regex pero no es venta de agua: pista de hielo, motel Aqua, calles Aqua, etc.). **`shop=water_purification` y `shop=water_refill`: 0 elementos** en toda la ZMM.

## 2. Comparación con competencia_v3 (541 puntos: 466 Places + 75 DENUE; dedupe 30 m)

| OSM | Nombre | Clase | Dist. al punto v3 más cercano | ¿Nuevo (>30 m)? | Colonias (de las 167) a ≤300 m del polígono |
|---|---|---|--:|---|---|
| node/6395186135 | (sin nombre) `shop=water` | competidor | 1 213 m | sí | ninguna |
| node/10810771827 | Agua Purificada Elite (vending) | competidor | 10 m | **no** (ya en v3) | ninguna |
| node/13626122401 | Agua Purificada (`drinking_water`) | competidor (por nombre) | 398 m | sí | ninguna |
| node/13915165758 | Agua Purificada (vending, Enrique H. Herrera 1214) | competidor | 409 m | sí | **Alfonso Reyes**, La Altamira |
| way/1000307510 | (sin nombre) `shop=water` | competidor | 827 m | sí | **Noria Norte**, **Cañada Blanca** |
| way/1056798363 | The Water House `shop=water` | competidor | 173 m | sí | ninguna |

- **OSM aporta 5 competidores NUEVOS** (de 6; 1 duplica a v3). Solo **2 puntos nuevos caen en colonias de las 167** (a ≤300 m del polígono, misma regla de v3): afectan a **4 colonias** (Alfonso Reyes #64, La Altamira #89, Noria Norte #54, Cañada Blanca #59). Las otras 3 caen fuera del universo de 167.
- **Impacto en los «58 ceros» (VERIFICADO con `colonias_competencia_cero.csv`):** solo **1 colonia sale del cero: Alfonso Reyes (#64)**, 0 → 1 competidor ≤300 m (clasificada «indeterminado_inclina_brecha»). Quedan **57 ceros**. Las otras 3 ya tenían ≥1 (La Altamira 2, Noria Norte 1, Cañada Blanca 2 → pasarían a 3, 2, 3). No se recalculó ni se cambió score.
- **Lectura (SUPUESTO):** OSM es casi inútil como fuente de competencia (6 puntos vs 541): confirma que los informales no están mapeados; no sirve para «arreglar» los ceros. Sí sirve como señal puntual de vending/auto-servicio no presente en DENUE/Places.

## 3. Mapa de calor interno

- Datos: `v2/data/heat_competencia_300m.csv` — celdas de **100 m**; columnas `lat,lon` (centro), `n_comp_300m`, `n_v3`, `n_osm_nuevo`, `cve_col_centro`. Cuenta competidores a ≤300 m **del centro de celda** (distancia plana, km/grado a lat 25.7). Se emiten celdas con n≥1 o con centro en polígonos de colonias +300 m (para ver los ceros): **28 799 celdas**, 12 980 con ≥1; distribución n: 0=15 819, 1=10 855, 2=1 839, 3=236, 4=48, 5=2 (VERIFICADO en el CSV).
- Página: `v2/competencia_heat.html` (Leaflet local de `../vendor`, base Esri World_Street_Map, celdas dibujadas en canvas; no usa carto/osm tiles). **No enlazada desde el hub.** Muestra «indicativo, competencia subcontada».
- URL en vivo: https://casca-code.github.io/mapa-purificadoras/v2/competencia_heat.html
- Límite: es un conteo bruto; no pesa por distancia ni por tipo (planta vs recarga). Con 541 puntos y mayoría Places, la densidad refleja también dónde Google tiene fichas.
