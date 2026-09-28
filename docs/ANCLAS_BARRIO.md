# Anclas de barrio (ZMM) — tortillerías, abarrotes, paradas, farmacias, bancos de préstamo

Capas estáticas (el mapa **sólo lee archivos** en `data/`; nunca llama DENUE/Places/Overpass en vivo).
BBox = mismo clip que `data/places_anclas_zmm.geojson` (`[-100.6592, 25.5586, -100.0526, 25.8728]`).

## Pipeline

```bash
python3 scripts/fetch_denue_anclas_barrio_zmm.py    # DENUE bulk CSV NL (gratis, sin token) → data/denue_anclas_barrio_zmm.geojson (gitignored, 6 MB)
python3 scripts/fetch_osm_anclas_barrio_zmm.py      # Overpass (gratis) → data/osm_anclas_barrio_zmm.geojson
python3 scripts/fetch_places_anclas_barrio_zmm.py   # Places Text Search (cap 550 req) → data/places_anclas_barrio_zmm.geojson
python3 scripts/build_anclas_barrio_zmm.py          # merge + dedupe → data/anclas_*_zmm.geojson + data/anclas_barrio_manifest.json
```

- DENUE: sin token INEGI en repo/.env → se usa la descarga masiva `denue_19_csv.zip` (mismos datos que la API).
- Places: misma llave que `fetch_places_anclas_zmm.py` (env → `.env` → `config/maps-key.js`). `--dry-run`, `--only`, `--grid 12x10`, `--merge`.

## Capas (toggle propio en panel Anclas → «Anclas de barrio», default OFF, canvas en pane `ptsVec` sobre polígonos)

| Capa | Archivo | Fuentes (prioridad) | Dedupe |
|---|---|---|---|
| Tortillerías | `anclas_tortillerias_zmm.geojson` | DENUE 311830 > Places «tortillería» > OSM | 30 m |
| Abarrotes / depósitos | `anclas_abarrotes_zmm.geojson` | DENUE 461110 + 462112 (minisúper sin cadenas) + 461211/461212 (vinos-licores / cerveza) > OSM convenience/general/kiosk/supermarket chico/alcohol/beverages | 30 m |
| Paradas de camión / ruta | `anclas_paradas_zmm.geojson` | OSM bus_stop/platform > Places `bus_stop` | 20 m |
| Farmacias de barrio | `anclas_farmacias_barrio_zmm.geojson` (extras) + Places farmacia existente | Places (Guadalajara/Benavides) > DENUE 464111 > OSM pharmacy | 30 m |
| Bancos de préstamo (Bienestar/Azteca) | `anclas_bancos_prestamo_zmm.geojson` (extras) + Places Banco Azteca + OSM retail banco_* | Places/OSM existentes > Places Bienestar/Elektra > DENUE (522110/522210/466112/523122/522452 con nombre AZTECA/BIENESTAR/ELEKTRA) > OSM | 30 m |

- **Dedupe sólo entre fuentes distintas**: dos puntos DENUE a 20 m = dos tienditas reales, no se funden. Prop `s` lista fuentes que confirman el punto.
- Farmacias y Bancos: el archivo trae sólo los extras que no están a ≤30 m de lo ya pintado por Places/OSM retail; el toggle prende ambos (incl. pines Scout banco/bienestar/farmacia). Los toggles viejos «Banco Azteca», «Banco del Bienestar», «Farmacias» salieron del submenú de marcas.
- Otros bancos (BBVA, Banorte…) **no** son ancla. Oxxo sigue como ancla (positiva: vende agua más cara).
- Abarrotes (~3 MB) y demás se descargan sólo al prender su toggle; los contadores salen de `anclas_barrio_manifest.json`.

## Huecos conocidos

- Places Text Search devuelve ≤60 por celda: tortillerías/paradas Places incompletas en zonas densas (DENUE cubre tortillerías; paradas dependen de OSM+Places).
- OSM ZMM flojo en tiendas (212) y tortillerías (11).
- DENUE = foto 2025-26 (diccionario 20/05/2026); negocios cerrados/abiertos después no se reflejan.
