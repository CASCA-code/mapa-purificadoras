#!/usr/bin/env python3
"""Genera docs/SCOUT_ANCLA_EXTRA.md desde v2/data/scout_top30_ancla_extra.csv y /workspace/downloads/ancla_extra_stats.json."""
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = pd.read_csv(f"{ROOT}/v2/data/scout_top30_ancla_extra.csv"); S = json.load(open("/workspace/downloads/ancla_extra_stats.json"))
r = pd.read_csv(f"{ROOT}/v2/data/scout_top30_retail.csv"); ov = len(set(t.h3) & set(r.h3))
C = S["comparacion_tipos"]
cmp_rows = "\n".join(f"| {k} | {v['n']} | {v['nuevos_vs_anclas_v3']} | {v['dentro_167']} | {v['nuevos_dentro_167']} |" for k, v in sorted(C.items(), key=lambda kv: -kv[1]["nuevos_vs_anclas_v3"]))
rows = []
for _, x in t.iterrows():
    nm = x.colonia_cercana if x.dist_a_colonia_m == 0 else f"{x.colonia_cercana} (a {x.dist_a_colonia_m:,} m)"
    comp = f"{int(x.n_bakery)}/{int(x.n_greengrocer)}/{int(x.n_marketplace)}"
    rows.append(f"| {x.prioridad} | `{x.h3}` | {x.n_butcher} | {comp} | {nm} | {x.municipio} | {x.rank_base_colonia} | {x.comp_300m_colonia} | {x.confianza_colonia} | [ver]({x.gmaps}) |")
