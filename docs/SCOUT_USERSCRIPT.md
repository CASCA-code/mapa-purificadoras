# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21 (v1.4.0)

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
- **v1.3.0:** walk vía saltos URL (`map_action=pano&viewpoint=`) — **sí caminaba**, pero cada paso hacía **pantalla negra**.
- **v1.4.0:** walk = **flecha SV** (paso suave *in-panorama*). Space / auto-walk / trayecto **ya no** hacen `location.assign` cada tick. URL-pano solo para **entrar** a la colonia (1×) o recovery raro.

## Instalación (Chrome / Edge / Firefox)

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)** (u otro gestor compatible).
2. En Tampermonkey → **Utilidades** → **Instalar desde URL**, pega:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js
   ```

   Alternativa: abre esa URL → Tampermonkey ofrece **Instalar**.
3. Confirma permisos (`ntfy.sh`, Maps, `casca-code.github.io`, Overpass, raw GitHub).
4. Abre **[Google Maps](https://www.google.com/maps)** (no `scout-sv.html`) → arrastra el **peoncito** naranja a una calle de la ZMM (Street View).
5. Debe aparecer el **HUD** (arriba-izquierda) con **v1.4.0 · flecha SV** y el **mini-peg** (abajo-izquierda).
6. Si el HUD no aparece o el auto no avanza: Tampermonkey → actualizar script a **v1.4.0+** desde la URL raw.

Actualizar: Tampermonkey suele detectar la nueva versión en el raw de GitHub; o reabre la URL e “Actualizar”.

## Flecha SV vs teletransporte URL

| | **flecha SV** (default) | **URL-pano** (teletransporte) |
|---|---|---|
| Qué hace | Intenta el mismo gesto que clickear la flechita blanca / chevron del camino; rotar con botones HTML si hace falta | `location.assign` a `map_action=pano&viewpoint=` |
| Pantalla negra | **No** — transición suave del panorama | **Sí** — flash negro / reload |
| Space / auto-walk | ✅ | ❌ desactivado en v1.4 |
| ▶ Siguiente | Un paso flecha | ❌ |
| Trayecto | Tras 1 entrada URL, camina con flecha hacia cada waypoint | Solo 1× al entrar colonia, o recovery cada ~8 fallos de flecha (con toast de aviso) |

### Por qué no hay “botón Forward” en el DOM

Investigación Maps SV 2025/2026: las chevrons blancas del asfalto se dibujan en **WebGL** (`canvas` de la escena). No hay un `<button aria-label="Forward">` estable. Sí hay botones HTML de **rotar** la vista. El userscript:

1. Busca overlays/DOM con labels tipo Forward / Adelante / navigate (por si Maps los expone).
2. Hace pointer-clicks en la zona típica del chevron (centro-bajo del canvas).
3. Enfoca el canvas y despacha `ArrowUp` (a menudo *untrusted* → ignorado).
4. Si está instalada la **extensión** companion, pide un `ArrowUp` **confiable** vía `chrome.debugger`.

## Extensión Chrome (fallback opcional)

Solo si Space / Siguiente **no avanzan** (Maps ignora eventos untrusted):

1. Chrome → `chrome://extensions` → **Modo de desarrollador** → **Cargar descomprimida**.
2. Elige la carpeta `extension/` de este repo.
3. Recarga la pestaña de Maps / Street View.
4. Al pedir flecha, Chrome puede mostrar un banner amarillo breve de “debugging” — es normal; se quita solo.

Detalle: [`extension/README.md`](../extension/README.md).

**Preferimos userscript solo.** La extensión es plan B documentado.

## Flujo recomendado (colonia → trayecto → pines)

1. En el HUD, **busca / elige una colonia** (lista prioriza **General Escobedo**, luego el resto de ZMM por `rank`). Ejemplo: *Pedregal del Topo Chico*.
2. Pulsa **Start trayecto**.
   - Carga el polígono desde Pages (`data/colonias.geojson`).
   - **Preferido:** filtra vías de `data/roads_zmm.geojson` (prebaked OSM Escobedo).
   - Si no hay calles prebaked: Overpass (timeout duro) → fallback rejilla ~50 m + **Reintentar**.
   - Arma puntos ~20 m. **Entra** al primer punto con **1 salto URL** (puede flash), luego camina con **flecha SV** (~0.8–1.5 s, slider).
