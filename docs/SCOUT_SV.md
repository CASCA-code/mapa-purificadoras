# Scout SV (Street View remoto)

Actualizado: 2026-09-21 — **estado operativo**

> **Billing Google Cloud:** Nicolás rechazó el hold ~$500 MXN de Maps Platform.  
> **Mapillary:** pivot abortado (también rechazado). Hay un `scout.html` experimental Mapillary en el árbol de trabajo / opcional — **no es el camino primario** y no se promociona en Pages.  
> **Próximo (planned):** userscript Tampermonkey / extensión Chrome que corre **sobre** `google.com/maps` Street View (Maps de consumidor, **sin** Cloud billing / API key). Hotkeys → mismos `localStorage` + ntfy que campo; auto-forward opcional vía flechas UI de SV; mini-mapa overlay. Build aparte.

Polish v2 ya en Pages (`scout-sv.html`): colores normales, mini-mapa Leaflet, sync LS+ntfy al soltar pin, hotkeys primarios M/S, comentario de zona (LineString). Esa página **sigue requiriendo** API key de Maps JS (billing) — útil solo si algún día se habilita Cloud; no pedir billing a Nicolás.


## Qué es

Herramienta para que **Nicolás** recorra colonias prioritarias de la ZMM desde la laptop/tablet con **Google Street View**: el Scout camina solo el grafo de panoramas (links forward) a velocidad media-rápida; tú sueltas pines / comentarios con hotkeys en el lat/lng (y heading) del panorama actual.

No inventa scores. No métricas/control (diferido). No sustituye el flujo de campo en `index.html` (Ubicarme / Comp / ＋ / ★).

## API key (Google Maps)

1. En [Google Cloud Console](https://console.cloud.google.com/) crea un proyecto (o usa uno de Purificadoras).
2. Habilita **Maps JavaScript API** (incluye Street View Panorama / Street View Service).
3. Crea una API key. Restringe por HTTP referrer a:
   - `https://casca-code.github.io/mapa-purificadoras/*`
   - `http://localhost/*` (si pruebas en local)
4. En Scout SV pega la key en el diálogo, o:
   - Query: `scout-sv.html?key=AIza…` (no compartas URLs con key)
   - `localStorage.purif_gmaps_key`
5. **No commits** de keys reales. El placeholder en código es `YOUR_API_KEY`.

## ToS / uso permitido

- **Human-in-the-loop:** una persona mira el panorama y decide qué marcar. Scout solo mueve la cámara entre panoramas públicos de Street View.
- No scrapear ni automatizar lectura de nombres de negocio, OCR masivo, ni dumps de tiles.
- **No se cachea imagery de Street View** — solo se persisten pines / líneas GeoJSON (coords + props).
- Cumple las [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms) y políticas de Street View.

## Hotkeys

Configurables en `SCOUT_HOTKEYS` al inicio de `scout-sv.html`.  
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
   - Append a `localStorage`:
     - competencia → `purificadoras_field_adds_v1`
     - anclas + comentarios → `purificadoras_anclas_v1`
   - `silentSync({ action: 'upsert', feature })` al topic `purif-zmm-campo-casca-v1` (mismo que campo).

2. **Export JSON** (respaldo) — mismas keys en el payload.

3. **Sync ntfy** (botón) — re-envía upserts de la sesión.

4. Workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → Pages. Ver `docs/FIELD_ADDS.md`.

## Mini-mapa (abajo-izquierda)

- Leaflet + tiles **Carto Voyager** (igual que calles en `index.html`).
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

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Ruta de colonia: `docs/RUTA_CAMPO.md`
