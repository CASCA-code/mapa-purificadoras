# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21 (v1.3.0)

> **Camino primario para Nicolás.** Corre **sobre** Google Maps de consumidor (`https://www.google.com/maps` Street View).  
> **Cero** Google Cloud / Maps Platform API key / hold de facturación.  
> **Usa siempre `google.com/maps` + peoncito.** No abras `scout-sv.html` (esa página sí pide key/billing).  
> Mapillary: abandonado.

## Qué es

Extensión de usuarios (Tampermonkey) que, mientras ves **Street View** en el Maps normal del navegador, te deja soltar los mismos pines / comentarios de zona que el mapa de campo, con las mismas teclas que Scout SV.

- Human-in-the-loop: tú miras el panorama y decides qué marcar.
- No scrapea negocios ni cachea imagery de Street View — solo GeoJSON (coords + props).
- Sync **primario: ntfy** (el userscript en `google.com` **no** puede compartir `localStorage` con `casca-code.github.io`).
- **v1.1:** picker de colonia + **trayecto** de cobertura vial (OSM) + auto-walk.
- **v1.2:** calles **prebaked** (`data/roads_zmm.geojson`) para Escobedo; Overpass con timeout duro + mirrors + **Reintentar**; fallback rejilla; búsqueda fuzzy.
- **v1.2.1:** trayecto **persiste** tras cada salto de URL; HUD aclara que no hace falta API key.
- **v1.3.0:** el peoncito automático **sí camina** — walk = **saltos URL Street View** (`map_action=pano&viewpoint=`), **no** tecla simulada. ArrowUp / MouseEvent sintéticos son *untrusted* y Maps los ignora; el soft `/@lat,lng,3a,…` a menudo **no** entra a SV sin panoid.

