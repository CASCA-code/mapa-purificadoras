# Scout — Street View dinámico (Maps JavaScript API)

Actualizado: 2026-09-25

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
| **A** | Señal de alto | `alto` / `ancla_campo` → capa Altos / stops |
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

Tras **F**: pide nombre (default «Favorito») y teléfono opcional (8+ dígitos). Tras **Y**: pide precio de **recarga** MXN (campo primario `precio_recarga_mxn`) y opcionalmente garrafón/envase (`precio_garrafon_mxn`); vacío = omitir. El toast y el `name` reflejan el precio (ej. `Comp $12 recarga`). Versión Scout **v2.0.0** · checkbox **Nítido** (default on): espera `pano_changed` + dwell 600 ms y salta ~48 m para reducir blur del morph Street View; off = cobertura densa. Fin de ruta: toast/HUD **Colonia completa**.

## Sync ntfy → mapa principal

Mismo topic que campo / userscript: `purif-zmm-campo-casca-v1`.

Al soltar pin: upsert ntfy + `localStorage` (`purificadoras_field_adds_v1` / `purificadoras_anclas_v1` / `purificadoras_ours_v1`). Merge a `data/field_adds.geojson` vía workflow existente — ver [`FIELD_ADDS.md`](FIELD_ADDS.md).

## Trayecto OSM

- Fuente calles: `data/roads_zmm.geojson` (prebaked **Escobedo + Monterrey** vía `scripts/prebake_roads_zmm.py`; otras munis se pueden añadir con `--muni`).
- Fuente polígonos: `data/colonias.geojson` — match por `cve_col` (picker) / nombre + municipio.
- **Colonia seleccionada:** clip al polígono con buffer **~25 m** (calles del borde); AVENIDAS + residential/living_street/service; cadena greedy con **teleport** entre componentes. Muestreo ~22 m; tope ~4000 pts.
- **Pocas calles prebaked (<40 pts):** Scout pide Overpass en vivo para el bbox de la colonia y re-arma el trayecto (mismo clip).
- **Lat/lng sin colonia:** radio ~1.4 km; modo Avenidas o Todo; muestreo ~18 m; tope ~900 pts.
- Dry-run: `python3 scripts/dryrun_colonia_route.py --cve 19039_0167` (Croc).
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


## Ya existe (v2.0.0) — no re-scoutear

Al iniciar colonia, Scout carga **lazy** (una vez por sesión, luego filtra al bbox del trayecto **+300 m**):

| Fuente | Archivo | → kind Scout | Icono mini-mapa |
|---|---|---|---|
| Scout / campo previos | `data/field_adds.geojson` + LS local no mergeado | kind del pin (S→semaforo, A→alto, H→hospital) | **sólido** color kind |
| Places anclas | `data/places_anclas_zmm.geojson` | modelorama, express (oxxo/six/farmacia/banco: skip) | **hueco** |
| Places préstamos | `data/places_prestamos_zmm.geojson` | empeno (prestamo/financiera: skip) | hueco |
| Places purificadoras | `data/places_purificadoras_zmm.geojson` | purificadora (Y) | hueco |
| DENUE | `data/compet.geojson` | purificadora (Y) | hueco |
| OSM semáforos | `data/semaforos_zmm.geojson` | semaforo (solo `traffic_signals`) | hueco |
| OSM altos | `data/stops_zmm.geojson` | alto (solo `stop`) | hueco |
| OSM anclas | `data/anclas.geojson` | escuela, iglesia, hospital | hueco |

- HUD: chip **Ya existen: N Scout · M bot** y chip **Cerca: Modelorama (Places) 12 m · …** (≤ **40 m** del pano, top 4).
- **Pines Scout siempre válidos**: nunca se bloquea el envío; no hay guard Scout↔Scout (2 Modeloramas Scout juntos = 2 reales).
- **Dedupe solo Scout ↔ bot, mismo kind, ≤ 15 m**: el punto bot se absorbe (se oculta del mini-mapa; cuenta como 1, queda tu pin). Al soltar pin encima de uno bot: toast **«Ya estaba (Places) a X m — se cuenta como 1, queda tu pin»**. Sin Shift-force (no hace falta).
- Cada payload Scout lleva `source: "scout"` (además de `fuente: "scout_maps"`, `client: "scout.html"`). El merge (`scripts/merge_field_add_issues.py`) pasa props tal cual y rellena `source:"scout"` si falta y `fuente` empieza con `scout` (clientes viejos). Formato sin cambios.
- Huecos de datos: OSM `stops_zmm` ≈ 38 pts (casi solo Monterrey); semáforos OSM escasos en García (2); DENUE solo 93 purificadoras formales. Favorito / Hospital-otro sin fuente bot (solo Scout previos).

## Dedupe Scout ↔ Places/OSM (15 m) — mapa principal

`DEDUPE_M = 15` en `index.html` (antes 10; igual que Scout). Si un pin Scout (`field_adds`) y un feature Places/OSM del **mismo kind** están a ≤ ~15 m (haversine), se trata como **un solo lugar**: gana Scout (borde punteado, «Añadida con Scout»), se oculta el gemelo. Aplica a modelorama, express, iglesia, escuela, empeno, **alto** (OSM stops) y **purificadora** (Scout Y vs Places purificadoras). Scout↔Scout nunca se deduplica. Los contadores de los toggles (Modelorama, Express, Empeño, Altos / stops, Purificadoras Places) se recalculan sobre el set deduplicado. No toca DENUE (capa puntuada) ni `score_100` (precalculado). Semáforo Scout (kind `otro`) aún no entra al dedupe del mapa principal.

## ToS

Human-in-the-loop en el marcado. No scrapear nombres de negocio ni cachear imagery SV — solo GeoJSON (coords + props).