3. Mientras camina:
   - Marca con **M / S / Y / E / P / I / H / C**.
   - **Space** = pausar / reanudar el trayecto.
   - **▶ Siguiente** = **un** paso flecha SV (no teletransporte).
   - **Pausa** / **Stop** en el HUD.
   - Ajusta la **velocidad** (slider ~0.8–2.5 s).
4. Si la flecha no avanza tras varios intentos, **skipea** el waypoint. Recovery URL solo cada N fallos (toast avisa el flash).
5. Al terminar: badge “Completo”; elige otra colonia.

Datos de colonias: `https://casca-code.github.io/mapa-purificadoras/data/colonias.geojson` (fallback raw GitHub).

Calles prebaked: `https://casca-code.github.io/mapa-purificadoras/data/roads_zmm.geojson` — regenerar con `python3 scripts/prebake_roads_zmm.py`.

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
| **Space** | Sin trayecto: Auto-walk flecha SV ON/OFF. Con trayecto: pausa/reanuda | — | — |
| **Z** / **Backspace** | Deshacer último pin de la sesión | — | — |

Botones HUD: **▶ Siguiente** · **Start trayecto** · **Pausa** · **Stop** · **Export** · **Sync ntfy**.

## Auto-walk (sin trayecto)

1. Entra a SV (peoncito).
2. **Space** → Auto-walk ON · **flecha SV**.
3. Cada tick (~1.1 s default): intenta un paso suave adelante **sin** recargar la página.
4. Si no hay avance: rota rumbo ±45° (botones HTML) y reintenta; tras N fallos para con toast. Recovery URL solo cada ~8 fallos (aviso de flash).
5. Badge / método: siempre **`flecha SV`** (o `flecha SV+ext` si la extensión respondió).

## Cómo llegan los pines al mapa principal

1. Al soltar pin / guardar comentario: **`silentSync({ action: 'upsert', feature })`** al topic **`purif-zmm-campo-casca-v1`** (mismo que `index.html`). Usa `GM_xmlhttpRequest` para saltar el CSP de Maps.
2. Workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → GitHub Pages. Ver `docs/FIELD_ADDS.md`.
3. **Export JSON** es respaldo.

### Por qué no basta localStorage

El userscript corre en `https://www.google.com`. El mapa vive en `https://casca-code.github.io`. Los orígenes **no comparten** `localStorage`. Sync = ntfy (o export).

`fuente` de cada feature: `scout_userscript`.

## Mini-mapa overlay

Canvas propio (peg + pines + trazo del trayecto) + enlace **Abrir mapa** a Pages. Sin tiles CDN (CSP de Maps).

## Permisos `@connect`

- `ntfy.sh` — sync pines
- `casca-code.github.io` / `raw.githubusercontent.com` — colonias + `roads_zmm.geojson`
- Overpass mirrors — refresh opcional
- `router.project-osrm.org` — reservado

## Limitaciones

- Hay que estar en **Street View** para marcar pines.
- Lat/lng/heading se leen de la URL + poll de `history`.
- Chevrons WebGL: click/pointer puede fallar en algunos builds → extensión.
- Entrada/recovery URL = flash negro (avisado).
- Colonias grandes se muestrean (máx. ~900 puntos).
- Topic ntfy público del repo (ver rotación en `FIELD_ADDS.md`). No se committean secrets nuevos.

## v1.4.0 — flecha SV (sin pantalla negra)

**Problema (Nicolás):** `map_action=pano` saltaba demasiado lejos → **pantalla negra** cada paso.

**Fix:**
1. Space / auto-walk / ▶ Siguiente = **flecha SV** (DOM chevron / pointer / ArrowUp / extensión).
2. Trayecto: **1 URL** para entrar a la colonia, luego flecha hacia waypoints (haversine); URL recovery raro.
3. HUD: método `flecha SV`.
4. Extensión opcional `extension/` documentada en español.
5. Docs: tabla flecha vs teletransporte.

## Relacionado

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Scout con Maps JS (billing): `docs/SCOUT_SV.md` · `scout-sv.html`
- Script: `userscripts/purificadoras-scout.user.js`
- Extensión: `extension/`
