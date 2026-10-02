# v3_espectaculares — paradas exactas + tráfico + dirección (INDICATIVO)

Copia pequeña y separada para Nicolás: ¿dónde conviene un **espectacular** (visible, con gente esperando y autos pasando) en la ZMM?
Mapa: https://casca-code.github.io/mapa-purificadoras/v3_espectaculares/ · Volver a [/v2/](../v2/).
No modifica `index.html`, `scout.html`, `v2/`, `data/` ni los scripts de merge. Build: `python3 scripts/build_espectaculares.py` (offline, **sin llaves, sin APIs de pago**; Overpass es gratis).

## Pregunta de Nicolás: ¿se consideraron las paradas EXACTAS de camión/metro para cerrar un espectacular?
**Antes (v2): NO.** v2 usó las paradas solo como (a) *conteo* dentro de 150 m / 100 m de cada celda o colonia (ancla "parada de camión", peso 0.75/1.0) y (b) la clase de vía OSM (índice 1–5) como proxy de tráfico. No evaluó parada por parada, ni visibilidad, ni el **sentido de circulación**. **Estaciones de Metrorrey y BRT/Ecovía/Transmetro no estaban** en los datos.
**Ahora (v3): SÍ**, con un modelo transparente (abajo). Sigue siendo proxy; no hay aforos.

## Dato importante (corrección)
`data/stops_zmm.geojson` = **38 señales de ALTO** (stop signs), NO paradas de camión. Las paradas reales son `data/anclas_paradas_zmm.geojson` (2,005: Places 1,438 · OSM 545 · ambos 22). No se usó `stops_zmm` aquí.

## Fuentes de paradas (fusionadas, 2,114 sitios)
| Fuente | Qué | Notas |
|---|---|---|
| OSM Overpass (nuevo, `scripts/fetch_osm_paradas_espectaculares.py` → `/workspace/downloads/osm_paradas_raw.json`) | estaciones Metrorrey (subway/light_rail, L1/L2/L3 + L4 monorriel + L6 BRT en construcción excluida), Ecovía/Transmetro (`amenity=bus_station`, network), terminales, `highway=bus_stop` con `ref/route_ref/network/direction` si existen | snapshot OSM 2026-07-28; mapeo voluntario, **parcial** |
| `data/anclas_paradas_zmm.geojson` | bus stops Places (nombre tipo "MTY-0718 Av. X NTE-SUR") + OSM | dedupe 20 m (prioridad OSM > Places); Places `transit_station` sin match OSM ≤200 m se trata como estación metro |
Resultado: bus 1,961 · metro 56 · BRT/Ecovía 61 · terminal 36 (OSM 779, Places 1,327, anclas-OSM 8). Estaciones multi-elemento (andenes/entradas/stop_position) se agrupan en un sitio (200 m). Casi ninguna parada OSM trae `route_ref`: **no se conoce la ruta/frecuencia** de la mayoría.

## Modelo (todo en `PARAMS` del script; pesos de JUICIO, no calibrados)
1. **Zona de visibilidad candidata:** círculo de **80 m** (parada) / **150 m** (metro, BRT, terminal).
2. **Vías adyacentes:** aristas OSM dentro del radio (calles mayores desde Overpass con `oneway/ref/name`, v2 `trafico_vias` para dibujo; `data/roads_zmm.geojson` para calles locales, sin sentido ni nombre). Se toma la vía de mayor índice (desempate: más cercana). Índice = clase OSM como en v2: troncal/autopista 5, primaria 4, secundaria 3, terciaria 2, enlace 1.
3. **Dirección:** `oneway=yes`/autopista/rotonda = un sentido (rumbo calculado de la geometría); `oneway=-1` invertido; sin etiqueta = **doble sentido** (ambos rumbos). Bulevares con 2 calzadas OSM separadas → se listan ambos sentidos. El cartel debe **mirar contra el flujo** (rumbo del flujo + 180°) para ser visto por autos que llegan. En el mapa: flechas negras = flujo, líneas verdes = hacia dónde mirar.
4. **Personas** (0–1) = 0.6 × percentil de *densidad* + 0.4 × flujo peatonal modelado EG-personas (`pie_score` del segmento más cercano ≤80 m; si no hay, solo densidad). Densidad = peso propio de la parada (bus 1, BRT 2, terminal 3, **metro = 6 × índice de afluencia, 3 si no hay dato; ver «Actualización 2026-10-01»**) + otras paradas ≤150 m (tope 15) + anclas ≤150 m (escuela, iglesia, hospital, banco Bienestar/Azteca, Oxxo, Express; tope 15 c/u; peso 1).
5. **Autos** = (índice de vía / 5) × multiplicador pico municipal. Multiplicador = promedio de mediana(07:00/22:00) y mediana(18:00/22:00) del municipio (TomTom indicativo); si el municipio no tiene dato (Monterrey, San Nicolás, San Pedro) se usa el **total ZMM (1.19)** y se marca.
6. **Score** = personas × autos, normalizado 0–100 (máx = 100). Ranking top 100 con supresión de sitios a <200 m (se cuenta cuántos se fusionaron).
Salida: `data/paradas_candidatas_top100.{geojson,csv}` (id, nombre/ruta, lon/lat, vía + clase, sentido/rumbo, partes del score, link Google Maps y Street View, banderas de cautela).

