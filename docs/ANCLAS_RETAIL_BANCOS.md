# Anclas retail y bancos (alto flujo)

Fecha: 2026-09-12  
Estado: activo en Version 2 (capas + Anclas*)

## Por qué

Nicolás: estos puntos son proxy de **alto flujo** peatonal/comercial en zonas D+/D. Entran al score solo vía **Anclas\*** (no tocan Demanda\* ni Comp\*).

## Categorías y pesos

| Categoría | Peso | n (ZMM, snapshot) | Notas de filtro |
|---|---:|---:|---|
| Bodega Aurrera Express / Mi Bodega Aurrera | 0.90 | 69 | Excluye hiper / Bodega Aurrera “grande” sin Express |
| Soriana Express | 0.90 | 3 | OSM sin Express en ZMM → 3 puntos curados (verificar en campo; Dos Ríos approx) |
| Modelorama / Six / cerveza specialty | 0.80 | 21 | Excluye OXXO y conveniencia general |
| Banco del Bienestar | 0.85 | 3 | OSM escaso; mejorar con DENUE cuando haya token |
| Banco Azteca | 0.85 | 22 | OSM + proxy Elektra co-ubicación |

Radio / decay: igual que anclas OSM — `peso·exp(−d/250)` a ≤250 m del **centroide** de colonia.

## Archivos

- `anclas_retail_bancos.geojson` / `.csv`
- `fetch_anclas_retail_bancos.py`
- Capas en mapa: toggles A / S / C / B / Z

## Fuera de alcance (explícito)

- Casas abandonadas: **no**
- Haitianos / migración por colonia: **no**

## Efecto en ranking

Tras el primer merge (2026-09-12), el **Top 10 no cambió**: casi ningún punto nuevo cae ≤250 m de centroides de las top colonias. Sí mueve Anclas\* en colonias medias (ej. Prados de La Cieneguita, Cañada Blanca, Unidad Pedreras).
