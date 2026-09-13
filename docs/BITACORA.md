# Bitácora Purificadoras

## 2026-09-13 (basemap Tec sin API)

- `/tec/`: quitamos CartoCDN; tiles **OpenStreetMap** sin API key.


## 2026-09-13 (fórmula documentada)

- `docs/FORMULA_SCORE.md`: historia v1→v2, pesos, anclas, link https://casca-code.github.io/mapa-purificadoras/


## 2026-09-13 (mapa Tec estudiantes)

- Nuevo mapa aparte en `/tec/`: deptos OSM + Oxxo/7-Eleven + puris (pocas) alrededor Campus Monterrey.
- Población de edificios: desconocida. Purificadoras OSM incompletas — falta campo/DENUE.


## 2026-09-12 (ruta de campo · capa B)

- Panel **ruta** en el mapa: top N / picks → TSP cerrado casa→paradas→casa → polilínea + Abrir en Google Maps.
- Casa fija: Violeta 116, Los Colorines, San Pedro. Docs: `docs/RUTA_CAMPO.md`.


## 2026-09-12 (escuelas / bancos / etiquetas)

- Fix: submenú Escuelas y Retail/bancos tenían `style="display:none"` que ganaba a `.open` → no se veían ni prendían.
- Al abrir la fila (o el ícono maestro vacío) se encienden todos los subtipos y se dibujan en el mapa.
- Etiquetas de municipio **ON** por default.


## 2026-09-12 (z-index menú izq)

- Rail / panelHost (score, base, capas) por encima del geoPanel de Ubicarme para que no los tape.


## 2026-09-12 (Ubicarme nombre siempre)

- Ubicarme muestra **siempre** el nombre de la colonia (en estudio = polígono; fuera = reverse Nominatim).
- Rank/score/detalle del estudio **solo** si está en las 167; fuera: nombre + “sin datos”, sin inventar score.
- Tocar el panel geo abre ficha solo si hay datos de estudio.


## 2026-09-12 (sheet Colonias)

- Swipe para cerrar solo en la **rayita**/handle de arriba; scrollear la lista ya no cierra el sheet.


## 2026-09-12 (cuadrito colonia)

- Al tocar colonia el `map.click` cerraba el `#coloniaCard` en el mismo gesto.
- Fix: `stopPropagation` en polígono; card arriba (safe-area, z-index 1500, scroll); `hideDetail` ya no se llama a sí misma.


## 2026-09-12 (hotfix mapa caído)

- Causa: `zoomControl:false` + `map.zoomControl.setPosition(...)` → TypeError y el script moría (sin capas, sin Colonias, sin Ubicarme).
- Fix: quitar `setPosition`; Leaflet/heat desde `vendor/` (sin CDN).
- Commit `f40afc3` en `CASCA-code/mapa-purificadoras`; Pages rebuilt.
- Sync local: `version2/mapa_purificadoras_version2.html` + `version2/vendor/`.


## 2026-09-12 (lista completa)

- Ranking en sidebar: **todas** las colonias (no solo top 15) + buscador.
- Botón **Color chico**: relleno del mapa más suave (fillOpacity 0.22) y chips más pequeños.

## 2026-09-12 (layout móvil)

- Mapa a pantalla casi completa en teléfono.
- Sidebar “Colonia objetivo” → bottom sheet **Capas y ranking** (colapsado; tocas para abrir).
- Ficha GPS compacta arriba (fuera del estudio = 2 líneas).

## 2026-09-12 (tarde)

- Default del mapa: **solo colonias score ON**; competencia, anclas (OSM + retail/bancos), etiquetas **OFF** (el usuario prende lo que quiere ver).
- Ubicarme: `getCurrentPosition` al tocar (dispara Allow) + `watchPosition`; reintento sin high-accuracy; mensajes de error por código; meta Permissions-Policy.

## 2026-09-12

- Default del mapa: **solo colonias score ON**; competencia, anclas (OSM + retail/bancos), etiquetas **OFF** (el usuario prende lo que quiere ver).
- Ubicarme: `getCurrentPosition` al tocar (dispara Allow) + `watchPosition`; reintento sin high-accuracy; mensajes de error por código; meta Permissions-Policy.

- Publicado mapa v2 en GitHub Pages: https://casca-code.github.io/mapa-purificadoras/
- Anclas retail/bancos (118 pts) + pesos en Anclas\*; capas A/S/C/B/Z.
- Ubicarme (GPS vivo + ficha rank) en el HTML.
- Top 10 v2 estable tras anclas nuevas.
- Tarifas SADM documentadas (Croc, ósmosis, doméstica vs comercial).
- Standing ops: actualizar MDs del folder y push a GitHub tras cada avance, sin pedir ok de público.
- Descartado: casas abandonadas, capa haitianos.

## Regla permanente

Después de cada conversación con avance: actualizar MD(s) aquí y en `version2/`, commit + push al repo `CASCA-code/mapa-purificadoras` (y copiar HTML a Pages).