## Tráfico de autos: qué se usó y qué NO
- **v2 índice de vía 1–5** (`data/trafico_vias.geojson`, 1,860 tramos): proxy por clase OSM. **No es aforo.**
- **TomTom (EG-fabricas)**: 228 pares OD industriales (hub de mano de obra → fábrica / fábrica → rampa), 6 horarios, **1 día típico (mar 2026-10-06, perfil histórico)**. NO son conteos por calle. Solo se usa como *multiplicador pico indicativo por municipio* = mediana de (tiempo a la hora / tiempo 22:00) por par. Etiqueta en mapa: **"TomTom indicativo, 1 día, uso interno"**.
- **Decisión de publicación (GitHub Pages es PÚBLICO):** se publican **solo agregados** (mediana por municipio y slot, n de pares; grupos <4 pares omitidos) en `data/tomtom_muni_indicativo.geojson` / `manifest.json`. **NO** se publican coordenadas OD, ids de tramo ni muestras crudas (los ToS de TomTom limitan redistribuir datos; el crudo queda en `/home/box/geo/trafico/trafico.db`, solo lectura). Cobertura: 13 municipios en el db; de los del mapa de Purificador, Monterrey, San Nicolás y San Pedro no tienen pares → usan total ZMM (los demás tienen 7–42 pares). Los pares son corredores industriales (Apodaca, Escobedo, Santa Catarina…), **no representan** centro/avenidas urbanas.
- Cero llamadas a TomTom/Google/Places en este trabajo.

## Gente (anclas)
2,726 anclas (escuela/iglesia/hospital de `data/anclas.geojson` + banco/Oxxo/Express/escuelas extra de `v2/data/anclas_v3.geojson`, dedupe por celda y tipo). EG-personas `segmentos_general.csv` (259,747 tramos, modelo) → solo se envían los **top 2,000** (~100 KB) como capa de contexto; archivos del mapa todos <1.2 MB (`trafico_vias.geojson` es copia de v2, 0.94 MB).

## Qué FALTA (honesto)
- **Aforos/conteos reales** de autos (SINTRAM/INEGI/SCT, HERE, TomTom Flow por vía) y de peatones (conteos de campo; Mapbox Movement/Telcel/Movistar con cotización).
- Estaciones **Metrorrey** completas y **Transmetro/Ecovía/Metrobús** dependen de OSM (mapeo voluntario; L6 en construcción excluida; paradas de ruta sin ruta/frecuencia). Places parcial (tope 60 por tile; nombres sin ruta).
- **Visibilidad real**: lado de la calle del andén, altura/ángulo, derecho de vía, cruces con semáforo (cola = más tiempo de exposición), obstrucciones. El rumbo sale de la geometría OSM (±10°) y puede errar en nodos/curvas.
- **Disponibilidad y renta** de espectaculares existentes (inventario de proveedores, permisos municipales/SEDUE).
- Pico por hora de cada **parada** (frecuencia de rutas, GTFS de Nuevo León si existe).
- Pesos del score no calibrados; mult. TomTom es de OD industriales (otros municipios usan total ZMM).
- Validación en campo (Scout/Street View con los links del top 100).

## Actualización 2026-10-01: Metro con afluencia real (reemplaza el peso de juicio Metro = 3)
**Qué cambió.** Antes el peso propio de una estación Metro era **3.0 fijo** (juicio). Ahora, para estaciones con dato, `peso_propio = W_MAX × índice_afluencia`, con `índice = accesos/día hábil (nov-2025, STC Metrorrey) ÷ máximo de la red` (0–1) y `W_MAX = 6` (parámetro `metro_afluencia.w_max` en `PARAMS`; **escala de juicio, no calibrada**: la estación más usada pesa 6, el doble del 3 anterior). El resto del score (otras paradas ≤150 m, anclas, vía, TomTom, percentil de densidad, flujo peatonal modelado) **no cambió**. Script: `scripts/build_espectaculares.py` (offline). Copia del top 100 anterior: `data/paradas_candidatas_top100_prev.csv`.

