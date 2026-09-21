# Scout SV (Street View remoto)

Actualizado: 2026-09-21 — **estado operativo**

> **Billing Google Cloud:** Nicolás rechazó el hold ~$500 MXN de Maps Platform.  
> **Mapillary:** pivot abortado (también rechazado). Hay un `scout.html` experimental Mapillary en el árbol de trabajo / opcional — **no es el camino primario** y no se promociona en Pages.  
> **Camino primario (sin billing):** userscript Tampermonkey sobre Street View de consumidor → [`docs/SCOUT_USERSCRIPT.md`](SCOUT_USERSCRIPT.md) · raw: `userscripts/purificadoras-scout.user.js`.

Polish v2 en Pages (`scout-sv.html`): colores normales, mini-mapa Leaflet, sync LS+ntfy al soltar pin, hotkeys primarios M/S, comentario de zona (LineString). Esa página **sigue requiriendo** API key de Maps JS (billing) — útil solo si algún día se habilita Cloud; **no pedir billing a Nicolás**. Preferir el userscript.

## Qué es (esta página)

Herramienta legacy/prototipo para recorrer colonias prioritarias de la ZMM con **Google Street View embebido** (Maps JavaScript API): Scout camina el grafo de panoramas; tú sueltas pines / comentarios con hotkeys.

No inventa scores. No métricas/control (diferido). No sustituye el flujo de campo en `index.html` (Ubicarme / Comp / ＋ / ★).

## API key (Google Maps) — solo si usas `scout-sv.html`

1. En [Google Cloud Console](https://console.cloud.google.com/) crea un proyecto (o usa uno de Purificadoras).
2. Habilita **Maps JavaScript API** (incluye Street View Panorama / Street View Service).
3. Crea una API key. Restringe por HTTP referrer a:
   - `https://casca-code.github.io/mapa-purificadoras/*`
   - `http://localhost/*` (si pruebas en local)
4. En Scout SV pega la key en el diálogo, o:
   - Query: `scout-sv.html?key=AIza…` (no compartas URLs con key)
   - `localStorage.purif_gmaps_key`
5. **No commits** de keys reales. El placeholder en código es `YOUR_API_KEY`.

**Sin billing:** no uses esta página; instala el userscript ([`SCOUT_USERSCRIPT.md`](SCOUT_USERSCRIPT.md)).

## ToS / uso permitido

- **Human-in-the-loop:** una persona mira el panorama y decide qué marcar. Scout solo mueve la cámara entre panoramas públicos de Street View.
- No scrapear ni automatizar lectura de nombres de negocio, OCR masivo, ni dumps de tiles.
- **No se cachea imagery de Street View** — solo se persisten pines / líneas GeoJSON (coords + props).
- Cumple las [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms) y políticas de Street View.

## Hotkeys

Configurables en `SCOUT_HOTKEYS` al inicio de `scout-sv.html` (mismas teclas en el userscript).  
**Primarios (arriba en leyenda):** **M** Modelorama · **S** Semáforo.

| Tecla | Qué marca | `kind` | `layer` |
|---|---|---|---|
| **M** | Modelorama *(primario)* | `modelorama` | `ancla_campo` |
| **S** | Semáforo *(primario)* | `otro` (nota `Semáforo`) | `ancla_campo` |
| **Y** | Competencia / purificadora | `purificadora` | `competencia` |
| **E** | Express | `express` | `ancla_campo` |
| **P** | Iglesia | `iglesia` | `ancla_campo` |
| **I** | Escuela | `escuela` | `ancla_campo` |
| **H** | Hospital / otro | `otro` | `ancla_campo` |
| **U** | Alias Modelorama (legacy) | `modelorama` | `ancla_campo` |
| **C** | Comentario de zona (línea) | `comentario_zona` | `comentario_zona` |
| **Space** | Pausar / reanudar caminata | — | — |
| **Backspace** / **Z** | Deshacer último pin/comentario (sesión + LS + ntfy delete) | — | — |

## Comentario de zona (LineString)

1. Hotkey **C** o botón **Comentar zona**.
2. Escribes el texto en el diálogo.
3. Scout guarda un **GeoJSON LineString** ~60 m centrado en el panorama, orientado al **heading** actual (±30 m).
4. Props típicas: `kind: "comentario_zona"`, `layer: "comentario_zona"`, `nota_raw` / `comentario`, `fuente: "scout_sv"`, `status: "inbox"`, `pano_id`, `heading`.
5. Se pinta en el **mini-mapa** (polyline rosa) y, tras sync/merge, en el **mapa principal** (`index.html` dibuja la línea + popup).

## Cómo llegan los pines al mapa principal

Misma pila que campo en `index.html` (no schema paralelo):

1. **Al soltar pin / guardar comentario**  
   - Append a `localStorage` (solo mismo origen Pages):
     - competencia → `purificadoras_field_adds_v1`
     - anclas + comentarios → `purificadoras_anclas_v1`
   - `silentSync({ action: 'upsert', feature })` al topic `purif-zmm-campo-casca-v1` (mismo que campo).

2. **Export JSON** (respaldo) — mismas keys en el payload.

3. **Sync ntfy** (botón) — re-envía upserts de la sesión.

4. Workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → Pages. Ver `docs/FIELD_ADDS.md`.

En el **userscript**, el sync primario es ntfy (LS de `google.com` no llega a Pages). Ver `SCOUT_USERSCRIPT.md`.

## Mini-mapa (abajo-izquierda)

- Leaflet + tiles **Carto Voyager** (igual que calles en `index.html`) — solo en `scout-sv.html`.
- Capas best-effort: `data/compet.geojson`, `anclas.geojson`, `field_adds.geojson`, `liked_zones.geojson` + pines de localStorage + sesión.
- Sigue el panorama (pegman rota con heading). Zoom cercano (~17).
- Solo coords/GeoJSON; **no** cachea tiles de Street View.

## Recorrido

- Centro: dropdown de colonias prioritarias o paste `lat,lng`.
- `StreetViewService.getPanorama` (±120 m, outdoor) → `StreetViewPanorama`.
- Auto-walk medio-rápido (slider; default ~6): link más alineado al POV; evita `pano` visitados; Space pausa.
- Contador de pasos; tope suave ~400.

## Colores / dark mode

Scout fuerza `color-scheme: only light` en página y `#pano` para que Chrome **no invierta** Street View ni el mini-mapa. UI en tema claro fijo.

## Diferido

- Métricas / panel de control: **no** en esta versión.
- Routing OSRM / grafo vial completo: no; solo grafo Street View.

## Relacionado

- **Userscript (recomendado):** [`docs/SCOUT_USERSCRIPT.md`](SCOUT_USERSCRIPT.md)
- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Ruta de colonia: `docs/RUTA_CAMPO.md`
