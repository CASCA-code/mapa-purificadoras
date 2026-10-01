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
4. **Personas** (0–1) = 0.6 × percentil de *densidad* + 0.4 × flujo peatonal modelado EG-personas (`pie_score` del segmento más cercano ≤80 m; si no hay, solo densidad). Densidad = peso propio de la parada (bus 1, BRT 2, metro/terminal 3) + otras paradas ≤150 m (tope 15) + anclas ≤150 m (escuela, iglesia, hospital, banco Bienestar/Azteca, Oxxo, Express; tope 15 c/u; peso 1).
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
