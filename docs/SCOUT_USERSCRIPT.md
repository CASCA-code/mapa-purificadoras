# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21 (v1.2.1)

> **Camino primario para Nicolás.** Corre **sobre** Google Maps de consumidor (`https://www.google.com/maps` Street View).  
> **Cero** Google Cloud / Maps Platform API key / hold de facturación. Si ves un mensaje de “API key”, **actualiza el userscript** (v1.2.1+) — ese aviso era un falso positivo o estabas en `scout-sv.html`.  
> **Usa siempre `google.com/maps` + peoncito.** No abras `scout-sv.html` (esa página sí pide key/billing).  
> Mapillary: abandonado.

## Qué es

Extensión de usuarios (Tampermonkey) que, mientras ves **Street View** en el Maps normal del navegador, te deja soltar los mismos pines / comentarios de zona que el mapa de campo, con las mismas teclas que Scout SV.

- Human-in-the-loop: tú miras el panorama y decides qué marcar.
- No scrapea negocios ni cachea imagery de Street View — solo GeoJSON (coords + props).
- Sync **primario: ntfy** (el userscript en `google.com` **no** puede compartir `localStorage` con `casca-code.github.io`).
- **v1.1:** picker de colonia + **trayecto** de cobertura vial (OSM Overpass) + auto-walk más fiable.
- **v1.2.1:** trayecto **persiste** tras cada salto de URL; navegación `/@lat,lng,3a,…` (sin ruido `?api=1`); fallback ArrowUp; HUD aclara “sin API key = correcto, usa Maps consumidor”.
- **v1.2:** calles **prebaked** (`data/roads_zmm.geojson`) para Escobedo — ya no depende de Overpass en vivo para colonias comunes; Overpass con timeout duro + mirrors + **Reintentar**; fallback rejilla; búsqueda fuzzy de colonia.

## Instalación (Chrome / Edge / Firefox)

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)** (u otro gestor compatible con Greasemonkey).
2. En Tampermonkey → **Utilidades** → **Instalar desde URL**, pega:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js
   ```

   Alternativa: abre esa URL → Tampermonkey ofrece **Instalar**.
3. Confirma permisos (`ntfy.sh`, Maps, `casca-code.github.io`, Overpass, raw GitHub).
4. Abre **[Google Maps](https://www.google.com/maps)** (no `scout-sv.html`) → arrastra el **peoncito** naranja a una calle de la ZMM (Street View).
5. Debe aparecer el **HUD** (arriba-izquierda) con la línea verde **“Sin API key · usa google.com/maps”** y el **mini-peg** (abajo-izquierda).
6. Si el HUD no aparece o habla de API key: Tampermonkey → actualizar script a **v1.2.1+** desde la URL raw de arriba.

Actualizar: Tampermonkey suele detectar la nueva versión en el raw de GitHub; o reabre la URL e “Actualizar”.

## Flujo recomendado (colonia → trayecto → pines)

1. En el HUD, **busca / elige una colonia** (lista prioriza **General Escobedo**, luego el resto de ZMM por `rank` del GeoJSON del proyecto).
2. Pulsa **Start trayecto**.
   - El script carga el polígono desde Pages (`data/colonias.geojson`).
   - **Preferido:** filtra vías de `data/roads_zmm.geojson` (prebaked OSM Escobedo) — suele armar el trayecto en pocos segundos, sin Overpass.
   - Si no hay calles prebaked en el polígono: intenta **OSM Overpass** (2–3 mirrors, timeout duro ~12 s/mirror, techo ~22 s). Nunca se queda infinito en “Consultando OSM…”.
   - Si Overpass también falla: **fallback** rejilla ~50 m + puntos en el borde del polígono + botón **Reintentar**.
   - Arma una secuencia de puntos ~20 m (cobertura greedy por centerlines) y te lleva por Street View.
3. Mientras camina el trayecto:
   - Marca con **M / S / Y / E / P / I / H / C** como siempre.
   - **Space** = pausar / reanudar el trayecto.
   - **Pausa** / **Stop** en el HUD.
   - Ajusta la **velocidad** (slider 0.6–4.0 s).
4. Si un punto no tiene Street View (timeout ~5.5 s sin entrar a modo pano), se **salta** y sigue.
5. Al terminar: badge “Completo” + toasts; puedes elegir otra colonia.

Datos de colonias: `https://casca-code.github.io/mapa-purificadoras/data/colonias.geojson` (fallback raw GitHub).