## Instalación (Chrome / Edge / Firefox)

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)** (u otro gestor compatible con Greasemonkey).
2. En Tampermonkey → **Utilidades** → **Instalar desde URL**, pega:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js
   ```

   Alternativa: abre esa URL → Tampermonkey ofrece **Instalar**.
3. Confirma permisos (`ntfy.sh`, Maps, `casca-code.github.io`, Overpass, raw GitHub).
4. Abre **[Google Maps](https://www.google.com/maps)** (no `scout-sv.html`) → arrastra el **peoncito** naranja a una calle de la ZMM (Street View).
5. Debe aparecer el **HUD** (arriba-izquierda) con **v1.3.0 · método URL-pano** y el **mini-peg** (abajo-izquierda).
6. Si el HUD no aparece o el auto/trayecto no salta: Tampermonkey → actualizar script a **v1.3.0+** desde la URL raw de arriba.

Actualizar: Tampermonkey suele detectar la nueva versión en el raw de GitHub; o reabre la URL e “Actualizar”.

## Flujo recomendado (colonia → trayecto → pines)

1. En el HUD, **busca / elige una colonia** (lista prioriza **General Escobedo**, luego el resto de ZMM por `rank` del GeoJSON del proyecto). Ejemplo: *Pedregal del Topo Chico*.
2. Pulsa **Start trayecto**.
   - El script carga el polígono desde Pages (`data/colonias.geojson`).
   - **Preferido:** filtra vías de `data/roads_zmm.geojson` (prebaked OSM Escobedo) — suele armar el trayecto en pocos segundos, sin Overpass.
   - Si no hay calles prebaked en el polígono: intenta **OSM Overpass** (opcional; timeout duro). Nunca se queda infinito en “Consultando OSM…”.
   - Si Overpass también falla: **fallback** rejilla ~50 m + puntos en el borde del polígono + botón **Reintentar**.
   - Arma una secuencia de puntos ~20 m y te lleva por Street View con **saltos URL-pano** cada ~2.8–3.5 s (Maps necesita tiempo de settle).
3. Mientras camina el trayecto:
   - Marca con **M / S / Y / E / P / I / H / C** como siempre.
   - **Space** = pausar / reanudar el trayecto (no dispara ArrowUp).
   - **▶ Siguiente** = avanza **un** waypoint a mano vía URL (sirve aunque el auto falle).
   - **Pausa** / **Stop** en el HUD.
   - Ajusta la **velocidad** (slider ~1.5–6.0 s; trayecto usa piso ~2.8 s).
4. Si un punto no tiene Street View, se **salta** y sigue. Solo pausa el trayecto entero tras **3 fallos SV completos seguidos** (entonces: arrastra el peoncito).
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

Botones en el HUD: **▶ Siguiente** · **Start trayecto** · **Pausa** · **Stop** · **Export** · **Sync ntfy**.

## Auto-walk (sin trayecto) — peoncito automático por URL

Si ya estás en Street View y solo quieres avanzar (sin colonia):

1. Entra a SV (peoncito).
2. **Space** → Auto-walk ON.
3. Cada tick el script:
   - Lee pose (lat/lng/heading) de la URL.
   - Calcula un punto **~12–18 m adelante** según el heading.
   - Hace `location.assign` al deep link consumidor:

```
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG&heading=H&pitch=0&fov=75
```

4. Tras el reload, el script relee la pose. Si `GM_setValue('purif_scout_autowalk', true)` está activo, **reanuda** auto-walk ~1.5 s después.
5. Si la pose **no cambia** tras un salto → gira heading **±45°** y reintenta; tras N fallos para con toast claro (sin hablar de API key).
6. Status / badge: método siempre **`URL-pano`**.

**No** depende de ArrowUp ni clicks sintéticos en el canvas (Maps los ignora por ser untrusted).

## Cómo se navega el trayecto (cero API key)

**No** se llama a Street View Static API ni a Maps JavaScript API. Solo URLs de Maps consumidor en tu sesión del navegador.

**Primario (v1.3+)** — Maps URLs `map_action=pano` + `viewpoint=` (el `api=1` es el esquema público de Google, **no** una API key de Cloud):

```
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG&heading=H&pitch=0&fov=75
```

El soft path `/@LAT,LNG,3a,75y,…` **ya no** es el primer intento: sin panoid a menudo no entra a Street View.

El trayecto se **guarda** (`sessionStorage` + `GM_setValue`) **antes** de cada `location.assign`, porque el reload mataría el estado. Al volver a cargar:

- Si ya estás cerca del waypoint actual → **incrementa índice** y programa el siguiente (no reasigna la misma URL en loop).
- Si ya se intentó ese índice y no hay avance → **skip** y sigue.
- Intervalo por defecto ~**2800–3500 ms**.

Progreso en HUD: `punto i/n · URL-pano · colonia`.

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

- Hay que estar en **Street View** (o haber saltado vía URL-pano) para marcar pines.
- Lat/lng/heading se leen de la URL (`map_action=pano`, `/@lat,lng,3a,…`, `!3d`/`!4d`) + poll de `history`.
- Cada salto URL **recarga** la página: el estado vive en `GM_setValue` / `sessionStorage`.
- Cobertura vial: prebaked Escobedo primero; fuera de Escobedo o si el prebake no cubre → Overpass o rejilla.
- Colonias con pocas vías OSM salen cortas (o usan rejilla).
- Colonias muy grandes se **muestrean** (máx. ~900 puntos) para no eternizar el recorrido.
- No implementa métricas / panel de control (diferido a propósito).
- Topic ntfy es el público del repo (ver nota de rotación en `FIELD_ADDS.md`). No se committean secrets nuevos.

## v1.3.0 — walk que sí se mueve (URL-pano)

**Problema:** auto-walk / trayecto no avanzaban. Root cause: `KeyboardEvent` / `MouseEvent` sintéticos son **untrusted** y Street View de Maps los ignora. Además `/@lat,lng,3a,…` sin panoid a menudo **no** abre SV.

**Fix:**
1. Walk primario = `location.assign` a `map_action=pano&viewpoint=LAT,LNG&heading=…`.
2. Auto-walk persiste flag `purif_scout_autowalk` + reanuda tras reload; si no hay avance, gira ±45°.
3. Trayecto: mismo URL-pano; intervalo más lento; skip de puntos muertos; pausa solo tras 3 fallos SV seguidos; **▶ Siguiente** manual.
4. HUD: método siempre `URL-pano`; sin mensajes que impliquen “falta API key”.

## v1.2 — Overpass hang fix

Problema: al elegir colonia el HUD se quedaba en **“Consultando OSM Overpass…”** sin fin.

Cambios: timeout duro + prebaked `roads_zmm.geojson` + fallback rejilla + fuzzy.

## v1.2.1 — falso “API key” + trayecto que no camina

Persistir/reanudar trayecto tras `location.assign`; HUD aclara que “sin API key” es correcto (Maps consumidor).

## Relacionado

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Scout con Maps JS (billing): `docs/SCOUT_SV.md` · `scout-sv.html`
- Script: `userscripts/purificadoras-scout.user.js`