**Cruce.** Por proximidad ≤250 m entre la coordenada de cada estación del archivo y los elementos tipo `metro` del mapa (cada elemento recibe la estación más cercana) + verificación de nombre. Resultado: **38/38 estaciones del archivo con match** (38 elementos del mapa; nombre coincide en 36). Dudas de match: «Ruiz Cortines» ↔ OSM «Ruiz Cortinez» (ortografía, a 249 m, en el límite); «Parque Fundidora» ↔ OSM «Arena Monterrey» a 16 m (nombre distinto, misma ubicación). **Sin match: 18 elementos `metro` del mapa** que no están en el archivo (nombres OSM: Parque Fundidora, Churubusco, Lindavista, Libertad, Bonifacio Salinas, San Rafael, La Victoria, La Talaverna, La Fe, Ginecología, Puente del Papa, Macroplaza, Serafin Pena, Pino Suárez, Fuerza Civil, Obispado / Torre Rise, Barrio Antiguo, Estación OSM sin nombre); el archivo sólo trae 38 estaciones (L1/L2/L3 y transbordos), así que probablemente son de líneas nuevas/en construcción u otros elementos OSM [no verificado]. Siguen con el peso de juicio 3.0 y llevan la bandera `metro_sin_afluencia(peso_juicio=3)`; **12 de ellos están en el nuevo top 100** (ranks 7, 21, 26, 27, 37, 39, 46, 47, 48, 54, 95, 100), incluido #7 «Ginecología»: ese lugar depende del 3.0 de juicio, no de afluencia.

**Antes → después (top 10).**

Antes (peso 3 fijo):

| # | Parada | Tipo | Municipio | Score |
|--:|---|---|---|--:|
| 1 | Universidad | metro | San Nicolás de los Garza | 100.0 |
| 2 | Unión de Permisionarios Ruta 301, S.C. (Ruta 301) | terminal | Monterrey | 91.9 |
| 3 | Cuauhtémoc | metro | Monterrey | 89.9 |
| 4 | (sin nombre) | bus | Apodaca | 88.2 |
| 5 | (sin nombre) | bus | Apodaca | 87.6 |
| 6 | Estación OSM sin nombre | terminal | Monterrey | 86.1 |
| 7 | Ginecología | metro | Monterrey | 85.5 |
| 8 | Fundadores | metro | Monterrey | 84.9 |
| 9 | Alameda | metro | Monterrey | 84.4 |
| 10 | Lerdo de Tejada | metro | Guadalupe | 82.0 |

Después (afluencia):

| # | Parada | Tipo | Municipio | Score |
|--:|---|---|---|--:|
| 1 | Universidad | metro | San Nicolás de los Garza | 100.0 |
| 2 | Cuauhtémoc | metro | Monterrey | 95.5 |
| 3 | Unión de Permisionarios Ruta 301, S.C. (Ruta 301) | terminal | Monterrey | 88.1 |
| 4 | (sin nombre) | bus | Apodaca | 85.7 |
| 5 | (sin nombre) | bus | Apodaca | 85.0 |
| 6 | Sendero | metro | General Escobedo | 83.7 |
| 7 | Ginecología | metro | Monterrey | 83.3 |
| 8 | Fundadores | metro | Monterrey | 82.4 |
| 9 | MTY-0718 Av. Eugenio Garza Sada NTE - SUR | bus | Monterrey | 80.3 |
| 10 | Estación OSM sin nombre | terminal | Monterrey | 80.3 |

Top 10 en común: 8/10; top 100 en común: 67/100. Tipos en el top 100: antes bus 51 · metro 31 · terminal 14 · BRT 4; después bus 58 · metro 23 · terminal 15 · BRT 4. Sube **Sendero** (#87 → #6, la estación con más accesos) y baja el grupo de estaciones de baja afluencia (p. ej. Santiago Tapia #29 → #99, San Nicolás #56 → #85; Moderna, Eloy Cavazos, Regina, Niños Héroes, General Anaya, Central, Y Griega, Del Golfo, Colonia Obrera salen del top 100).

**Caveats.**
- Los accesos son entradas al sistema de **un mes** (nov-2025), no personas esperando ni visibilidad desde la calle; una estación muy usada puede estar en una vía sin espacio para cartel.
- `W_MAX = 6` es juicio. La forma lineal (índice ÷ máximo) deja la afluencia muy sesgada hacia pocas estaciones; no está probado contra ninguna medición de visibilidad/ventas.
- Mezcla de escalas: estaciones sin dato conservan 3.0 (ver arriba) y quedan por encima de la afluencia mediana de las estaciones con dato.
- **Datos de uso interno:** el archivo fuente `personas_export/metro_estaciones_afluencia.csv` (conteos crudos) **no se publica**. Aquí sólo va el **índice normalizado por estación** (`data/metro_afluencia_indice.csv`: estación, línea, coordenada, índice 0–1) y la bandera `metro_afluencia_idx=…` en el top 100. No hay conteos crudos en ningún archivo de este directorio.
- Si el archivo fuente no está en la máquina, el script usa el índice derivado (aviso en consola); sin ninguno, vuelve al 3.0.