Calles prebaked: `https://casca-code.github.io/mapa-purificadoras/data/roads_zmm.geojson` — regenerar con `python3 scripts/prebake_roads_zmm.py`.

Búsqueda de colonia: fuzzy (sin acentos) + aliases (`topo`, `pedregal`, `san francisco` → Villas / Pedregal del Topo Chico, etc.).

## Hotkeys (igual que Scout SV)

| Tecla | Qué marca | `kind` | `layer` |
|---|---|---|---|
| **M** | Modelorama *(primario)* | `modelorama` | `ancla_campo` |
| **S** | Semáforo *(primario)* | `otro` (nota `Semáforo`) | `ancla_campo` |
| **Y** | Competencia / purificadora | `purificadora` | `competencia` |
| **E** | Express | `express` | `ancla_campo` |
| **P** | Iglesia | `iglesia` | `ancla_campo` |
| **I** | Escuela | `escuela` | `ancla_campo` |
| **H** | Hospital / otro | `otro` | `ancla_campo` |
| **U** | Alias Modelorama | `modelorama` | `ancla_campo` |
| **C** | Comentario de zona (línea ~60 m) | `comentario_zona` | `comentario_zona` |
| **Space** | Sin trayecto: Auto-walk ON/OFF. Con trayecto activo: pausa/reanuda | — | — |
| **Z** / **Backspace** | Deshacer último pin de la sesión | — | — |

Botones en el HUD: **Start trayecto** · **Pausa** · **Stop** · **Export** · **Sync ntfy**.

## Auto-walk (sin trayecto)

Si ya estás en Street View y solo quieres avanzar por los links del panorama (sin colonia):

1. Entra a SV (peoncito).
2. **Space** → Auto-walk ON.
3. El script intenta, en orden:
   1. **ArrowUp** en canvas / document (con `keyCode` 38).
   2. Click en controles “Forward / Adelante / Siguiente” y hotspot del canvas.
   3. Reintento ArrowUp.
4. Detecta avance por **cambio de lat/lng en la URL**; si falla N veces seguidas → para (callejón sin salida).
5. Slider de velocidad; **no** dispara teclas mientras el diálogo **C** (comentario) está abierto ni cuando escribes en el buscador de colonia.

El método que avanzó se muestra en el badge (`SV · auto ▶ · ArrowUp` / `btn:…` / `canvas-hotspot`). En la práctica **ArrowUp con foco en el canvas** + detección por URL es el más estable; el click de UI es respaldo.

## Cómo se navega el trayecto (cero API key)

**No** se llama a Street View Static API ni a Maps JavaScript API. Solo URLs de Maps consumidor en tu sesión del navegador.

1. **Preferido** — path de Street View (igual que al soltar el peoncito):

```
https://www.google.com/maps/@LAT,LNG,3a,75y,HEADINGh,90t
```

2. **Respaldo** — Maps URLs `map_action=pano` (el `api=1` de esa URL es el esquema público de Google, **no** una API key de Cloud):

```
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG&heading=H&pitch=0&fov=75
```

3. Si ya estás en SV y el siguiente punto está cerca → **ArrowUp / click Adelante** sin recargar.

El trayecto se **guarda** (`sessionStorage` + `GM_setValue`) antes de cada `location.assign`, porque el reload mataría el estado. Al volver a cargar, el script **reanuda** solo.

Si tras 2 intentos **no entra a Street View**: el HUD pausa y dice en español que arrastres el **peoncito** en `google.com/maps` (nunca `scout-sv.html`). Progreso: `punto i/n · colonia`.

## Cómo llegan los pines al mapa principal

