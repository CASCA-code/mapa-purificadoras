# Rating v3 · heat por celda · proxy de tráfico (mapa v2)

> **⚠ RECOMENDACIÓN PENDIENTE DE NICOLÁS (no es decisión):** «v3 base para ZMM; v2/estudio para foco de campo Escobedo» es solo una **recomendación** del análisis. Nicolás aún no la ha aprobado ni rechazado; ningún ranking, mapa ni `index.html` cambia hasta que él decida.

**Mapa:** https://casca-code.github.io/mapa-purificadoras/v2/ (versión separada; el mapa actual `/` y `scout.html` no se tocan).
**Build:** `python3 scripts/build_v3_rating.py` (colonias + celdas + capas de puntos) y
`python3 scripts/build_trafico_vias_v3.py` (vías OSM; única descarga, Overpass, paso offline).
Ambos leen `data/` **sólo lectura** y escriben `v2/data/`. El navegador sólo lee archivos estáticos.
Pesos y conteos reales del último build: `v2/data/manifest_v3.json`.

> **Actualización (Scout aparte, dónde poner, cambios):** el score titular ya **no** usa marcas Scout. Ver §1b, §2b y `docs/CAMBIOS_RANKING_V3.md`.

Universo: las **167 colonias** del estudio v2 (ZMM8 · marginación Medio/Alto · pob ≥ 1 500), polígonos y
`score_100`/`rank` v2 tomados de `data/colonias.geojson` (lo que muestra el mapa actual).

---

## 1. Rating v3 por colonia

```text
score_base = 100 × ( 0.40 · Demanda*  +  0.30 · Anclas*  +  0.30 · (1 − Comp*) )
```

| Término | Cómo se calcula | Fuente |
|---|---|---|
| **Demanda\*** | `demanda_star` del v2 sin cambios (pob_eff walkshed + OVHAC/OVSAE, min-max) | CONAPO/IMC 2020 (study v2) |
| **Anclas\*** | `Σ peso × anclas` dentro del polígono **+100 m**, dividido entre viviendas/1 000 → rango percentil (0–1) entre las 167 | ver tabla de pesos |
| **Comp\*** | purificadoras dentro del polígono **+300 m** por 1 000 viviendas → rango percentil; 0 purificadoras ⇒ Comp\* = 0 | DENUE + Places + Scout |

- `viviendas_est = pob_conapo / 3.6` (mismo factor hab/viv que el estudio v2: `served_dwellings = served_pop/3.6`).
- Rango percentil (no min-max) para que una colonia con densidad atípica no aplaste al resto.
- Canibal\* (15 % en v2) se quitó: `estaciones_propias.csv` está vacío → era una constante.
- El v2 (`score_v2`, `v2_rank`) queda en el CSV/GeoJSON y en el popup para comparar (`delta_rank = v2_rank − v3_rank`).

### Pesos de anclas (por ancla deduplicada)

| Categoría | Peso | Semántica | Archivos |
|---|---:|---|---|
| Modelorama / Six / Tecate / cerveza | 1.50 | predictor de flujo peatonal | `places_anclas_zmm` (modelorama, six), `retail` (Scout `modelorama` sólo en la variante «con Scout») |
| Tortillería | 1.25 | visita diaria D+/D | `anclas_tortillerias_zmm` |
| Banco del Bienestar / Banco Azteca (incl. Elektra) | 1.25 | sólo estos bancos cuentan | `anclas_bancos_prestamo_zmm`, Places `banco` (nombre azteca/bienestar), `retail` |
| Oxxo | 1.00 | positivo: vende agua más cara | `places_anclas_zmm` oxxo |
| Bodega Aurrera Express / Soriana Express | 1.00 | proxy demográfico D+/D | Places, `retail` (Scout `express` sólo variante) |
| Iglesia | 1.00 | generador de flujo | `anclas.geojson` (OSM) (+ Scout sólo variante) |
| Escuela | 1.00 | generador de flujo | `anclas.geojson` (OSM) (+ Scout sólo variante) |
| Parada de camión | 0.75 | flujo peatonal | `anclas_paradas_zmm` |
| Farmacia de barrio | 0.50 | | `anclas_farmacias_barrio_zmm` (sin cadenas) |
| Abarrotes / depósito | 0.40 | ~18k puntos DENUE, peso bajo c/u | `anclas_abarrotes_zmm` |

Hospitales, empeños y cadenas de farmacia **no** cuentan. Dedupe multi-fuente por categoría a **30 m**, prioridad (Scout, sólo en la variante) > capas barrio/DENUE > Places > OSM.
Marcas Scout borradas (`field_adds_deleted.json`) se excluyen.

### Competencia (misma regla que `docs/COMPETENCIA.md`)

