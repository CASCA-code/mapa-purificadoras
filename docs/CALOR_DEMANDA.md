# Calor (Monterrey) como proxy estacional de demanda de garrafón

Fecha: **2026-10-02**. VERIFICADO = visto en la fuente citada; SUPUESTO = inferencia mía. **Uso:** factor estacional para *unit economics* (ventas/mes de una estación). **NO** para ranking de colonias: el calor es casi igual en toda la ZMM y no discrimina entre colonias. No altera ningún score. Script: `scripts/clima_dias_calor_mty.py` (1 petición pública sin llave) + `scripts/doc_calor_demanda.py`. Datos: `data/clima_mty_dias_calor.csv` (69 meses, 2021-01 a 2026-09).

## 1. Datos de temperatura

- Fuente: Open-Meteo Historical Weather API (`https://archive-api.open-meteo.com/v1/archive?latitude=25.67&longitude=-100.31&start_date=2021-01-01&end_date=2026-09-30&daily=temperature_2m_max,temperature_2m_min&timezone=America/Mexico_City`), sin llave. Respuesta guardada en `/workspace/downloads/om_raw.json` (fuera del repo): 2,099 días, 0 faltantes, último día 2026-09-30.
- **Ojo (VERIFICADO en la respuesta):** la API devolvió la celda de reanálisis en lat 25.694, lon −100.283, elevación 531 m — no es una estación meteorológica. Son temperaturas modeladas (celda ~10 km), pueden diferir de lo que marca una estación o la prensa. Ejemplo: la prensa dice «hasta 40 °C» el 2026-07-22 (ABC Noticias); en esta serie julio-2026 tuvo máx. 39.1 °C y 0 días ≥40 °C.
- Umbrales: Tmax diaria ≥35 °C y ≥40 °C (cuenta de días por mes). Octubre 2026 no está (el mes no termina). Octubre-diciembre promedian sobre 5 años, los demás meses sobre 6.

## 2. Días de calor por año

| Año | Días con dato | Días ≥35 °C | Días ≥40 °C | Tmax máx. (°C) |
|--:|--:|--:|--:|--:|
| 2021 | 365 | 42 | 0 | 39.8 |
| 2022 | 365 | 74 | 3 | 41.1 |
| 2023 | 365 | 95 | 12 | 42.6 |
| 2024 | 366 | 36 | 5 | 44.4 |
| 2025 | 365 | 66 | 4 | 43.1 |
| 2026 (a sep.) | 273 | 48 | 1 | 40.1 |

## 3. Climatología mensual (promedio de días por mes)

| Mes | Años | Días ≥35 °C (prom.) | Mín–máx | Días ≥40 °C (prom.) | Tmax media (°C) |
|---|--:|--:|---|--:|--:|
| ene | 6 | 0.0 | 0–0 | 0.0 | 19.7 |
| feb | 6 | 0.8 | 0–3 | 0.0 | 23.7 |
| mar | 6 | 1.8 | 0–5 | 0.0 | 28.0 |
| abr | 6 | 3.7 | 0–8 | 0.2 | 29.8 |
| may | 6 | 8.5 | 2–18 | 1.3 | 32.3 |
| jun | 6 | 10.5 | 3–19 | 1.8 | 33.8 |
| jul | 6 | 11.7 | 0–28 | 0.2 | 33.6 |
| ago | 6 | 16.7 | 4–25 | 0.7 | 34.9 |
| sep | 6 | 6.0 | 0–18 | 0.0 | 31.7 |
| oct | 5 | 0.4 | 0–1 | 0.0 | 27.4 |
| nov | 5 | 0.2 | 0–1 | 0.0 | 23.4 |
| dic | 5 | 0.0 | 0–0 | 0.0 | 22.0 |

Agosto es el mes más caluroso en días ≥35 °C (16.7 de 31 en promedio); mayo–septiembre concentran casi todos los días ≥35 °C, y los ≥40 °C son raros (≤7 por mes; sobre todo may–jun; máx. 7 en jun-2023). Diciembre–febrero ≈ 0 días ≥35 °C. Variación entre años grande: p. ej. julio 0 (2021, 2024) a 28 días (2023).

## 4. ¿Hay fuente pública que ligue calor con demanda de agua embotellada? (verificación)