1. Al soltar pin / guardar comentario el script hace **`silentSync({ action: 'upsert', feature })`** al topic **`purif-zmm-campo-casca-v1`** (mismo que `index.html` / `scout-sv.html` / merge). Usa `GM_xmlhttpRequest` para saltar el CSP de Maps.
2. Workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → GitHub Pages. Ver `docs/FIELD_ADDS.md`.
3. Al abrir el mapa (`index.html`) se ve la capa compartida + merge de anclas/field adds (rutina existente).
4. **Export JSON** es respaldo (mismas keys `purificadoras_field_adds_v1` / `purificadoras_anclas_v1` en el payload). Útil si ntfy falló o quieres importar a mano.

### Por qué no basta localStorage

El userscript corre en el origen `https://www.google.com`. El mapa vive en `https://casca-code.github.io`. Los orígenes **no comparten** `localStorage`. Por eso el sync **debe** ser ntfy (o el export). El script igual escribe esas keys en el LS de Google como backup local de sesión, pero el mapa Pages **no** las lee de ahí.

`fuente` de cada feature: `scout_userscript`.

## Mini-mapa overlay

Google Maps impone CSP estricto (bloquea Leaflet/CDN y a menudo iframes externos). El overlay es un **canvas propio** (peg + pines de la sesión + trazo rosa del trayecto) + enlace **Abrir mapa** a Pages centrado cerca de la pose actual. Sin tiles Carto embebidos — a propósito, para que funcione sin pelear CSP.

## Permisos `@connect`

- `ntfy.sh` — sync pines
- `casca-code.github.io` / `raw.githubusercontent.com` — colonias + `roads_zmm.geojson`
- `overpass-api.de` / `overpass.kumi.systems` / `overpass.openstreetmap.ru` — Overpass opcional (refresh)
- `router.project-osrm.org` — reservado (puente corto opcional; no obligatorio)

## Limitaciones

- Hay que estar en **Street View** para marcar pines (el trayecto te mete solo).
- Lat/lng/heading se leen de la URL (`/@lat,lng,3a,…`, `map_action=pano`, `!3d`/`!4d`) + poll de `history`.
- Cobertura vial: prebaked Escobedo primero; fuera de Escobedo o si el prebake no cubre → Overpass o rejilla.
- Colonias con pocas vías OSM salen cortas (o usan rejilla).
- Colonias muy grandes se **muestrean** (máx. ~900 puntos) para no eternizar el recorrido.
- Auto-walk local no es el grafo de panoramas de la API de Maps; el **trayecto por colonia** es el camino fiable para cobertura.
- No implementa métricas / panel de control (diferido a propósito).
- Topic ntfy es el público del repo (ver nota de rotación en `FIELD_ADDS.md`). No se committean secrets nuevos.

## v1.2 — Overpass hang fix (Step 1)

Problema: al elegir colonia (p. ej. Pedregal del Topo Chico, Villas de San Francisco) el HUD se quedaba en **“Consultando OSM Overpass…”** sin fin.

Cambios:
1. Timeout duro por mirror (~12 s) + techo total ~22 s + mensaje de error + **Reintentar**.
2. Query Overpass más chica (`[timeout:15][maxsize:…]`, sin `pedestrian`).
3. **Prebaked** `data/roads_zmm.geojson` (Escobedo) servido desde Pages/raw — camino feliz sin Overpass.
4. Fallback densificar borde del polígono + rejilla ~50 m.
5. Búsqueda fuzzy de colonias.

## v1.2.1 — falso “API key” + trayecto que no camina

**Qué reportó Nicolás:** el userscript “dice que no tiene API key” y por eso el trayecto no camina bien.

**Causa real (no faltaba key):**
1. El toast de boot decía `sin API key` (mensaje positivo mal leído como error).
2. Cada waypoint hacía `location.assign` → reload → se perdía `state.route` → el trayecto moría al primer punto.
3. Posible confusión con `scout-sv.html` (esa página **sí** muestra gate de API key).

**Fix:** persistir/reanudar trayecto; URL `/@…,3a,…`; HUD fijo “Sin API key · usa google.com/maps (NO scout-sv)”; si falla el walk, instrucciones del peoncito en español (sin culpar a una key).

## Relacionado

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Scout con Maps JS (billing): `docs/SCOUT_SV.md` · `scout-sv.html`
- Script: `userscripts/purificadoras-scout.user.js`