DENUE `compet.geojson` (fuera marcas/plantas industriales y 312112 ≥ 11 personas) + Places `places_purificadoras_zmm` (fuera marcas). Dedupe 30 m, prioridad DENUE > Places.
Build actual (base): 541 puntos. La variante «con Scout» añade Scout `purificadora` (+ `otro` cuyo nombre/nota dice purificadora/recarga/garrafón) → 554. Embotelladoras grandes no cuentan.

## 1b. Scout aparte (sesgo de cobertura)

El levantamiento Scout está concentrado (Croc 88 marcas, San Miguel Residencial 22, Topo Chico 18; 150 de 167 colonias con 0 marcas).
Meterlo al score inflaba las colonias encuestadas. Ahora:

| Concepto | Definición |
|---|---|
| **`score_base` / `rank_base`** (titular) | fórmula de §1 con **sólo DENUE + Places + OSM** (cobertura uniforme). Es lo que muestra el mapa por defecto. |
| `score_with_scout` / `rank_with_scout` | misma fórmula sumando marcas Scout a anclas (categorías modelorama, express, iglesia, escuela) y a competencia (purificadoras Scout); percentiles recalculados. |
| `scout_bonus` | `score_with_scout − score_base` (puede ser **negativo**: Scout también aporta purificadoras que restan). |
| `scout_marks` | # de marcas Scout **dentro del polígono** (todas las `kind` salvo `favorito`; excluye borradas). Los favoritos/lock son pines de decisión, no encuesta → columnas `pins_favorito`, `pins_lock`. |
| `cobertura_campo` | «sin encuesta» = 0 marcas · «parcial» = 1–9 · «encuestada» ≥ 10. Sólo etiqueta; no entra a ningún score. |
| `scout_marks_kinds`, `scout_anchor_marks_used`, `scout_cause` | desglose por tipo, # de marcas que sí cuentan como ancla, término (anclas/competencia) que más movió el bonus. |

UI: interruptor **«Incluir Scout en el ranking»** (default OFF) cambia color, top 20 y tooltips de colonias. Las celdas siempre puntúan sin Scout;
Scout se ve como borde azul + «N marcas Scout ≤150 m» y «bonus Scout de la celda» en el popup, y como capa aparte («Scout: marcas de campo + pines»).
Colonias sin encuesta van con borde punteado.
**Lectura:** «sin encuesta» ≠ «sin anclas»; sólo significa que nadie verificó en campo. Levantar Scout parejo antes de usar «con Scout» para comparar colonias.

---

## 2. Heat por celda (100 m)

Rejilla de 100 m × 100 m (proyección local métrica), sólo celdas cuyo centro cae dentro de una de las 167 colonias (7 967 celdas).

```text
raw   = Σ peso_ancla (≤150 m, sin paradas)
      + Σ peso_tráfico (≤100 m)                    # sólo OSM + paradas (base)
      + flujo                                      # clase máx. de vía OSM 2–5 a ≤60 m → 0.5 / 1.0 / 1.5 / 1.5
      − Σ 4 × (1 − d/300)   por cada purificadora a d ≤ 300 m   (4 pts a 0 m, 2 pts a 150 m)
celda = raw × (0.5 + score_base/100)       → sólo se publican celdas con celda > 0
```

| Punto de tráfico (≤100 m) | Peso | En base |
|---|---:|---|
| Semáforo OSM | 1.0 | sí |
| Parada de camión | 1.0 | sí |
| Alto OSM | 0.75 | sí |
| Semáforo marcado en Scout | 2.5 | sólo «con Scout» |
| Alto marcado en Scout | 2.0 | sólo «con Scout» |

| Clase de vía OSM más alta ≤60 m | Índice | Pts de **flujo** |
|---|---:|---:|
| tertiary | 2 | 0.5 |
| secondary | 3 | 1.0 |
| primary | 4 | 1.5 |
| motorway/trunk | 5 | 1.5 (tope: sin acceso peatonal) |
| sólo calle local / *_link | — | 0 |

