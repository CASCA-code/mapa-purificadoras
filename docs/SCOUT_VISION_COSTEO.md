# Scout Visión — costeo y plan (SOLO COSTEO, sin gasto)

Actualizado: 2026-10-02 (hora CDMX) · Estado: **plan/estimación**. No se llamó a ninguna API con cobro (Google Maps / Street View / Places / TomTom), no se usó ninguna key, no se gastó nada. Solo lectura de páginas públicas de tarifas/términos y cálculo con datos locales.

Idea de Nicolás: Scout procesa imágenes de calle, detecta negocios/anclas que faltan en el mapa (Oxxo, Modelorama, purificadora, tortillería, abarrotes, letreros) y propone pines **"sugeridos"**; Nicolás aprueba cada uno.

## 1. Resumen ejecutivo

| | |
|---|---|
| Colonia piloto | **Fomerrey 112 (San Bernabé 9)**, Monterrey, `19039_0289`, #2 del top 10 base v3, 0.43 km², 1,055 viviendas est., **sin encuesta** de Scout |
| Calle transitable | **11.39 km** (OSM, Geofabrik 2026-09-29) |
| Fotos a 1 foto/20 m | **570** posiciones · **1,140** imágenes con 2 ángulos (izq/der) |
| Costo piloto (todos los escenarios) | **de MXN 0 a ≈ MXN 150** (ver tabla §6) — el costo es trivial |
| El problema real | **No es el dinero, es el permiso**: los Términos de Google Maps Platform prohíben bajar/almacenar Street View en bloque y usarlo para ML (§5). Además Street View Static exige **billing activo** y Nicolás ya rechazó el hold de ~MXN 500 (ver `SCOUT_SV.md`). |
| Recomendación | **Mapillary + detector local (OCR)** = MXN 0 y viable por términos; si el OCR local falla, **Mapillary + Gemini 2.5 Flash-Lite** ≈ **MXN 2.4** por el piloto. Requiere token gratuito de Mapillary y verificar cobertura (§4). |

## 2. Calle transitable y nº de fotos (datos locales)

Método: pyosmium sobre `zmm.osm.pbf` (recorte ZMM del extracto Geofabrik `mexico-260929`, 2026-09-29 20:22 UTC; el recorte no trae timestamp propio en el header, el origen sale del log de la caja) → vías `highway` ∈ {motorway, trunk, primary, secondary, tertiary, unclassified, residential, living_street, service (sin `parking_aisle`/`driveway`/`drive-through`/`emergency_access`, sin acceso private/no) + *_link}, recortadas al polígono de la colonia en `data/colonias.geojson`, longitudes en km (proyección local). Cada vía de OSM cuenta una vez (una calzada doble cuenta dos veces). Verificación cruzada: `data/roads_zmm.geojson` (Overpass 2026-09-25) da 11.4 km para la misma colonia.

Piloto — Fomerrey 112: residential 9.28 · tertiary 1.06 · secondary 0.92 · service 0.13 = **11.39 km**.

Top 10 base v3 (para escalar):

| # | Colonia | km calle | Posiciones 1/20 m | Imágenes ×2 |
|---|---|---:|---:|---:|
| 1 | Ampliación Municipal | 2.85 | 142 | 284 |
| **2** | **Fomerrey 112 (San Bernabé 9)** | **11.39** | **570** | **1,140** |
| 3 | San Miguel Residencial | 31.01* | 1,550 | 3,100 |
| 4 | Croc | 34.38 | 1,719 | 3,438 |
| 5 | Pueblo Nuevo 4to Sector | 9.21 | 460 | 920 |
| 6 | Pueblo Nuevo 1er Sector | 6.05 | 302 | 604 |
| 7 | Fomerrey 24 | 3.79 | 190 | 380 |
| 8 | Gloria Mendiola | 9.70 | 485 | 970 |
| 9 | Floridos Bosques del Nogalar | 5.01 | 250 | 500 |
| 10 | Rincón de Las Mitras (Fomerrey 2) | 6.51 | 326 | 652 |
| | **Total top 10** | **119.9** | **5,995** | **11,990** |

\* incluye 0.91 km de `motorway` (no relevante para anclas; se puede excluir).