| # | Fuente | Qué dice (VERIFICADO leyendo la fuente) | Límite |
|--:|---|---|---|
| 1 | de Preux & Roche (2024, preprint **sin revisión por pares**, SSRN 4862789), PDF alojado en NielsenIQ: https://nielseniq.com/global/en/wp-content/uploads/sites/4/2024/09/How-Is-Climate-Fuelling-the-Thirst-for-Sweetness.pdf | Con panel de consumo de hogares de EE. UU., un día con Tmax **>95 °F (≈35 °C)** aumenta **+0.75 %** el volumen mensual comprado de agua embotellada vs. un día de 65–70 °F; el efecto de >90 °F no se compensa después | EE. UU.; agua embotellada de retail (no garrafón a domicilio/recarga); +0.75 % es **por cada día** extremo dentro del mes |
| 2 | Zapata (2021), *Ecological Economics* 187, Ecuador: https://ideas.repec.org/a/eee/ecolec/v187y2021ics0921800921001488.html | Con encuestas de hogares: +1 °C de temperatura media ≈ casi **+1/5 de botella** consumida; mayor efecto en zonas rurales y ocupaciones expuestas | Ecuador, botellas por hogar; no es MX ni garrafón |
| 3 | Milenio, 2026-05-13, La Laguna (Torreón): https://www.milenio.com/estados/laguna-altas-temperaturas-disparan-venta-agua-embotellada | Repartidores/comerciantes dicen **+50 % o más** en venta de agua embotellada y garrafones con el calor; rutas de >350 garrafones/día vs ~150 en temporada normal; familias piden más cuando falla el suministro o hay apagones | Anecdótico (entrevistas), no es Monterrey. Nota: 350 vs 150 es +133 %, no «+50 %»: la nota no concilia sus propias cifras |
| 4 | ScienceDirect S092552731730244X (efecto de olas de calor/frío en bebidas, EE. UU.): https://www.sciencedirect.com/science/article/abs/pii/S092552731730244X | **NO verificado a texto completo** (la página devolvió bloqueo Cloudflare tanto por WebFetch como curl); sólo vi el resumen vía buscador: «heat waves increase the demand by 2.1% per degree»; agua embotellada entre las más sensibles | Sólo fragmento de buscador → trátese como SUPUESTO hasta leer el artículo |
| 5 | ABC Noticias, 2026-07-22, Monterrey: https://abcnoticias.mx/local/2026/7/22/ola-de-calor-dispara-hasta-40-venta-de-bebidas-nieves-en-monterrey-288231.html | Un comerciante del Centro reporta +30–40 % en ventas de **aguas frescas, paletas y nieves** en los últimos 3 días de calor | No es garrafón ni agua embotellada; un solo comercio |
| 6 | Quadratín NL, 2026-07-30: https://nuevoleon.quadratin.com.mx/sucesos/el-calor-no-dispara-la-venta-de-aguas-en-el-centro-de-monterrey/ | Vendedores ambulantes del Centro **no** vieron aumento: la gente lleva su propio termo/botella | Contraejemplo anecdótico; también no es garrafón |

- **Conclusión VERIFICADA:** hay evidencia pública *externa* (EE. UU., Ecuador, prensa de Torreón) de que el calor sube el consumo de agua embotellada; **no encontré** ninguna fuente pública con datos de ventas de **garrafón/recarga en Monterrey** ligadas a temperatura. Para Monterrey la relación es **SUPUESTO** (plausible, magnitud desconocida).
- **SUPUESTO ilustrativo (no usar como cifra de negocio):** si el coeficiente de EE. UU. (+0.75 % por día ≥35 °C en el mes) fuera transferible, agosto (16.7 días ≥35 °C) daría ≈ +12.5 % vs. un mes sin esos días, y enero ≈ 0 %. La transferibilidad (agua de retail → recarga de garrafón; EE. UU. → ZMM; hogares con agua de llave poco confiable) **no está demostrada**.

## 5. Cómo usarlo en unit economics (propuesta, no aplicada)

- `data/unit_economics_escenarios.csv` usa `garr_mes` fijo (p. ej. 900). Propuesta: añadir un escenario con **factor estacional por mes** = parámetro de entrada, con 3 valores de juicio (bajo/medio/alto) alrededor del perfil de días ≥35 °C de §3, y **reemplazarlo por datos propios** apenas la primera estación tenga 2–3 meses de ventas (conteo diario de garrafones vs. Tmax del día, que se puede bajar con el mismo script).
- Lo robusto de este análisis es la **forma estacional** (may–sep calientes; dic–feb sin días ≥35 °C), no la magnitud. Que los meses calientes coincidan con más ventas es lo esperable pero no está medido para esta zona.
- Riesgo operativo ligado (ya documentado en `docs/SADM_AGUA_CONFIABILIDAD.md`): el mismo calor sube el consumo de agua de llave y las caídas de presión/bombeo (ver notas de julio 2026 allí), que pueden afectar la toma de agua de la estación justo en pico.

## 6. Límites
- Una celda de reanálisis, 5.75 años: 2021–2026 incluye el calor extremo de 2023 (95 días ≥35 °C) y años más suaves; no es una climatología de 30 años.
- Tmax diaria no mide sensación térmica ni humedad ni noches calientes (Tmin media 21–24 °C en jun–sep está en el CSV).
- No se usó ninguna API con llave; 1 sola petición a Open-Meteo.