tab = "\n".join(rows)
md = f"""# Scout: top 30 celdas con carnicerías OSM (ancla extra) aún sin encuestar

Fecha: **2026-10-02**. Lista de **plan de campo para Nicolás**; no se hizo trabajo de campo ni se contactó a nadie. VERIFICADO = conteo en el archivo citado; SUPUESTO = inferencia. **No altera ningún score.** Scripts: `scripts/extract_osm_anchor_extra.py`, `scripts/analisis_scout_ancla_extra.py`, `scripts/doc_scout_ancla_extra.py`. Tabla: `v2/data/scout_top30_ancla_extra.csv` (30 filas).

## 1. Por qué carnicerías (`shop=butcher`)

`anclas_v3.geojson` ya trae parada, tortillería, escuela, farmacia, cerveza, Oxxo, express, iglesia y banco; la lista de Scout anterior (`SCOUT_TOP30_RETAIL.md`) cubrió `shop=supermarket|convenience`. Iglesia (`place_of_worship`) ya está en v3 (306 puntos OSM), así que se descartó. De los candidatos que quedaban conté puntos OSM y cuántos no están a ≤30 m de ningún punto de `anclas_v3` (misma regla de 30 m de v3):

| Tipo OSM | Puntos (tras dedupe 30 m) | Nuevos vs `anclas_v3` | Dentro de las 167 colonias | Nuevos dentro de las 167 |
|---|--:|--:|--:|--:|
{cmp_rows}

- **Carnicería gana por volumen:** {C['butcher']['nuevos_vs_anclas_v3']} puntos nuevos, casi el doble que panaderías ({C['bakery']['nuevos_vs_anclas_v3']}) y 16 veces las fruterías ({C['greengrocer']['nuevos_vs_anclas_v3']}).
- **Mercado/tianguis (`amenity=marketplace`) tiene el vínculo más directo con flujo peatonal, pero solo hay {C['marketplace']['n']} y el etiquetado es ruidoso:** entre los 10 nombres hay «Muebles Villareal», «Soriana Híper», «Penny Riel» y «Multicomercial Guadalupe» (VERIFICADO en el raw); solo cuatro llevan «Mercado» en el nombre («Mercado Popular No. 3 Francisco Villa», «Mercado La Florida», «Mercado Emiliano Zapata» y «Mercado»). No alcanza para 30 celdas.
- **Vínculo con la recarga: SUPUESTO.** Una carnicería de barrio se visita varias veces por semana a pie; quien compra ahí pasa por la calle donde podría haber una estación. No tengo dato de que ese flujo se convierta en compra de garrafón. Es el mismo tipo de supuesto de las anclas de barrio (`ANCLAS_BARRIO.md`).

## 2. Datos y método

- **Overpass no respondió** hoy. Probé `overpass.private.coffee`, `overpass-api.de`, `overpass.kumi.systems` y `lz4.overpass-api.de` con una petición cada uno y 3 s de espera entre ellos: los cuatro cerraron sin conexión (código 000, 0 bytes, timeout 40 s). Antes, `SCOUT_TOP30_RETAIL.md` documentó fallas en los mismos mirrors.
- **Fallback (público, mismo contenido OSM):** extracto Geofabrik `mexico-260929.osm.pbf` (2026-09-29) en la caja, leído con pyosmium: nodos y vías (centroide de sus nodos; relaciones omitidas) con `amenity=marketplace` o `shop=butcher|greengrocer|bakery` en el bbox lat 25.52..25.92, lon −100.70..−100.00. Raw (fuera del repo): `/workspace/downloads/osm_anchor_extra_raw.json`, **{S['n_raw']} elementos** (carnicería {S['por_tipo_raw']['butcher']}, panadería {S['por_tipo_raw']['bakery']}, mercado {S['por_tipo_raw']['marketplace']}, frutería {S['por_tipo_raw']['greengrocer']}). © OpenStreetMap contributors, ODbL.
- Dedupe interno a 30 m dentro del mismo tipo ({S['dup_internos']} duplicados). «Nuevo» = a más de 30 m de cualquier punto de `anclas_v3`. Quedan **{S['n_butcher_nuevos']} carnicerías nuevas** en **{S['n_hex_butcher']} celdas H3 r8** (≈0.74 km² cada una).
- «Sin encuestar» = 0 marcas de encuesta Scout en la celda (`scout_marks_v3.geojson`, sin pines favorito/lock). Las {S['n_hex_butcher']} celdas con carnicería tienen 0 marcas, así que este filtro no recorta nada aquí.
- **Orden:** carnicerías en la celda (máx. {S['max_butcher_hex']}), luego panadería+frutería+mercado en la misma celda (complemento, columna `n_bakery/n_greengrocer/n_marketplace`), luego menor distancia a una de las 167 colonias. Solo hay dos niveles de carnicerías (2 y 1), así que **el orden fino dentro de cada nivel viene de los desempates y no mide demanda**.
- Colonia: la que más se solapa con la celda; si ninguna la toca, la más cercana (distancia en metros desde el centro de la celda, columna `dist_a_colonia_m`).

## 3. Lista de campo (top 30)

Columna «Panad/frut/merc» = panaderías / fruterías / mercados nuevos en la misma celda.

| # | Celda H3 r8 | Carnic. | Panad/frut/merc | Colonia (cercana) | Municipio | Rango base | Comp. v3 ≤300 m | Confianza banda | Mapa |
|--:|---|--:|---|---|---|--:|--:|---|---|
{tab}

Por municipio: {', '.join(f'{k} {v}' for k, v in S['top30_municipios'].items())}. Confianza de banda de la colonia: {', '.join(f'{k} {v}' for k, v in S['top30_confianza'].items())}.

## 4. Lectura y límites

- **Solo {S['top30_dentro_167']} de las 30 celdas tocan una de las 167 colonias**, y {S['top30_dist_le500']} están a ≤500 m de una (VERIFICADO en el CSV). Las otras caen en zonas de comercio fuera de las colonias de marginación media-alta; sirven como señal de dónde hay comercio de paso, no como candidatas directas. Antes de ir, mirar `dist_a_colonia_m`: la más lejana está a {S['top30_dist_max']:,} m.
- **Cobertura OSM desigual (voluntaria).** {S['n_butcher_nuevos']} carnicerías para toda la ZMM es una fracción del comercio real; DENUE las trae por SCIAN y probablemente muchas más (no lo consulté aquí). Una celda sin punto no es una celda sin carnicería.
- Muchas son cadenas de descuento (SuKarne, El Ofertón de Cantú, Carnes San Juan; 9 de las 30 celdas traen SuKarne o El Ofertón de Cantú): atraen volumen de compra semanal. SUPUESTO que ese volumen cruce con un punto de recarga.
- Solapamiento con la lista anterior (`SCOUT_TOP30_RETAIL.md`): **{ov} celdas** están en las dos listas (tienda de conveniencia y carnicería juntas); son las más baratas de visitar primero.
- El rango base de la colonia es de contexto; esta lista no persigue el ranking: {int((t.rank_base_colonia <= 30).sum())} de las 30 celdas tienen como colonia más cercana una del top 30 base.
- Qué hacer en campo (cuando Nicolás decida): caminar la celda ~15 min, contar peatones y clientes 10 min frente a la carnicería, anotar en Scout (kind `otro`) y revisar recargas informales (`docs/COMPETENCIA_CERO.md`).
- Si se quisiera sumar esto a Anclas\\*: no se probó ni se aplicó; requiere decisión de Nicolás.
"""
open(f"{ROOT}/docs/SCOUT_ANCLA_EXTRA.md", "w").write(md); print(len(md))