Por qué Fomerrey 112 como piloto: tamaño medio (11 km ≈ 1,140 fotos, un día de revisión), top 2 de v3 (si Scout encuentra anclas nuevas, mueve el ranking), 52 abarrotes / 4 tortillerías / 0 Oxxo ya en datos (hay línea base para medir recall/precisión) y sin encuesta de campo previa. Alternativa más barata: Ampliación Municipal (#1, 284 imágenes) pero 0.1 km² es muy poco para validar.

Sensibilidad (piloto): 1 foto/10 m → 1,139 pos. / 2,278 imgs · 1/30 m → 380 pos. / 760 imgs.

## 3. Tarifas vigentes (verificadas 2026-10-02)

**Tipo de cambio**: **MXN 18.37 / USD** (FIX Banxico determinado el 2026-10-01 = 18.3688; fuente: Banxico SIE "Mercado cambiario", vía búsqueda 2026-10-02). Las páginas consultadas muestran otras referencias del mismo día (18.07 «para solventar obligaciones», 18.19 en otra tabla de Banxico); usé la más alta (18.37) para ser conservador. **SUPUESTO**: sin cobertura cambiaria.

### Google Street View Static API / Metadata
Fuente: <https://developers.google.com/maps/billing-and-pricing/pricing> («Last updated 2026-09-28 UTC», leída 2026-10-02) y <https://developers.google.com/maps/documentation/streetview/usage-and-billing> (misma fecha).
- **Static Street View** (Essentials, SKU 9BD0-A2EE-44C3): **10,000 llamadas gratis/mes**; luego **USD 7.00 por 1,000** (hasta 100k), 5.60 (100–500k).
- **Street View Metadata** (SKU 3168-48A9-5C8C): **ilimitado, sin cargo** → sirve para filtrar puntos sin panorama antes de pedir imagen.
- Imagen máx. 640×640 px. La doc dice: *"you must enable billing on each of your projects and include an API key"*. Es decir, **el free cap de 10k no evita tener billing activo** (tarjeta/hold).
- El uso se agrega por cuenta de facturación y por mes.

### Mapillary API
Fuentes: <https://www.mapillary.com/developer/api-documentation/> y <https://www.mapillary.com/terms> (leídas 2026-10-02 con curl; WebFetch dio 400).
- Todas las llamadas a `graph.mapillary.com` y `tiles.mapillary.com` **exigen token** (client token desde el dashboard de desarrolladores). Verificado: una llamada sin token devuelve `Invalid OAuth 2.0 Access Token` (code 190) y tiles 403.
- Límites: 60,000 req/min entidades, 10,000 req/min búsqueda, 50,000 req/día tiles.
- **¿Gratis?** Las páginas de documentación y términos **no publican precio ni cargo** por llamada; la página `/pricing` devuelve "no encontrada". Entonces: *sin cargo documentado*, pero **no pude verificar una declaración oficial explícita de "gratis"**. Tratar como USD 0 con ese asterisco.
- Licencia imágenes: CC BY-SA, con atribución (logo Mapillary + enlace).

### Modelos de visión (por 1M de tokens, USD)
Fuente: <https://ai.google.dev/gemini-api/docs/pricing> («Last updated 2026-10-01 UTC») y <https://docs.x.ai/developers/models> (2026-10-02). OpenAI: la página de precios dio timeout, **no verificado**.

| Modelo | Entrada | Salida | Tokens por imagen 640×640 |
|---|---:|---:|---|
| Gemini 2.5 Flash-Lite (std) | 0.10 | 0.40 | 258 (imagen ≤768 = 1 tile; doc *Count tokens*) |
| Gemini 2.5 Flash-Lite (batch) | 0.05 | 0.20 | 258 |
| Gemini 3.1 Flash-Lite (std) | 0.25 | 1.50 | 1,120 (default Gemini 3; `low`=280; doc *media resolution*) |
| Gemini 3.1 Flash-Lite (batch) | 0.125 | 0.75 | 1,120 |
| grok-4.3 (<200k) | 1.25 | 2.50 | **no documentado** → SUPUESTO 1,500 |

Nota: el tier gratis de Gemini existe pero con "contenido usado para mejorar productos" y límites; **no lo usé** en los números. Detector local: costo en dinero MXN 0 (OCR tipo RapidOCR/PaddleOCR vía onnxruntime —ya instalado en la caja—, + reglas por texto OXXO / MODELORAMA / PURIFICADORA / TORTILLERIA / ABARROTES / AGUA). **No instalado ni probado**; YOLO genérico (COCO) no detecta marcas; detectar logos requeriría entrenar/afinar (ver §5 por qué eso no se puede con Street View de Google).

## 4. Cobertura Mapillary en la colonia

**No verificada.** La API pública requiere token (ver §3); sin key no hay forma de consultar cobertura, y no se usó ninguna key. Siguiente paso (gratis, 1 llamada de bbox con token de Mapillary): contar imágenes y secuencias dentro del bbox de Fomerrey 112 (≈ centro 25.7666, -100.3733), fecha de captura y % de calles con imagen reciente. **SUPUESTO**: cobertura Mapillary en colonias populares de la ZMM es parcial y de antigüedad variable → medir antes de decidir. Nota: `SCOUT_SV.md` registra que el pivot Mapillary se marcó como "rechazado" por Nicolás el 2026-09-21 (motivo no documentado; Mapillary no pide billing) — reconfirmar con él.

## 5. Términos de Google sobre procesar/almacenar Street View

Fuente: Google Maps Platform Terms of Service, <https://cloud.google.com/maps-platform/terms>, §3.2.3 (leído 2026-10-02):
- **3.2.3(a) No Scraping**: prohíbe "pre-fetch, index, store, reshare, or rehost Google Maps Content" y "**bulk download … Street View images**", y "copy and save business names, addresses…".
- **3.2.3(b) No Caching**.
- **3.2.3(c) No Creating Content From Google Maps Content**, con ejemplo explícito: *"construct an index of tree locations within a city from Street View imagery"* (equivalente a construir un índice de negocios) y *"(vii) use Google Maps Content to improve machine learning and artificial intelligence models, including to train, test, validate or fine-tune the models"*.
- 3.2.3(d)(iii): no usar los servicios en un servicio de listados/directorio.
- 3.2.1(c)(ii): no usar los servicios "to avoid incurring Fees" (no trocear cuentas para quedarse en el free cap).

**Restricción clave:** bajar Street View Static en lote (1,140 fotos a 1 cada 20 m) para que un modelo extraiga/indexe negocios **contradice 3.2.3(a) y (c)**; además no se puede entrenar/validar/afinar ningún detector con esas imágenes. Es un uso masivo, automatizado y almacenado — justo lo que ya excluía el criterio human-in-the-loop de `SCOUT_SV.md`. Esto **no es asesoría legal**; procesar "al vuelo sin guardar" tampoco está permitido expresamente y sigue siendo riesgoso. Consecuencias según los Términos: suspensión inmediata por violar 3.2 (§5.2(d)) y responsabilidad sin tope por usar fuera de las restricciones de licencia (§15.2(d)).

Mapillary (<https://www.mapillary.com/terms>, §11–12): uso comercial permitido para "improvement, training, and development of … algorithms, datasets…" y servicio a clientes; obligaciones: atribución (logo + enlace), salvaguardas contra reidentificación/desenfoque de caras y placas, no scrapear fuera de la API, registrar la app, la app debe aportar valor propio. Imágenes CC BY-SA. → **Encaja con el plan**, a diferencia de Google.

## 6. Escenarios — piloto Fomerrey 112 (1,140 imágenes)

Supuestos de cálculo (**SUPUESTO**): 1 foto/20 m, 2 ángulos; 1,140 imágenes todas con panorama (cota superior: Metadata gratis filtra las que no existen); prompt de texto 300 tokens; salida JSON 150 tokens; sin reintentos; FX 18.37 MXN/USD.

| # | Escenario | Imágenes (USD) | Visión (USD) | USD piloto | **MXN piloto** | Viable por términos |
|---|---|---:|---:|---:|---:|---|
| A1 | Google + API visión (Gemini 3.1 Flash-Lite) | 0 (1,140 < 10k gratis) | 0.66 | 0.66 | **12.2** (+ billing activo) | **No** (§5) |
| A2 | Google + API visión (Gemini 2.5 Flash-Lite) | 0 | 0.13 | 0.13 | **2.4** (+ billing activo) | **No** |
| A3 | Google + grok-4.3 (1,500 tok/img SUPUESTO) | 0 | 2.99 | 2.99 | **55.0** (+ billing activo) | **No** |
| B | Google + detector local (OCR) | 0 | 0 | 0 | **0** (+ billing activo) | **No** |
| C | Mapillary + detector local (OCR) | 0* | 0 | 0 | **0** | Sí, con atribución |
| D | Mapillary + Gemini 2.5 Flash-Lite | 0* | 0.13 | 0.13 | **2.4** | Sí |
| E | Mapillary + Gemini 3.1 Flash-Lite | 0* | 0.66 | 0.66 | **12.2** | Sí |
| Ref. | Google **sin** free cap (peor caso, 1,140 × USD 7/1000) | 7.98 | — | 7.98 | **146.6** | No |

\* sin cargo documentado; no verificado explícitamente como "gratis" (§3). Batch API de Gemini reduce 50% la parte de visión (D ≈ MXN 1.2, E ≈ MXN 6.1).

Escala top 10 (11,990 imágenes, **SUPUESTO** mismos parámetros): Google Static = 1,990 sobre el cap → USD 13.93 ≈ **MXN 256** (MXN 1,542 sin cap); visión: 2.5 Flash-Lite MXN 25.5 · 3.1 Flash-Lite MXN 127.8 · grok-4.3 MXN 578. Mapillary + local = MXN 0.

Costos no monetarios (no incluidos): tiempo de Nicolás para aprobar pines (**SUPUESTO**: la tasa de falsos positivos del OCR local es alta con letreros dañados/ocluidos; validar con muestra de 100 imágenes), CPU de la caja (8 núcleos, ~2 GB RAM libres al momento de la revisión: el OCR por lotes debe ser chico), almacenamiento de imágenes (permitido para Mapillary con atribución; no para Google).

## 7. Recomendación

**El más barato viable: C — Mapillary + detector local (OCR): MXN 0.** Si la calidad del OCR no alcanza, **D — Mapillary + Gemini 2.5 Flash-Lite: ≈ MXN 2.4 por la colonia piloto (≈ MXN 25 por el top 10)**. Los escenarios A/B parecen igual de baratos pero **no son viables** por los Términos de Google (§5) y requieren billing que Nicolás ya rechazó.

Plan en pasos (cada uno requiere visto bueno de Nicolás antes de gastar/usar key):
1. Nicolás crea (o autoriza crear) un **client token de Mapillary** (sin tarjeta). Sin token no se puede ni medir cobertura.
2. Medir cobertura Mapillary en Fomerrey 112 (1–2 llamadas, sin costo): imágenes/km y antigüedad. Criterio de paso (**SUPUESTO**): ≥ 60% de la calle con imagen de < 3 años; si no, cambiar de colonia piloto o complementar con campo / userscript humano.
3. Descargar solo las imágenes del piloto (con atribución), correr OCR local + reglas; salida = GeoJSON `layer: "sugerido"` con confianza, miniatura y fuente; **no escribe en `anclas`** ni cambia scores hasta que Nicolás apruebe cada pin.
4. Medir precisión/recall contra los 52 abarrotes + 4 tortillerías ya conocidos en la colonia; solo si hace falta, comparar con D.
5. Mantener el camino humano de `SCOUT_USERSCRIPT.md` para Street View de consumidor (permitido: persona mirando y marcando).

## 8. Riesgos / lagunas

- Cobertura y antigüedad Mapillary: **no verificadas** (falta token).
- "Mapillary gratis": sin cargo documentado, sin declaración explícita encontrada.
- OpenAI: tarifa no verificada (timeout). xAI: tokens por imagen no documentados → SUPUESTO 1,500.
- Google: términos vigentes en la página al 2026-10-02; Google puede cambiarlos (§1.3(b)). Consulta legal propia si se quiere usar Google en volumen.
- El repo ya contiene `data/places_*.geojson` (Places API); no se auditó aquí su cumplimiento con 3.2.3(a)(iii). Fuera de alcance, pero conviene revisarlo.
- Estimaciones de km usan OSM: calles faltantes/privadas se excluyen; ±10%.
