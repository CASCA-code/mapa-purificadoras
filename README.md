# Mapa Purificadoras (ZMM)

Sitio público del **Mapa Version 2** — site selection de estaciones de recarga de garrafón (~19 L) en la Zona Metropolitana de Monterrey.

**Abrir el mapa:** https://casca-code.github.io/mapa-purificadoras/

## Contenido del repo

| Archivo | Qué es |
|---|---|
| `index.html` | Mapa Leaflet offline (score_100, capas, Ubicarme) |
| `scout-sv.html` | Scout SV — Street View remoto (pines hotkey) |
| `docs/` | Notas operativas (anclas, GPS, SADM, bitácora) |
| `README.md` | Este archivo |

Fuente de trabajo local (PC Nicolás): `OneDrive/Desktop/purificadora/version2/`

## Cómo usar en el teléfono

1. Abre el link de Pages en Chrome/Safari.
2. Toca **Ubicarme** y acepta ubicación.
3. Enciende/apaga capas de anclas (Aurrera Express, Soriana Express, cerveza, Bienestar, Azteca) en el rail.

## Actualización

El agente Purificador actualiza MD + HTML y hace push tras cada avance de conversación (regla del 2026-09-12).


## Ruta de campo
Panel **ruta** en el rail: arma un circuito desde casa (Violeta 116, Los Colorines, San Pedro) por colonias del ranking y abre Google Maps. Ver `docs/RUTA_CAMPO.md`.


## Mapa Tec (estudiantes)
https://casca-code.github.io/mapa-purificadoras/tec/ — deptos + Oxxo/Super7 + purificadoras cerca del Campus Monterrey. Ver `docs/MAPA_TEC_ESTUDIANTES.md`.


## Fórmula del score
Cómo se llegó a `score_100`: [`docs/FORMULA_SCORE.md`](docs/FORMULA_SCORE.md).


## Scout SV (Street View remoto)
https://casca-code.github.io/mapa-purificadoras/scout-sv.html — camina panoramas y marca competencia/anclas con teclado. Ver [`docs/SCOUT_SV.md`](docs/SCOUT_SV.md). Cache-bust: `?v=<sha7>`.