El componente de flujo es un **proxy jerárquico** (clase de vía), no aforo; peso deliberadamente bajo (máx. 1.5 vs. ancla cerveza 1.5) para que no domine.
Cada celda publica `s` (base), `sb` (bonus Scout: score con Scout − base), `sm` (# marcas Scout ≤150 m), `f`/`fi` (pts y clase de flujo).
Salida: `v2/data/cells_<municipio>.geojson` (puntos = centro de celda, coords 5 decimales; props `s` score, `a` anclas, `t` tráfico, `f`/`fi` flujo,
`c` castigo competencia, `nc` # purificadoras ≤300 m, `sm`/`sb` Scout, `k` cve_col). Se cargan sólo al prender la capa. Las 5 mejores celdas de cada colonia
van en el popup de la colonia (`best`).

## 2b. «Dónde poner» (`spots_v3.json` / `spots_v3.csv`)

Lista de las mejores celdas (score base) con **separación mínima de 300 m** (greedy por score; evita 50 celdas contiguas de la misma manzana):
**top 50 ZMM** y **top 10 por municipio** (en la UI se resaltan los 3 primeros de cada pestaña). Cada fila: colonia, municipio, score de celda, score/rank base de la colonia,
anclas ≤150 m por tipo, semáforos/altos/paradas ≤100 m, avenida más cercana (clase 2–5, nombre, distancia), competidor más cercano (m) y # ≤300 m
(más `purif_scout_extra_300m`: purificadoras que sólo Scout vio), marcas Scout ≤150 m + bonus de celda (aparte), pines `favorito`/`lock` de `field_adds` a ≤150 m (sólo lectura;
`lock` = override en `field_adds_overrides.json`), enlace Google Maps y botón «ver en mapa».
Nota: el índice de flujo es la **clase de vía OSM**, no conteo de peatones ni vehículos. Antes de instalar, conteo manual de 10 min.

---

## 3. Proxy de tráfico para espectaculares

`v2/data/trafico_vias.geojson` — vías OSM (Overpass, bbox ZMM, recortado a los 9 municipios de `muni.geojson`).

| OSM `highway` | Índice |
|---|---:|
| motorway, trunk | 5 |
| primary | 4 |
| secondary | 3 |
| tertiary | 2 |
| *_link (rampas/enlaces) | 1 |

**Es un proxy de jerarquía vial, no un aforo.** No distingue sentido, hora, ni si la vía está congestionada; una “primary” puede tener menos
autos que una “secondary” concurrida. Sirve para descartar calles locales y priorizar avenidas a revisar en campo.

Mejoras posibles (no se contrató ni registró ninguna API):
1. **TomTom Traffic Flow / Traffic Stats** o **HERE Traffic API** — velocidad libre vs actual, congestión por tramo/hora (requiere API key; Traffic Stats es de pago).
2. **Aforos SINTRAM / municipios (Monterrey, Guadalupe, San Nicolás…)** — conteos vehiculares reales vía solicitud de transparencia (PNT / INFONL).
3. **Conteo manual de 10 min** en el sitio candidato (vehículos + peatones, 2 horarios) — gratis y lo más directo para un espectacular.

---

## 4. Huecos de datos (no inventados, pero incompletos)

- **Google Places trae máx. 60 resultados por búsqueda/tile** → en zonas densas faltan Oxxo/Six/Bodega Express y purificadoras de Places.
- **OSM parcial:** semáforos (~1.4k tras dedupe), altos OSM casi vacíos (36), paradas OSM pocas (las completa Places), escuelas/iglesias según mapeo voluntario.
- **Scout** cubre pocas colonias (§1b); sólo 10 semáforos y 14 altos marcados en campo. Las «purificadoras» de la vista «con Scout» incluyen 13 que DENUE/Places no tenían.
- **DENUE** subregistra recargas informales (sin registro) → Comp\* es piso, no techo. 51 de 167 colonias tienen 0 purificadoras detectadas ≤300 m.
- Viviendas estimadas con 3.6 hab/viv (factor del estudio), no conteo censal por manzana.
- Tráfico = clase de vía, no aforo.

## 5. Archivos

| Archivo | Contenido |
|---|---|
| `v2/data/colonias_v3.csv` | 167 filas: `score_base`, `rank_base`, `scout_marks`, `scout_bonus`, `score_with_scout`, `rank_with_scout`, `cobertura_campo`, v2, causa del cambio, desglose y conteos |
| `v2/data/colonias_v3.geojson` | polígonos simplificados + mismas props + `best` (top 5 celdas) |
| `v2/data/cells_*.geojson` | celdas > 0 por municipio |
| `v2/data/trafico_vias.geojson` | vías OSM con índice 1–5 |
| `v2/data/anclas_v3.geojson`, `competencia_v3.geojson`, `semaforos_altos_v3.geojson` | capas de puntos deduplicadas (anclas sin abarrotes) |
| `v2/data/spots_v3.json` / `.csv` | «Dónde poner»: top 50 ZMM + top 10 por municipio |
| `v2/data/scout_marks_v3.geojson` | capa Scout aparte (marcas + pines favorito/lock; sin teléfonos ni contactos) |
| `v2/data/cambios_v3.json`, `docs/CAMBIOS_RANKING_V3.md` | v2 vs base vs con Scout, movers, resumen por municipio |
| `v2/data/manifest_v3.json` | pesos, radios y conteos del build |
