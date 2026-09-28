# Rating v3 · heat por celda · proxy de tráfico (mapa v2)

**Mapa:** https://casca-code.github.io/mapa-purificadoras/v2/ (versión separada; el mapa actual `/` y `scout.html` no se tocan).
**Build:** `python3 scripts/build_v3_rating.py` (colonias + celdas + capas de puntos) y
`python3 scripts/build_trafico_vias_v3.py` (vías OSM; única descarga, Overpass, paso offline).
Ambos leen `data/` **sólo lectura** y escriben `v2/data/`. El navegador sólo lee archivos estáticos.
Pesos y conteos reales del último build: `v2/data/manifest_v3.json`.

Universo: las **167 colonias** del estudio v2 (ZMM8 · marginación Medio/Alto · pob ≥ 1 500), polígonos y
`score_100`/`rank` v2 tomados de `data/colonias.geojson` (lo que muestra el mapa actual).

---

## 1. Rating v3 por colonia

```text
score_v3 = 100 × ( 0.40 · Demanda*  +  0.30 · Anclas*  +  0.30 · (1 − Comp*) )
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
| Modelorama / Six / Tecate / cerveza | 1.50 | predictor de flujo peatonal (en Scout = cualquier depósito/abarrotes grande) | Scout `modelorama`, `places_anclas_zmm` (modelorama, six), `retail` |
| Tortillería | 1.25 | visita diaria D+/D | `anclas_tortillerias_zmm` |
| Banco del Bienestar / Banco Azteca (incl. Elektra) | 1.25 | sólo estos bancos cuentan | `anclas_bancos_prestamo_zmm`, Places `banco` (nombre azteca/bienestar), `retail` |
| Oxxo | 1.00 | positivo: vende agua más cara | `places_anclas_zmm` oxxo |
| Bodega Aurrera Express / Soriana Express | 1.00 | proxy demográfico D+/D | Scout `express`, Places, `retail` |
| Iglesia | 1.00 | generador de flujo | `anclas.geojson` + Scout |
| Escuela | 1.00 | generador de flujo | `anclas.geojson` + Scout |
| Parada de camión | 0.75 | flujo peatonal | `anclas_paradas_zmm` |
| Farmacia de barrio | 0.50 | | `anclas_farmacias_barrio_zmm` (sin cadenas) |
| Abarrotes / depósito | 0.40 | ~18k puntos DENUE, peso bajo c/u | `anclas_abarrotes_zmm` |

Hospitales, empeños y cadenas de farmacia **no** cuentan. Dedupe multi-fuente por categoría a **30 m**, prioridad Scout > capas barrio/DENUE > Places > OSM.
Marcas Scout borradas (`field_adds_deleted.json`) se excluyen.

### Competencia (misma regla que `docs/COMPETENCIA.md`)

DENUE `compet.geojson` (fuera marcas/plantas industriales y 312112 ≥ 11 personas) + Places `places_purificadoras_zmm` (fuera marcas) +
Scout `purificadora` (+ `otro` cuyo nombre/nota dice purificadora/recarga/garrafón). Dedupe 30 m, prioridad Scout > DENUE > Places.
Build actual: 572 → **554** puntos. Embotelladoras grandes no cuentan.

### Chequeo de sesgo Scout

El levantamiento Scout está concentrado (63 marcas en Croc, 20 en San Miguel Residencial, 16 en Topo Chico).
Por eso se publica también `score_v3_sin_scout` / `rank_v3_sin_scout` (misma fórmula sin marcas Scout).
Ej.: Croc #1 con Scout → #20 sin Scout; San Miguel Residencial #4 → #23. Las colonias sin levantamiento no se ven afectadas.
**Lectura:** donde no hay Scout, v3 subestima anclas; levantar Scout parejo antes de comparar colonias muy distintas.

---

## 2. Heat por celda (100 m)

Rejilla de 100 m × 100 m (proyección local métrica), sólo celdas cuyo centro cae dentro de una de las 167 colonias (7 967 celdas).

```text
raw   = Σ peso_ancla (≤150 m, sin paradas)
      + Σ peso_tráfico (≤100 m)
      − Σ 4 × (1 − d/300)   por cada purificadora a d ≤ 300 m   (4 pts a 0 m, 2 pts a 150 m)
celda = raw × (0.5 + score_v3/100)       → sólo se publican celdas con celda > 0
```

| Punto de tráfico (≤100 m) | Peso |
|---|---:|
| Semáforo marcado en Scout | 2.5 |
| Alto marcado en Scout | 2.0 |
| Semáforo OSM | 1.0 |
| Parada de camión | 1.0 |
| Alto OSM | 0.75 |

Scout es la fuente primaria de semáforos/altos; OSM se descarta si está a ≤15 m de una marca Scout.
Salida: `v2/data/cells_<municipio>.geojson` (puntos = centro de celda, coords 5 decimales; props `s` score, `a` anclas, `t` tráfico,
`c` castigo competencia, `nc` # purificadoras ≤300 m, `k` cve_col). Se cargan sólo al prender la capa. Las 5 mejores celdas de cada colonia
van en el popup de la colonia (`best`).

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
- **Scout** cubre pocas colonias (ver §1 sesgo); sólo 10 semáforos y 14 altos marcados en campo.
- **DENUE** subregistra recargas informales (sin registro) → Comp\* es piso, no techo. 51 de 167 colonias tienen 0 purificadoras detectadas ≤300 m.
- Viviendas estimadas con 3.6 hab/viv (factor del estudio), no conteo censal por manzana.
- Tráfico = clase de vía, no aforo.

## 5. Archivos

| Archivo | Contenido |
|---|---|
| `v2/data/colonias_v3.csv` | 167 filas: v3 + v2 + desglose + conteos por categoría + chequeo sin Scout |
| `v2/data/colonias_v3.geojson` | polígonos simplificados + mismas props + `best` (top 5 celdas) |
| `v2/data/cells_*.geojson` | celdas > 0 por municipio |
| `v2/data/trafico_vias.geojson` | vías OSM con índice 1–5 |
| `v2/data/anclas_v3.geojson`, `competencia_v3.geojson`, `semaforos_altos_v3.geojson` | capas de puntos deduplicadas (anclas sin abarrotes) |
| `v2/data/manifest_v3.json` | pesos, radios y conteos del build |
