# Scout SV (Street View remoto)

Actualizado: 2026-09-21 — prototipo v1 en `scout-sv.html`.

**Abrir:** https://casca-code.github.io/mapa-purificadoras/scout-sv.html  

Cache-bust: añade `?v=<sha7>` (o cualquier query) si el navegador sirve HTML viejo, p. ej.  
`https://casca-code.github.io/mapa-purificadoras/scout-sv.html?v=SHA7`.

## Qué es

Herramienta para que **Nicolás** recorra colonias prioritarias de la ZMM desde la laptop/tablet con **Google Street View**: el Scout camina solo el grafo de panoramas (links forward) a velocidad media-rápida; tú sueltas pines con hotkeys en el lat/lng del panorama actual.

No inventa scores. No sustituye el flujo de campo en `index.html` (Ubicarme / Comp / ＋ / ★).

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
- Cumple las [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms) y políticas de Street View. Uso operativo interno de site selection; no redistribuir imagery.

## Hotkeys (sesión)

Configurables en el objeto `SCOUT_HOTKEYS` al inicio de `scout-sv.html`.

| Tecla | Qué marca | `kind` | `layer` |
|---|---|---|---|
| **Y** | Competencia / purificadora | `purificadora` | `competencia` |
| **U** | Modelorama | `modelorama` | `ancla_campo` |
| **O** | Express | `express` | `ancla_campo` |
| **P** | Iglesia | `iglesia` | `ancla_campo` |
| **I** | Escuela | `escuela` | `ancla_campo` |
| **S** | Semáforo | `otro` (name/nota `Semáforo`) | `ancla_campo` |
| **H** | Hospital / otro | `otro` | `ancla_campo` |
| **Space** | Pausar / reanudar caminata | — | — |
| **Backspace** / **Z** | Deshacer último pin (sesión) | — | — |

## Cómo llegan los pines al mapa principal

1. **Export JSON (v1 recomendado)**  
   Botón **Exportar JSON** → archivo + portapapeles con la misma forma de keys que el export de campo:
   ```json
   {
     "exported_at": "…",
     "fuente": "scout_sv",
     "keys": {
       "purificadoras_field_adds_v1": [ /* Features competencia */ ],
       "purificadoras_anclas_v1": [ /* Features ancla_campo */ ]
     }
   }
   ```
   Cada Feature es GeoJSON Point con `properties` alineadas a campo (`id`, `kind`, `name`, `nota_raw`, `ts`, `fuente: "scout_sv"`, `status: "inbox"`, `layer`, …).

2. **Sync ntfy (opcional)**  
   Botón **Sync ntfy** hace `upsert` al mismo topic que `index.html` (`purif-zmm-campo-casca-v1`). El workflow / `scripts/merge_field_add_issues.py` mergea a `data/field_adds.geojson` → Pages. Ver `docs/FIELD_ADDS.md`.

3. Tras merge + push, abre el mapa principal (cache-bust `?v=`) y verás los pines en capas competencia / anclas campo.

## Recorrido (v1)

- Centro: dropdown de colonias prioritarias (centroides de `data/colonias.geojson`) o paste `lat,lng`.
- `StreetViewService.getPanorama` (±120 m, outdoor) → `StreetViewPanorama`.
- Auto-walk: elige el link cuyo heading está más alineado al POV actual; evita `pano` ya visitados; slider de velocidad + Space.
- Contador de pasos; tope suave ~400 (pausar y seguir o nuevo centro).

## Límites / siguiente

- No hay routing de red vial completa (OSRM etc.): solo grafo Street View.
- Colonia picker = lista corta hardcodeada (ampliar leyendo geojson si hace falta).
- ntfy es best-effort (CORS/beacon); export-first sigue siendo el path fiable.
- Pegman del mini-mapa no rota con heading (v1).

## Relacionado

- Mapa campo: `index.html` · sync: `docs/FIELD_ADDS.md`
- Ruta de colonia: `docs/RUTA_CAMPO.md`
