# B4: topografía (pendiente a pie)

**Motivo:** Nicolás: «nadie va a subir con algo tan pesado» (un garrafón pesa ~19 L ≈ 19 kg). Se marca dónde el terreno es cuesta arriba. **No cambia `score_base` ni `rank_base`**: es una etiqueta y un ajuste aparte.

## Fuente
- **Copernicus GLO-30 DSM** (ESA, acceso libre y gratuito), ~30 m. Ya estaba en disco: `/home/box/geo/base_mty/raw/dem/Copernicus_DSM_COG_10_N25_00_W101_00_DEM.tif` y `..._W100_00_DEM.tif` (descargados el 2026-10-01). No se descargó nada nuevo.
- Es un **modelo de superficie** (incluye techos y árboles), no de terreno desnudo: se suaviza (gaussiana σ = 1 pixel) para quitar ruido. A 30 m no ve escalones, banquetas ni rampas: la pendiente es un promedio del entorno, no de la calle exacta.
- Cálculo: `scripts/build_b4_topografia.py` (offline, corre después de `build_b4.py`). Fecha del cálculo: 2026-10-02.

## Qué se calcula
| Dato | Cómo | Dónde se ve |
|---|---|---|
| Pendiente a pie (300 m) | media de la pendiente (%) en un disco de 300 m (el mismo radio caminable de B4) | estaciones sugeridas, puntos de «Dónde poner» |
| Desnivel 300 m | máximo − mínimo de elevación en ese disco | «Detalle» de cada punto |
| Pendiente de la colonia | media y p90 de los pixeles dentro del polígono | ficha de colonia («Detalle del puntaje»), etiqueta en el ranking |

## Umbrales (SUPUESTO, sin calibrar con datos de ventas ni de campo)
| Pendiente | Etiqueta | Ajuste del puntaje de celda («Dónde poner») |
|---|---|---|
| hasta 8 % | Plana (sin etiqueta) | × 1.0 |
| más de 8 % hasta 12 % | Cuesta arriba | × 0.8 |
| más de 12 % | Muy empinada | × 0.6 |

Los umbrales vienen del rango 8–10 % que se pidió como punto de partida; los factores 0.8 y 0.6 son juicio mío, no medidos. El puntaje ajustado se muestra en el «Detalle» del punto y **no reordena** la lista.

## Resultados con los datos actuales
- Colonias (pendiente media del polígono): 130 planas, 9 cuesta arriba, 28 muy empinadas. Las más empinadas: Pedregal del Topo Chico, Bosques de La Estanzuela, Unidad del Pueblo, La Campana (pie de cerro; el polígono incluye ladera).
- Estaciones sugeridas (236): 192 con pendiente ≤ 8 %, 21 entre 8 y 12 %, 23 por encima de 12 %.
- Puntos de «Dónde poner» (68): 61 planos, 4 cuesta arriba, 3 muy empinados.
- Economía: se muestran las colonias del top del ranking que hacen falta para sumar 3 estaciones (cubren la meta de $21,750/mes) y 4 (plan de capital), contando todas las estaciones sugeridas y contando sólo las de pendiente ≤ 8 %. Resultado: 3 estaciones = 2 colonias (con o sin ajuste); 4 estaciones = 3 colonias sin ajuste y 2 colonias evitando cuestas (la #1 del ranking tiene su estación en cuesta). Detalle en la pestaña Economía.

## Límites
- La pendiente media en 300 m puede ocultar una calle empinada concreta y viceversa. Verificar en campo antes de comprar.
- No se calcula el sentido: no se sabe si los clientes vienen de arriba o de abajo de la estación. Cuesta arriba para el cliente depende de dónde vive.
- La penalización por pendiente no entra al rating, a la banda de confianza ni a la economía por estación (los $ por estación siguen igual).
