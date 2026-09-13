# Mapa Version 2 — purificadoras ZMM

Ranking compuesto de oportunidad (0–100) para colonias gated de la Zona Metropolitana de Monterrey.
**No reemplaza** el estudio / mapa anterior: el artefacto viejo sigue en

`../mapa_purificadoras_artifact.html`

## Fórmula

```
Score = 100 × (0.40·Demanda* + 0.25·(1 − Comp*) + 0.20·Anclas* + 0.15·(1 − Canibal*))
```

Todos los términos con `*` están min-max normalizados a 0–1 **sobre las mismas 167 colonias** del estudio v1 (grado Medio/Alto, pob ≥ 1500, ZMM8).

| Término | Definición |
|---|---|
| **Demanda\*** | `pob_eff = 0.5·served_pop_500m + 0.5·min(served_pop_500m, 5·POB_TOT)` · `demanda_raw = pob_eff · (0.85·OVHAC_norm + 0.15·OVSAE_norm)` |
| **Comp\*** | `minmax(comp_formal + comp_informal)`. Formal = DENUE (recarga 1.0, industrial 0.15, decay ~400 m). Informal = proxy a **1.0 por 1,000 viviendas** (columna v1 a 1.5/1000 escalada ×1.0/1.5). |
| **Anclas\*** | Suma `peso·exp(−d/250)` de anclas a ≤250 m del **centroide** (no polígono). Pesos: jardín 1.00; **Aurrera Express / Soriana Express 0.90**; iglesia / **Banco del Bienestar / Banco Azteca 0.85**; **Modelorama/Six/cerveza specialty 0.80**; hospital 0.70; universidad 0.55; primaria/secundaria 0.40; preparatoria 0.35; college 0.30; otra 0.20. Retail/bancos en `anclas_retail_bancos.geojson`. |
| **Canibal\*** | Suma `exp(−d/500)` desde el centroide a estaciones en `estaciones_propias.csv`. Si el CSV está vacío → Canibal\*=0 (el factor aporta el 0.15 completo). |

### Viabilidad (columnas aparte, **no** entran al Score)

- Precio recarga: **$12 MXN** / garrafón
- Break-even / OPEX estación: **$13 000 MXN/mes** (provisional — estimado de franquicia ~13k; documentado en `build_report_v2.json`)
- Resto: `hh_size=3.6`, `garrafones/viv/sem=2`, `capture_rate=3%`, `semanas/mes=4.33` (igual que v1)

## Cómo re-ejecutar

Desde PowerShell, en esta carpeta:

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\purificadora\version2"
python pipeline_v2.py
python build_map_v2.py
```

Salidas:

- `colonias_v2_scored.csv`
- `colonias_v2.geojson` (propiedades: `score_100`, componentes, `rank`)
- `build_report_v2.json` (params + top 20)
- `mapa_purificadoras_version2.html`

Entradas que **reutiliza** (no las modifica):

- `../colonias_zmm_scored.csv` — pob, OVHAC/OVSAE, served_pop, lat/lon
- `../colonias_zmm.geojson` — polígonos
- `../competidores_zmm.geojson` — DENUE formal
- `../anclas_contexto_zmm.geojson` — escuelas / iglesias / hospitales

## Cómo agregar estaciones propias (canibalización)

Edita `estaciones_propias.csv`:

```csv
id,nombre,lat,lon,status,fecha,notas
# ejemplo (quita el # y usa coordenadas reales):
# E001,Escobedo Centro,25.806,-100.320,planeada,2026-09,prueba
```

`status`: `planeada` | `abierta`.

Luego vuelve a correr `pipeline_v2.py` + `build_map_v2.py`. Las colonias cercanas bajarán de score (sube Canibal\*). En el mapa, la capa **Estaciones propias** aparece solo si hay filas.

## DENUE en vivo (más adelante)

Hoy se usa el snapshot `datos_fuente/denue_purif_nl.json` → `competidores_zmm.geojson`.
Para refrescar competencia formal:

1. Re-descargar DENUE SCIAN 312112 (NL) o actualizar `denue_purif_nl.json`
2. Re-correr el `datos_fuente/pipeline.py` del estudio v1 (escribe `competidores_zmm.geojson` en la raíz)
3. Re-correr este `pipeline_v2.py`

No hace falta rehacer CONAPO/IMC si solo cambia DENUE o estaciones propias.

## Diferencias vs el artefacto viejo

| | Artefacto v1 (`mapa_purificadoras_artifact.html`) | Version 2 |
|---|---|---|
| Score | `demanda / (1 + competencia)` con informal | Compuesto 0–100 con 4 factores normalizados |
| Demanda | served_pop × (0.70 OVHAC + 0.30 OVSAE) | `pob_eff` con tope 5×POB + (0.85 / 0.15) |
| Competencia | formal + informal (1.5/1000) | formal + informal (**1.0**/1000) en Comp* |
| Anclas | capa de contexto, **no** en el score | entran al score (20%); pesos: jardín>iglesia>hospital>uni>escuelas |
| Canibalización | no | CSV de estaciones propias |
| Precio / BE | $15 · $18k | $12 · $13k (provisional) |
| Archivo | raíz del proyecto | `version2/` (paralelo) |

## Nota

Este directorio es **paralelo** al estudio. No borra ni sobrescribe `mapa_purificadoras_artifact.html`, `pipeline.py` outputs, ni el informe Obsidian.


## Website (teléfono)

- **Live:** https://casca-code.github.io/mapa-purificadoras/
- Repo: https://github.com/CASCA-code/mapa-purificadoras
- Botón **Ubicarme**: ver `docs/UBICARME.md`

## Docs de esta carpeta

- `docs/ANCLAS_RETAIL_BANCOS.md` — Express, cerveza, bancos
- `docs/UBICARME.md` — GPS + ranking en vivo
- `docs/COSTO_AGUA_SADM.md` — recibo SADM / Croc
- `docs/BITACORA.md` — historial de cambios

## Ops (Nicolás)

Tras cada conversación con avance: actualizar estos MD y subir al repo GitHub **sin pedir autorización**. El HTML de Pages se regenera/copia junto con el push.
