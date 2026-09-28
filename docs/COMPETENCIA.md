# Purificadoras (competencia) — una sola capa

Toggle **Purificadoras (competencia)** (panel Anclas, apagado por defecto). Reemplaza a
«Competencia (recarga)», «Competencia (planta)» y «Purificadoras (Places + Scout)».

## Fuentes (todas archivos estáticos en `data/`)

| Fuente | Archivo | Ícono |
|---|---|---|
| DENUE (INEGI, SCIAN 312112 + recarga de barrio) | `data/compet.geojson` | círculo rojo **D** |
| Google Places (purificadora / recarga / garrafón) | `data/places_purificadoras_zmm.geojson` | círculo azul punteado **G** |
| Scout / campo (hotkey **Y**, botón Comp) con precios | `data/field_adds.geojson` `kind=purificadora` (+ localStorage del teléfono) | teal punteado **Y** · «Añadida con Scout» |
| Anclas `otro` cuyo nombre/nota dice purificadora / recarga de agua / garrafón | `field_adds` | → se pintan como Scout **Y** |

Se incluyen estaciones de agua al menudeo, purificadoras de barrio, recargas y plantas chicas (DENUE industrial con 0–10 personas).

## Dedupe

~**30 m** = mismo negocio. Prioridad **Scout > DENUE > Places**. El gemelo de menor prioridad no se pinta,
pero queda registrado: el popup muestra **Fuentes: Scout + DENUE (…) + Places (…)** y, si hay Scout, sus precios
(Recarga / Garrafón / Medio / Galón). Scout ↔ Scout nunca se deduplica.

Conteo actual (build `20260928-comp-merge`): **560** puntos en el toggle (DENUE + Places + 15 Scout, ya deduplicados); 21 excluidos.

## Exclusiones (plantas embotelladoras industriales)

Regla en `index.html` (`compExcludeDenue` / `compExcludePlaces`):

1. **Nombre / razón social** coincide con `COMP_EXCL_NAME_RE`:
   `bonafont · ciel · e-pura/epura · santorini · electropura · embotelladora · envasadora · cedis · industrial ·
   laboratorios · liquitek · coca-cola · pepsi · bebidas mundiales · arca continental · aquafina · soy sanna`
2. **DENUE canal `industrial/embotellador` (SCIAN 312112) con estrato ≥ 11 personas.**

Excluidos hoy (21):

| Fuente | Nombre | Estrato | Motivo |
|---|---|---|---|
| DENUE | AGUA INDUSTRIAL DE MONTERREY | 31–50 | marca/planta industrial |
| DENUE | AGUA PURIFICADA CIÉNEGA | 11–30 | 312112 ≥11 |
| DENUE | AGUA PURIFICADA LA PEÑITA | 51–100 | 312112 ≥11 |
| DENUE | AGUA STAR (Garza Elizondo y Cía.) | 251+ | 312112 ≥11 |
| DENUE | AQUA FINA | 11–30 | marca |
| DENUE | BONAFONT – BEC Monterrey CEDIS (×2) | 0–5 / 101–250 | marca |
| DENUE | BONAFONT – BEC Nueva Esperanza CEDIS | 0–5 | marca |
| DENUE | BONAFONT – BEC Santa Catarina CEDIS | 0–5 | marca |
| DENUE | ELECTROPURA | 51–100 | marca |
| DENUE | Envasadora de Aguas en México – Monterrey planta | 251+ | marca (Epura/Ciel) |
| DENUE | Envasadora de Aguas en México – Santa Catarina planta | 31–50 | marca |
| DENUE | GRUPO VEBIAR | 11–30 | 312112 ≥11 |
| DENUE | HIDROPURIFICADORA STAR | 101–250 | 312112 ≥11 |
| DENUE | LABORATORIOS MONTERREY | 31–50 | marca |
| DENUE | LIQUITEK DE MÉXICO | 11–30 | marca |
| DENUE | SOY SANNA | 11–30 | marca |
| DENUE | WATER HOUSE (Purificadora Salba) | 11–30 | 312112 ≥11 |
| Places | Bonafont Cedis | — | marca |
| Places | Bonafont Guadalupe | — | marca |
| Places | CIEL Juventud (Bebidas Mundiales) | — | marca |

Lista viva en consola: `window.__purifCompExcluded`.
Se conserva **AGUA DEL CIELO REGIO** (DENUE industrial, 0–5 personas; «cielo» ≠ marca Ciel).

El score_100 de colonias (Comp*, `n_recarga_1km` / `n_industrial_1km`) está precalculado y no cambia con esta capa visual.

## Regla de datos

El mapa **sólo lee archivos guardados** en `data/` (DENUE, Places, OSM, Scout/field_adds). Nunca llama a Places
API ni Overpass en vivo. Para refrescar: correr los scripts `scripts/fetch_*.py` (offline, con key) y commitear el GeoJSON.
Única llamada externa del mapa aparte de teselas: Nominatim reverse (nombre de colonia en «Ubicarme»), no es fuente de puntos.
