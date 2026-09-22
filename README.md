# Mapa Purificadoras (ZMM)

Sitio público del **Mapa Version 2** — site selection de estaciones de recarga de garrafón (~19 L) en la Zona Metropolitana de Monterrey.

**Abrir el mapa:** https://casca-code.github.io/mapa-purificadoras/

## Contenido del repo

| Archivo | Qué es |
|---|---|
| `index.html` | Mapa Leaflet offline (score_100, capas, Ubicarme) |
| `scout-sv.html` | Scout SV embebido (requiere Maps billing; preferir userscript) |
| `userscripts/purificadoras-scout.user.js` | Tampermonkey Scout sobre google.com/maps (**cero** API key; **v1.8.1** giros predeterminados del trayecto, exitBearing 80–120 m, turn-only si desalineado, HUD próx turno) |
| `extension/` + `extension-dist/*.zip` | **REQUERIDA**: ArrowUp/Left/Right vía `chrome.debugger` |
| `data/roads_zmm.geojson` | Calles OSM prebaked (Escobedo) para trayecto scout |
| `scripts/prebake_roads_zmm.py` | Regenera `roads_zmm.geojson` vía Overpass |
| `data/semaforos_zmm.geojson` | Semáforos OSM (ZMM) — capa contexto |
| `data/stops_zmm.geojson` | Altos / yield OSM (ZMM) — capa contexto |
| `scripts/fetch_osm_traffic.py` | Regenera semáforos + stops vía Overpass |
| `docs/` | Notas operativas (anclas, GPS, SADM, bitácora) |
| `README.md` | Este archivo |

Fuente de trabajo local (PC Nicolás): `OneDrive/Desktop/purificadora/version2/`

## Cómo usar en el teléfono

1. Abre el link de Pages en Chrome/Safari.
2. Toca **Ubicarme** y acepta ubicación.
3. Enciende/apaga capas de anclas (Aurrera Express, Soriana Express, cerveza, Bienestar, Azteca) en el rail.

## Actualización

El agente Purificador actualiza MD + HTML y hace push tras cada avance de conversación (regla del 2026-09-12).


## Ruta de campo
Panel **ruta** en el rail: arma un circuito desde casa (Violeta 116, Los Colorines, San Pedro) por colonias del ranking y abre Google Maps. Ver `docs/RUTA_CAMPO.md`.


## Mapa Tec (estudiantes)
https://casca-code.github.io/mapa-purificadoras/tec/ — deptos + Oxxo/Super7 + purificadoras cerca del Campus Monterrey. Ver `docs/MAPA_TEC_ESTUDIANTES.md`.


## Fórmula del score
Cómo se llegó a `score_100`: [`docs/FORMULA_SCORE.md`](docs/FORMULA_SCORE.md).


## Scout (Street View remoto)
**Primario (sin billing):** userscript Tampermonkey sobre Maps de consumidor — [`docs/SCOUT_USERSCRIPT.md`](docs/SCOUT_USERSCRIPT.md) · instalar desde  
`https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js`  
Elige colonia (Escobedo + ZMM) → **Start trayecto** cubre **todas** las calles OSM del polígono (Chinese Postman; sin Maps billing) → marca pines con hotkeys.  
`scout-sv.html` (Maps JS embebido) sigue en Pages pero **requiere Google Cloud billing** — **no usarla**; no pedir key a Nicolás. Camino correcto: userscript **v1.8.1+** + extensión (extensión = pasito; script = mapa de calles + giros; Space = pausa / Start) en `google.com/maps`; extensión **requerida** (`extension/` / `extension-dist/*.zip`). Mapillary abandonado. Legacy: [`docs/SCOUT_SV.md`](docs/SCOUT_SV.md).

## Tránsito OSM (semáforos / altos)
Capas gratuitas de OpenStreetMap en el panel **Anclas → Tránsito**: **Semáforos** y **Altos / stops**.
No son cobertura completa (OSM incompleto en ZMM); no puntúan. Para marcas manuales en campo sigue usando Scout **S**.
Refrescar datos: `python3 scripts/fetch_osm_traffic.py` → commit de `data/semaforos_zmm.geojson` + `data/stops_zmm.geojson`.

