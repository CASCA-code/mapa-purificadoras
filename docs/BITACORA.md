## 2026-09-21 (scout v1.7.3 — sin flicker speed + destrabado)

- Speed: botones −/+ (sin range); se quitó `blurHudInputs`/`withHudInputLock` que parpadeaba el HUD en cada step de la extensión.
- Stuck: `routeBusy` watchdog ~5.5s; POV hard timeout; pose sin cambio N pasos → U-turn una vez luego skip; toast `destrabado`.
- Look-ahead cruces (exit bearing) de 1.7.2 se mantiene. Reinstall `?v=173`.

## 2026-09-21 (scout v1.7.2 — speed fijo + look-ahead cruces)

- Nicolás: velocidad “subía sola” porque ArrowLeft de la extensión también golpeaba el `<input type="range">` enfocado.
- Fix: blur/disable inputs HUD antes de cada `ext` step; `tabindex=-1`; ignore Arrow*/Home/End en el slider (`preventDefault`+`stopImmediatePropagation`); solo drag de puntero cambia speed; persist GM+localStorage.
- Cruces: annotate `turnDeg`/`exitBearing` en waypoints; ~55 m antes de |giro|≥35° alinea POV a la **salida** del trayecto (bursts extra); HUD `↳ der` / `↰ izq`.

## 2026-09-21 (scout v1.7.0 — POV rota hacia trayecto antes de avanzar)

- Feedback Nicolás v1.6: walking OK-ish, pero POV “gira” débil y sigue mirando el forward viejo → ↑ va mal.
- Fix: userscript alinea POV (`step({turnDeg, forward:false})` + poll heading URL, max 2 bursts extra) **antes** de ArrowUp; U-turn ~180° real; HUD `POV 120°→85°`.
- Extensión **1.5.1**: DEG_PER_TURN_KEY≈9°, settle 320 ms entre giros y Up, un attach para turn+wait+Up, mouse-drag backup; zip refreshed.
- Cobertura colonia (Chinese Postman) de v1.6 intacta.

## 2026-09-21 (scout v1.5.0 — extensión PRIMARY / trayecto auto)

- Nicolás: flecha userscript no movía; necesitaba walk fully automatic por trayecto de colonia.
- Realidad: clicks/teclas untrusted fallan. Solo extensión `chrome.debugger` ArrowUp/Left/Right es confiable → **PRIMARY (requerida)**.
- Extensión v1.5: burst attach→keys→detach; API `step({turnDeg})` / turnLeft / turnRight / ping; zip en `extension-dist/purificadoras-scout-ext.zip`.
- Userscript v1.5: detecta ext (HUD verde/rojo); cada tick llama extensión PRIMERO; pace ~800 ms; Start→entra 1× URL→loop sin clicks hacia waypoints; Space=pausa; progreso `colonia · i/n · ext`.
- Docs ES: instalar extensión ANTES de esperar walk.

## 2026-09-21 (scout userscript v1.4.0 — flecha SV)

- Feedback Nicolás: `map_action=pano` saltaba demasiado lejos → pantalla negra cada paso.
- Fix: Space / auto-walk / trayecto usan **flecha SV** (paso suave in-panorama: click chevron / pointer / ArrowUp). URL-pano solo 1× entrada a colonia o recovery raro.
- HUD: `flecha SV`. ▶ Siguiente = un paso flecha (no teletransporte).
- Extensión Chrome opcional `extension/` (debugger ArrowUp) si Maps ignora eventos untrusted.
- Docs: `docs/SCOUT_USERSCRIPT.md` explica flecha vs teletransporte.

## 2026-09-21 (scout userscript v1.2.1)

- Falso positivo “sin API key” + trayecto que moría al primer waypoint (`location.assign` sin persistir ruta).
- Fix: persist/resume trayecto, URL `/@lat,lng,3a,…`, HUD “usa google.com/maps (NO scout-sv)”. Cero Maps Platform key.

# Bitácora Purificadoras

## 2026-09-14 / 15 (campo + slim móvil)

- **Slim map** `67cf5f9`: `index.html` ~161 KB; GeoJSON en `data/`; tiles Carto→OSM→Esri; SW cache para celular MX.
- Live: https://casca-code.github.io/mapa-purificadoras/?v=67cf5f9
- **Ubicarme**: punto sigue GPS; mapa centra una vez; Parar; freeze GPS al abrir sheet.
- Dock campo ★ / ＋ / Comp; sync `field_adds` vía ntfy; anclas one-tap.
- **CRM pins**: Ezequiel (Taller esquinita, 81 1060 2066 @ 25.726089,-100.331291); Luis Volkswagen (81 1525 3207 @ 25.733938,-100.328697) — nombre+tel en Nosotros/Fav.
- **Liked**: cluster Estanzuela Fomerrey 45; Topo Chico / Niño Artillero; Timoteo `liked_rejected` (rechazo fuerte).
- Agente **Psicología** en equipo Purificadoras (embudo permiso pared / Carnegie).
- Recordatorio: llamada barbacoa **miércoles**.



## 2026-09-13 (mapa Tec + Centro)

- Expandido `/tec/` a Tec + Centro (Independencia excluida). ~90 deptos, Oxxo/7-Eleven, puris GMaps.
- Demográfica distinta a ZMM D+/D: estudiantes (Tec) vs mayor ingreso (Centro).


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
