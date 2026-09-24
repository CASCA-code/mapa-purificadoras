# Mapa Purificadoras (ZMM)

Sitio público del **Mapa Version 2** — site selection de estaciones de recarga de garrafón (~19 L) en la Zona Metropolitana de Monterrey.

**Abrir el mapa:** https://casca-code.github.io/mapa-purificadoras/

## Contenido del repo

| Archivo | Qué es |
|---|---|
| `index.html` | Mapa Leaflet offline (score_100, capas, Ubicarme) |
| `scout.html` | **Scout** Maps JS + Dynamic Street View (key en `config/maps-key.js`, cero paste) |
| `config/maps-key.js` | Key Maps JS embebida (restringir referrer `https://casca-code.github.io/*`) |
| `scout-sv.html` | Redirect → `scout.html` |
| `userscripts/purificadoras-scout.user.js` | Tampermonkey Scout sobre google.com/maps (**cero** API key; **v1.9.1** F Favorito + Y precios; Avenidas-first vs Todo) |
| `extension/` + `extension-dist/*.zip` | **REQUERIDA**: ArrowUp/Left/Right vía `chrome.debugger` |
| `data/roads_zmm.geojson` | Calles OSM prebaked (Escobedo) para trayecto scout |
| `scripts/prebake_roads_zmm.py` | Regenera `roads_zmm.geojson` vía Overpass |
| `data/semaforos_zmm.geojson` | Semáforos OSM (ZMM) — capa contexto |
| `data/stops_zmm.geojson` | Altos / yield OSM (ZMM) — capa contexto |
| `scripts/fetch_osm_traffic.py` | Regenera semáforos + stops vía Overpass |
| `data/places_anclas_zmm.geojson` | Anclas comerciales Places API (New) — Modelorama/Bodega Aurrera Express/Oxxo/… |
| `scripts/fetch_places_anclas_zmm.py` | Regenera Places anclas (key vía `.env` o `config/maps-key.js`) |
| `data/places_prestamos_zmm.geojson` | Anclas Places API — préstamo / casas de empeño / financiera |
| `scripts/fetch_places_prestamos_zmm.py` | Regenera Places préstamos (key vía `.env` o `config/maps-key.js`) |
| `docs/` | Notas operativas (anclas, GPS, SADM, bitácora) |
| `README.md` | Este archivo |

Fuente de trabajo local (PC Nicolás): `OneDrive/Desktop/purificadora/version2/`

## Cómo usar en el teléfono

1. Abre el link de Pages en Chrome/Safari.
2. Toca **Ubicarme** y acepta ubicación.
3. Anclas comerciales (Places) y Préstamos / casas de empeño van **apagadas por defecto**; enciéndelas en el rail cuando las necesites (Bodega Aurrera Express, Modelorama, Oxxo, bancos, farmacias, empeño…).

## Actualización

El agente Purificador actualiza MD + HTML y hace push tras cada avance de conversación (regla del 2026-09-12).


## Ruta de campo
Panel **ruta** en el rail: arma un circuito desde casa (Violeta 116, Los Colorines, San Pedro) por colonias del ranking y abre Google Maps. Ver `docs/RUTA_CAMPO.md`.


## Mapa Tec (estudiantes)
https://casca-code.github.io/mapa-purificadoras/tec/ — deptos + Oxxo/Super7 + purificadoras cerca del Campus Monterrey. Ver `docs/MAPA_TEC_ESTUDIANTES.md`.


## Fórmula del score
Cómo se llegó a `score_100`: [`docs/FORMULA_SCORE.md`](docs/FORMULA_SCORE.md).


## Scout (Street View remoto)
**Primario (Maps JS):** https://casca-code.github.io/mapa-purificadoras/scout.html — Dynamic Street View + trayecto OSM avenidas/todo, hotkeys, sync ntfy. Key embebida en `config/maps-key.js` (cero paste). Docs: [`docs/SCOUT.md`](docs/SCOUT.md). Restringir referrer a `https://casca-code.github.io/*`.

**Fallback (sin Maps Platform):** userscript Tampermonkey + extensión Chrome sobre `google.com/maps` — [`docs/SCOUT_USERSCRIPT.md`](docs/SCOUT_USERSCRIPT.md) · raw  
`https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js?v=191`  
(v1.9.1 Favorito+precios; extensión **1.6.1** requerida para el pasito).

## Tránsito OSM (semáforos / altos)
Capas gratuitas de OpenStreetMap en el panel **Anclas → Tránsito**: **Semáforos** y **Altos / yield**.
La consulta incluye `highway=traffic_signals` en nodos/vías y `crossing=traffic_signals` (cruce señalizado), además de `highway=stop|give_way` y `traffic_sign=stop` en nodos/vías. No son cobertura completa (OSM incompleto en ZMM); no puntúan. Para marcas manuales de campo sigue usando Scout **S**.
Refrescar datos: `python3 scripts/fetch_osm_traffic.py` → commit de `data/semaforos_zmm.geojson` + `data/stops_zmm.geojson`.

