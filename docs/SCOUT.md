# Scout — Street View dinámico (Maps JavaScript API)

Actualizado: 2026-09-22

**Live:** https://casca-code.github.io/mapa-purificadoras/scout.html

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

## Cómo usar

1. Abre https://casca-code.github.io/mapa-purificadoras/scout.html
2. Elige colonia prioritaria (Escobedo) o pega `lat,lng` (default: última posición o San Miguel Residencial).
3. Cobertura: **Avenidas** (default) o **Todo**.
4. **Iniciar Scout** → arma trayecto desde `data/roads_zmm.geojson` y camina Dynamic Street View.
5. Hotkeys para pines; **Space** pausa/reanuda.

## Hotkeys

| Tecla | Qué | `kind` / `layer` |
|---|---|---|
| **M** | Modelorama | `modelorama` / `ancla_campo` |
| **S** | Semáforo | `otro` + nota Semáforo / `ancla_campo` |
| **F** | Favorito | `favorito` / `favoritos` |
| **Y** | Competencia | `purificadora` / `competencia` |
| **E** | Express | `express` / `ancla_campo` |
| **P** | Iglesia | `iglesia` / `ancla_campo` |
| **I** | Escuela | `escuela` / `ancla_campo` |
| **H** | Hospital / otro | `otro` / `ancla_campo` |
| **U** | Alias Modelorama | igual que M |
| **C** | Comentario de zona (~60 m LineString) | `comentario_zona` |
| **Space** | Pausar / reanudar | — |
| **Z** / **⌫** | Deshacer último pin | — |

## Sync ntfy → mapa principal

Mismo topic que campo / userscript: `purif-zmm-campo-casca-v1`.

Al soltar pin: upsert ntfy + `localStorage` (`purificadoras_field_adds_v1` / `purificadoras_anclas_v1` / `purificadoras_ours_v1`). Merge a `data/field_adds.geojson` vía workflow existente — ver [`FIELD_ADDS.md`](FIELD_ADDS.md).

## Trayecto OSM

- Fuente: `data/roads_zmm.geojson` (prebaked Escobedo/ZMM).
- **Avenidas:** `primary`, `secondary`, `tertiary`, `unclassified`, `trunk`.
- **Todo:** + `residential`, `living_street`, `service`.
- Radio ~900 m alrededor del centro; muestreo ~18 m; tope ~900 pts.
- Mini-mapa = `google.maps.Map` ligado al panorama (ruta + pines + pegman).

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
