# Scout Userscript (Tampermonkey) — Street View sin billing

Actualizado: 2026-09-21

> **Camino primario para Nicolás.** Corre **sobre** Google Maps de consumidor (`google.com/maps` Street View).  
> **No** requiere Google Cloud / Maps Platform API key / hold de facturación.  
> Mapillary: abandonado. `scout-sv.html` (Maps JS embebido) queda solo si algún día hay billing.

## Qué es

Extensión de usuarios (Tampermonkey) que, mientras ves **Street View** en el Maps normal del navegador, te deja soltar los mismos pines / comentarios de zona que el mapa de campo, con las mismas teclas que Scout SV.

- Human-in-the-loop: tú miras el panorama y decides qué marcar.
- No scrapea negocios ni cachea imagery de Street View — solo GeoJSON (coords + props).
- Sync **primario: ntfy** (el userscript en `google.com` **no** puede compartir `localStorage` con `casca-code.github.io`).

## Instalación (Chrome / Edge / Firefox)

1. Instala **[Tampermonkey](https://www.tampermonkey.net/)** (u otro gestor compatible con Greasemonkey).
2. En Tampermonkey → **Utilidades** → **Instalar desde URL**, pega:

   ```
   https://raw.githubusercontent.com/CASCA-code/mapa-purificadoras/main/userscripts/purificadoras-scout.user.js
   ```

   Alternativa: abre esa URL → Tampermonkey ofrece **Instalar**.
3. Confirma permisos (`ntfy.sh`, Maps).
4. Abre [Google Maps](https://www.google.com/maps) → arrastra el **peoncito** a una calle de la ZMM (Street View).
5. Debe aparecer el **HUD** (arriba-izquierda) y el **mini-peg** (abajo-izquierda).

Actualizar: Tampermonkey suele detectar la nueva versión en el raw de GitHub; o reabre la URL e “Actualizar”.

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
| **Space** | Auto-walk ON/OFF (simula flecha adelante) | — | — |
| **Z** / **Backspace** | Deshacer último pin de la sesión | — | — |

Botones en el HUD: **Export** (JSON de respaldo) · **Sync ntfy** (reenvía upserts de la sesión).

## Cómo llegan los pines al mapa principal

1. Al soltar pin / guardar comentario el script hace **`silentSync({ action: 'upsert', feature })`** al topic **`purif-zmm-campo-casca-v1`** (mismo que `index.html` / `scout-sv.html` / merge). Usa `GM_xmlhttpRequest` para saltar el CSP de Maps.
2. Workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → GitHub Pages. Ver `docs/FIELD_ADDS.md`.
3. Al abrir el mapa (`index.html`) se ve la capa compartida + merge de anclas/field adds (rutina existente).
4. **Export JSON** es respaldo (mismas keys `purificadoras_field_adds_v1` / `purificadoras_anclas_v1` en el payload). Útil si ntfy falló o quieres importar a mano.

### Por qué no basta localStorage

El userscript corre en el origen `https://www.google.com`. El mapa vive en `https://casca-code.github.io`. Los orígenes **no comparten** `localStorage`. Por eso el sync **debe** ser ntfy (o el export). El script igual escribe esas keys en el LS de Google como backup local de sesión, pero el mapa Pages **no** las lee de ahí.

`fuente` de cada feature: `scout_userscript`.

## Mini-mapa overlay

Google Maps impone CSP estricto (bloquea Leaflet/CDN y a menudo iframes externos). El overlay es un **canvas propio** (peg + pines de la sesión) + enlace **Abrir mapa** a Pages centrado cerca de la pose actual. Sin tiles Carto embebidos — a propósito, para que funcione sin pelear CSP.

## Limitaciones

- Hay que estar en **Street View** (no solo el mapa 2D). El HUD avisa si aún no.
- Lat/lng/heading se leen de la URL (`/@lat,lng,3a,…,Hh,Tt` y/o `!3d`/`!4d`) + poll de `history`. Si Google cambia el formato de URL, puede hacer falta un ajuste.
- **Auto-walk** simula `ArrowUp` / click best-effort en la UI de SV; no es tan fiable como el grafo de links del Scout con API. Úsalo como ayuda, no como robot.
- No implementa métricas / panel de control (diferido a propósito).
- Topic ntfy es el público del repo (ver nota de rotación en `FIELD_ADDS.md`). No se committean secrets nuevos.

## Relacionado

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Scout con Maps JS (billing): `docs/SCOUT_SV.md` · `scout-sv.html`
- Script: `userscripts/purificadoras-scout.user.js`
