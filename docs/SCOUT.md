# Scout — Street View dinámico (Maps JavaScript API)

Actualizado: 2026-09-24

**Live:** https://casca-code.github.io/mapa-purificadoras/scout.html  
Cache-bust tip: añade `?v=<commit-sha>` tras un deploy.

Herramienta oficial para recorrer Escobedo / ZMM con **Google Maps JavaScript API** + **StreetViewPanorama** (Dynamic Street View). **No** usa Places API ni Street View Static API.

## Cero setup de key

La key de Maps JS está en [`config/maps-key.js`](../config/maps-key.js) (`window.PURIF_MAPS_KEY`). Abrir la URL y listo.

### Restricción obligatoria (Google Cloud Console)

En el proyecto (p. ej. `807995860142`), restringe la key:

- **Application restrictions → HTTP referrers**
  - `https://casca-code.github.io/*`
  - `http://localhost/*` (opcional, pruebas locales)
  - `http://127.0.0.1/*` (opcional)
- **API restrictions:** Maps JavaScript API (Dynamic Street View vía panorama embebido).
- **No hace falta** Places ni Street View Static para Scout.

La key es visible en el cliente (Pages); la protección real es el referrer lock.

Override avanzado (raro): `localStorage.purif_gmaps_key` o botón **Key…** en el topbar — no es el flujo normal.

## Pantalla al cargar

Al abrir Scout, el panorama Street View se muestra **de inmediato** (centro Escobedo / última posición) vía `StreetViewService.getPanorama` outdoor. Si no hay imagery, cae a mapa de respaldo con mensaje en español — nunca un void negro. Errores de key/billing/referrer aparecen en HUD (`gm_authFailure`).

Si ves error de autenticación: confirma en Cloud Console referrers `https://casca-code.github.io/*` (+ localhost) y Maps JavaScript API + billing en el proyecto de la key.

## Cómo usar

1. Abre https://casca-code.github.io/mapa-purificadoras/scout.html
2. Elige colonia prioritaria (Escobedo) o pega `lat,lng` (default: última posición o San Miguel Residencial).
3. **Colonia** → cobertura completa del polígono (`data/colonias.geojson`): todas las calles (residential + avenidas). UI pasa a **Todo**. Lat/lng suelto: **Avenidas** o **Todo** ± ~1.4 km.
4. **Iniciar Scout** → arma trayecto desde `data/roads_zmm.geojson` (clip al polígono si hay colonia) y camina Dynamic Street View.
5. Hotkeys para pines; **Space** pausa/reanuda. Cada pin/comentario/undo se sync a ntfy automáticamente.

## Hotkeys

| Tecla | Qué | `kind` / `layer` |
|---|---|---|
| **M** | Modelorama | `modelorama` / `ancla_campo` |
| **S** | Semáforo | `otro` + nota Semáforo / `ancla_campo` |
| **F** | Favorito (prompt nombre + tel opcional) | `favorito` / `favoritos` + `favorito:true` |
| **Y** | Competencia (prompt precio recarga / garrafón) | `purificadora` / `competencia` + `precio_*_mxn` |
| **E** | Express | `express` / `ancla_campo` |
| **P** | Iglesia | `iglesia` / `ancla_campo` |
| **I** | Escuela | `escuela` / `ancla_campo` |
| **H** | Hospital / otro | `otro` / `ancla_campo` |
| **N** | Empeño / Monte | `empeno` / `ancla_campo` → capa Casas de empeño |
| **U** | Alias Modelorama | igual que M |
| **C** | Comentario de zona (~60 m LineString) | `comentario_zona` |
| **Space** | Pausar / reanudar | — |
| **Z** / **⌫** | Deshacer último pin | — |

Tras **F**: pide nombre (default «Favorito») y teléfono opcional (8+ dígitos). Tras **Y**: pide precio de **recarga** MXN (campo primario `precio_recarga_mxn`) y opcionalmente garrafón/envase (`precio_garrafon_mxn`); vacío = omitir. El toast y el `name` reflejan el precio (ej. `Comp $12 recarga`). Versión Scout **v1.9.6** · checkbox **Nítido** (default on): espera `pano_changed` + dwell 600 ms y salta ~48 m para reducir blur del morph Street View; off = cobertura densa. Fin de ruta: toast/HUD **Colonia completa**.

## Sync ntfy → mapa principal

Mismo topic que campo / userscript: `purif-zmm-campo-casca-v1`.

Al soltar pin: upsert ntfy + `localStorage` (`purificadoras_field_adds_v1` / `purificadoras_anclas_v1` / `purificadoras_ours_v1`). Merge a `data/field_adds.geojson` vía workflow existente — ver [`FIELD_ADDS.md`](FIELD_ADDS.md).

## Trayecto OSM

- Fuente calles: `data/roads_zmm.geojson` (prebaked Escobedo/ZMM).
- Fuente polígonos: `data/colonias.geojson` — match por nombre (acentos/espacios) + municipio.
- **Colonia seleccionada:** clip de segmentos al polígono (punto dentro o arista que cruza); fuerza AVENIDAS + residential/living_street/service; cadena greedy con **teleport** entre componentes (no abandona manzanas sueltas). Muestreo ~22 m; tope ~4000 pts (si hace falta, sube el paso antes de stride).
- **Lat/lng sin colonia:** radio ~1.4 km; modo Avenidas o Todo; muestreo ~18 m; tope ~900 pts.
- Mini-mapa: ruta + outline del polígono + pines + pegman.

## Sync → mapa principal

- Cada hotkey / comentario / undo llama `silentSync` (fetch a ntfy `purif-zmm-campo-casca-v1`) al instante; toast **Enviado al mapa** / **Error sync**.
- El mapa público lee `data/field_adds.geojson` tras el merge Action (plantilla `docs/merge-field-adds.workflow.yml` → `.github/workflows/`): cron **cada ~2 h** si está instalado (`15 */2`), más `workflow_dispatch` / `repository_dispatch` (`merge-field-adds`).
- **Latencia:** LS local inmediato. ntfy inmediato (toast Enviado al mapa). Mapa público: hasta ~2 h **después de instalar** el merge workflow; hoy hay que mergear a mano (`scripts/merge_field_add_issues.py`) o copiar la plantilla a `.github/workflows/`.
- Cache-bust: `scout.html?v=<commit>` tras deploy Pages.

## Qué aún necesita Places / Static (no habilitado)

| Necesidad | API | Estado |
|---|---|---|
| Autocomplete de negocios / Place Details | Places | **No** — no llamar |
| Imágenes SV por URL `streetview` static | Street View Static | **No** — usamos panorama dinámico |
| Map + Street View embebido | Maps JavaScript | **Sí — esto es Scout** |

## Fallback sin Maps Platform

Userscript Tampermonkey + extensión Chrome sobre `google.com/maps`: [`SCOUT_USERSCRIPT.md`](SCOUT_USERSCRIPT.md).

## Legacy

- `scout-sv.html` redirige a `scout.html`.
- Notas antiguas: [`SCOUT_SV.md`](SCOUT_SV.md).

## ToS

Human-in-the-loop en el marcado. No scrapear nombres de negocio ni cachear imagery SV — solo GeoJSON (coords + props).
