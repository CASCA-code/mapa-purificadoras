#!/usr/bin/env python3
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open("/workspace/downloads/scout_top30_stats.json"))
T = pd.read_csv(f"{ROOT}/v2/data/scout_top30_retail.csv")
L = []; w = L.append
w("# Scout: top 30 celdas de comercio de barrio (OSM) aún sin encuestar\n")
w("Fecha: **2026-10-02**. Lista de **plan de campo para Nicolás**; no se hizo trabajo de campo ni se contactó a nadie. VERIFICADO = conteo en el archivo citado; SUPUESTO = inferencia. **No altera ningún score.** Scripts: `scripts/analisis_scout_top30_retail.py`, `scripts/doc_scout_top30_retail.py`. Tabla: `v2/data/scout_top30_retail.csv` (30 filas).\n")
w("## 1. Datos y método\n")
w("- Consulta pedida: OSM `shop=supermarket|convenience`, bbox lat 25.52..25.92, lon −100.70..−100.00. **Overpass no respondió** hoy: `overpass.private.coffee` (2 intentos, timeout 120 s/100 s sin bytes), `overpass-api.de`, `lz4.overpass-api.de`, `overpass.kumi.systems`, `maps.mail.ru` (sin respuesta) y `overpass.openstreetmap.fr` (403 «only white-listed»). Se mantuvo ritmo bajo (≈1 petición por mirror, sin reintentos agresivos).")
w("- **Fallback (público, mismo contenido OSM):** extracto Geofabrik `mexico-260929.osm.pbf` (2026-09-29) ya en la caja (`/home/box/geo/base_mty/raw/pbf/`), leído con pyosmium: nodos `shop=…` en el bbox + vías `shop=…` (centroide de sus nodos; relaciones omitidas). Raw: `/workspace/downloads/osm_retail_zmm_raw.json` (**1,792 elementos**: nodos 905 + vías 887 — VERIFICADO en el log). © OpenStreetMap contributors, ODbL.")
w(f"- Dedupe: {S['n_dup_interno']} duplicados internos a ≤30 m; **{S['n_dup_anclas_v3']} más a ≤30 m de un ancla v3 de categoría oxxo/express/cerveza** (`v2/data/anclas_v3.geojson`, misma regla de 30 m que v3) → quedan **{S['n_unicos']:,}** puntos OSM (convenience {S['shops']['convenience']:,}, supermarket {S['shops']['supermarket']}) que **no están en anclas_v3**. Los abarrotes DENUE no se restan (no están en anclas_v3).")
w(f"- Celdas: **H3 resolución 8** (`h3` 4.5.0 instalado con pip en venv local; ≈0.74 km², lado ≈460 m): {S['n_hex']} celdas con ≥1 punto; mediana {S['mediana_hex']:.0f} puntos/celda, máx. {S['max_n']}. {S['n_hex_en_colonias']} celdas tocan una de las 167 colonias.")
w(f"- «Sin encuestar» = **0 marcas de encuesta Scout** dentro de la celda (`scout_marks_v3.geojson`, excluidos pines favorito/lock). {S['n_hex_surveyed']} celdas ya tienen marcas. La columna `scout_vecinos_ring1` muestra marcas en celdas vecinas (sólo informativa).")
w(f"- Elegibles: sin marcas Scout, ≥15 % de la celda dentro de una colonia de las 167 (evita celdas que sólo rozan el polígono) → **{S['n_elig']}** celdas; se listan las 30 con más puntos (desempate por # supermercados). Con tan pocas elegibles, **de la posición ~13 en adelante hay empates en 2–4 puntos**: el orden fino no es significativo.\n")
w("## 2. Lista de campo (top 30)\n")
w("| # | Celda H3 r8 | Pts OSM (super/conv) | Colonia | Municipio | Rango base | Comp. v3 ≤300 m | Confianza banda | Mapa |\n|--:|---|---|---|---|--:|--:|---|---|")
for _, x in T.iterrows():
    w(f"| {x.prioridad} | `{x.h3}` | {x.n_total} ({x.n_super}/{x.n_conv}) | {x.colonia} | {x.municipio} | {int(x.rank_base_colonia)} | {int(x.comp_300m_colonia)} | {x.confianza_colonia} | [ver]({x.gmaps}) |")
w(f"\nPor municipio: " + ", ".join(f"{k} {v}" for k, v in S["top30_municipios"].items()) + f". Confianza de banda de la colonia: " + ", ".join(f"{k} {v}" for k, v in S["top30_confianza"].items()) + ". Ninguna de las 30 está en el top-30 del rango base (`top30_rank_base_le30 = %d`): esta lista **no** persigue las mismas colonias que el ranking; mide comercio de paso aún no verificado.\n" % S["top30_rank_base_le30"])
w("## 3. Lectura y límites\n")
w("- **Hallazgo (VERIFICADO en los archivos):** OSM trae **%s comercios de barrio que no están en `anclas_v3`** (sólo 337 coinciden con Oxxo/Express/cerveza de v3). Es consistente con el hueco de Google Places (máx. 60 por búsqueda/tile, `docs/RATING_V3.md` §4). Si se integrara OSM retail al ancla «oxxo/express» el Anclas\\* cambiaría; **no se probó ni se aplicó** (pendiente de Nicolás)." % f"{S['n_unicos']:,}")
w(f"- {S['top30_global_en_colonias']} de las 30 celdas más densas de toda la ZMM caen en las 167 colonias; las más densas (19 y 11 puntos) están fuera de las 167 colonias y {S['hex_con_scout_top30_global']} del top-30 global ya tienen Scout.")
w("- `n_nombre_cadena` usa una regex amplia sobre `name`/`brand` (Oxxo, 7-Eleven, Six, Extra, Super City, Soriana, Aurrera, HEB…): **%d de %s** puntos coinciden, o sea casi todo el «convenience» OSM es cadena; no distingue tienda de barrio independiente. Supuesto: más tiendas = más flujo peatonal (mismo supuesto de anclas v3, sin dato de ventas)." % (S["cadenas"], f"{S['n_unicos']:,}"))
w("- Cobertura OSM desigual (voluntaria); una celda con pocos puntos puede ser mapeo incompleto, no ausencia de comercio. «Sin encuestar» ≠ «sin comercio».")
w("- Qué hacer en campo (cuando Nicolás decida): recorrer la celda ~15 min, contar clientes/peatones 10 min en la esquina comercial, anotar en Scout (kind `express`/`otro`/`purificadora`), y revisar recargas informales (`docs/COMPETENCIA_CERO.md`).")
open(f"{ROOT}/docs/SCOUT_TOP30_RETAIL.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
