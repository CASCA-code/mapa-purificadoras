# B4 (BORRADOR): qué se tomó de B2 y de B3

**Página:** https://casca-code.github.io/mapa-purificadoras/b4/ — `noindex`, etiqueta visible «BORRADOR B4», **sin enlace desde el hub**. Archivos nuevos: `b4/index.html`, `b4/data/*`, `docs/B4_ECONOMIA.md`, `docs/B4_MEZCLA.md`, `data/b4_escenarios.csv`, `data/b4_escalonado.csv`, `scripts/build_b4.py`. No se tocó `index.html` del hub, `scout.html`, ni `v2/` / `v3_espectaculares/`.

## 0. Cómo interpreté «B2» y «B3» (hallazgo importante)

Pedido de Nicolás vía Yamil: «B4 = lo mejor de B2 y B3; le gusta el UI de B2; si las fórmulas de B3 son mejores, úsalas». No hay ningún documento del repo que nombre «B1–B4» (búsqueda por texto: ninguna coincidencia). Usé esta lectura (la interpretación del encargo, confirmada contra el contenido de los archivos):

| Nombre | Qué es en el repo | Qué contiene realmente |
|---|---|---|
| (#1) hub | `index.html` | Mapa actual, ranking **v2** (`score_100`, 0.40/0.25/0.20/0.15). Intocable. |
| **B2** | `v2/index.html` (URL `/v2/`) | **UI** de panel con pestañas Ranking / Dónde poner / Cambios / Capas **y ya calcula el rating v3 base** (`score_base = 100·(0.40·Demanda* + 0.30·Anclas* + 0.30·(1−Comp*))`, `docs/RATING_V3.md`), Scout aparte, heat por celda 100 m, «dónde poner». |
| **B3** | `v3_espectaculares/index.html` (+ README, `docs/BANDA_CONFIANZA.md`, `docs/V2_VS_V3.md`) | Mapa de **espectaculares/paradas**: `score = personas × autos` por parada (Metro con afluencia STC nov-2025, sentido vial, TomTom indicativo, top 100 paradas). **No** puntúa colonias. Su UI es la más pulida (escala 4/8, 44 px, focus visible). La banda de confianza y la comparación v2/v3 viven en docs/datos de la línea v3, no en una página. |

Consecuencia: **las «fórmulas v3» ya estaban dentro de la página B2**; B3 no tiene una fórmula alternativa de colonias que comparar. Lo que B3/línea-v3 aporta de nuevo y **sí encaja** es la banda de confianza, el índice de afluencia Metro y el tratamiento de «0 competidores = no verificado». Si Nicolás se refería a otra cosa por B2/B3, hay que corregirlo.

## 1. Tomado de B2 (`v2/index.html`)

1. **Estructura y flujo de UI**: panel lateral (escritorio) / hoja inferior (móvil), pestañas Ranking · Dónde poner · Capas · Cambios, ficha de colonia en popup, lista Top 20 con clic → zoom, botón «☰ Panel» en móvil.
2. **Rating v3 base** de las **167 colonias** (`colonias_v3.geojson`: `score_base`, `rank_base`, términos D\*/A\*/C\*, anclas por 1 000 viv, competidores ≤300 m) con **la misma fórmula 0.40/0.30/0.30** (sin cambios).
3. **Interruptor «Incluir Scout en el ranking»** (default OFF), borde punteado «sin encuesta», capa Scout aparte.
4. **Pestaña «Dónde poner»** (mejores celdas de 100 m con anclas, semáforos/altos/paradas, flujo por clase de vía OSM, competidor más cercano) — con separación cambiada (ver §3).
5. **Heat por celda 100 m**, capas de tráfico (proxy OSM 1–5), anclas, purificadoras, semáforos/altos, fondo satélite Esri.
6. **Pestaña «Cambios v2→v3»** (histórico de movimiento de ranking), sin cambios de contenido.
7. **Paleta/rampas** de color (rosa para colonias, amarillo→rojo para celdas) y tiles **Esri World_Street_Map**.

## 2. Tomado de B3 / línea v3

1. **Banda de confianza** (`colonias_v3_banda_confianza.csv`, `docs/BANDA_CONFIANZA.md`): para cada colonia, rango p10/p50/p90, ancho, `confianza` alta/media/baja (8/74/85), P(top-30) y P(top-30) bajo estrés. Se muestra en cada fila del ranking, en el popup, y permite **ordenar** por mediana de rango (p50) o por P(top-30) y **filtrar** por confianza. Etiqueta «MODELO, no pronóstico».
2. **«0 competidores = no verificado»** (`V2_VS_V3.md` §3/§7, `COMPETENCIA_CERO.md`, `comp_cero_desconocido` de la banda): insignia «0 comp. sin verificar» en 58 colonias, en vez de tratar el 0 como dato firme.
3. **Capa Metro con afluencia** (`v3_espectaculares/data/metro_afluencia_indice.csv`, 38 estaciones, índice 0–1 = accesos/día hábil nov-2025 ÷ máximo; sólo el índice normalizado, sin conteos crudos). Se dibuja con tamaño ∝ índice, y el popup de colonia indica el Metro a ≤1 km. **Informativa: no entra a ningún score.**
4. **Sistema de diseño pulido de la página B3** (tokens 4/8, tipografía jerárquica, tarjeta de leyenda, objetivos ≥44 px, `focus-visible`, `prefers-reduced-motion`, marcadores de 44 px con círculo visible de 24 px, `text-wrap`, `tabular-nums`) — aplicado según el skill `ui-pulida-y-disenio`; es CSS/patrón de B3 aplicado a la estructura de B2 (el B2 original no cumple 44 px).
5. **Principio de etiquetado honesto** (proxy ≠ aforo, «uso interno», banderas de cautela).

## 3. Decisiones nuevas en B4 (no vienen de B2 ni B3) — todas **[SUPUESTO]**

| Decisión | Valor | Sustento breve |
|---|---|---|
| **Separación mínima entre estaciones en la misma colonia** | **600 m** | = 2 × radio caminable de **300 m** (SUPUESTO ~4–5 min a pie; es el mismo radio que el modelo ya usa para competencia, `R_comp_m = 300`). A <600 m los dos radios de 300 m se traslapan y la 2.ª estación compite con la 1.ª como lo haría un competidor ajeno (canibalización). Más de 600 m desperdicia colonias pequeñas. No hay datos de ventas ni de distancia real que viaja el cliente. |
| **Estaciones sugeridas por colonia** | 1 a 3 (tope 3) | Greedy por score de celda: la mejor celda siempre; 2.ª y 3.ª sólo si su celda ≥ **60 %** de la mejor **y** está a ≥600 m de las ya elegidas. Resultado: 115 colonias→1, 35→2, 17→3 (236 sitios). Umbral 60 % es de juicio; no se calibró con ventas. |
| **«Dónde poner» con 600 m** | filtro sobre `spots_v3.json` | Se aplicó 600 m (antes 300 m) sobre las filas existentes: top ZMM 50→40; los pesos de celda no cambian. |
| **Categoría SADM** | Cat. 6 (comercial) base; Cat. 2 sensibilidad | Ver `B4_ECONOMIA.md` §2. |
| **Precio máquina** | $87,000 | [DATO] Nicolás. |

## 4. Descartado y por qué

| Descartado | De | Por qué |
|---|---|---|
| `score = personas × autos` de paradas y su ranking top 100 | B3 | Es un score de **espectaculares** (visibilidad vehicular), no de demanda de recarga de garrafón; mezclarlo en el rating de colonias no tiene sustento. |
| Sentido vial / dirección del cartel («cartel mira S») | B3 | Sólo aplica a visibilidad de un cartel. |
| Multiplicador TomTom por municipio | B3 | Datos de 1 día, OD industriales, «uso interno»; no representa tráfico urbano y la publicación es agregada por ToS. No se copió. |
| Tráfico de autos como factor de score | B3 | B2 ya trae el proxy de clase de vía en celdas; sin aforos no mejora. |
| Segmentos peatonales EG-personas, todas las paradas | B3 | Capas de contexto de un modelo distinto, 100 KB+ y sin validación para recarga. Sólo se tomó Metro. |
| Metro como **puntos** del score | B3 | La afluencia Metro no está calibrada contra ventas de garrafón; demanda de recarga es residencial. W_MAX = 6 es de juicio. Queda informativa. |
| **Competencia como bonus con tope** | pedido | **No existe en v3**: en v3 la competencia **resta** (`1−Comp*`, 30 %). Sin base en el repo, no se inventó. |
| Ponderación por densidad (`score_dens`) y viviendas Censo | BANDA/SENSIBILIDAD | Es sensibilidad (MODELO), no ranking; ya está reflejada en la banda (p10–p90). Cambiar el titular sin ventas reales no es justificable. |
| Pestaña de diseño v2 viejo (`score_100` 0.40/0.25/0.20/0.15, Canibal\* constante) | hub | Se reemplaza por v3; la canibalización queda como **separación de 600 m**, no como término. |
| Heat de competencia 300 m (`v2/competencia_heat.html`) | B2 (página aparte) | Página separada; no se integró (la capa de purificadoras ya está). |

## 5. Pendiente de Nicolás

- Confirmar qué eran «B2» y «B3» (lectura de esta página, §0).
- Que apruebe separación 600 m / umbral 60 % y Cat. 6 base (todos SUPUESTO).
- Recomendación v3-ZMM / v2-Escobedo sigue pendiente (no se tocó).
