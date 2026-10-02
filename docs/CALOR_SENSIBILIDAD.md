# Sensibilidad del margen mensual al calor (parámetro, no recalcula v3)

Fecha: **2026-10-02**. Pregunta: cuánto cambia el margen mensual de una estación si la demanda de garrafón sube en los meses con más días de calor. Es un **parámetro de escenario**; no toca `score_base`, `rank_base` ni ningún archivo v3. Etiquetas: VERIFICADO = visto en el archivo o fuente citada; OFICIAL = tarifa SADM; ESTIMADO = supuesto de costos ya usado en `docs/UNIT_ECONOMICS_RECONCILIADO.md`; **SUPUESTO** = valor que no tiene dato propio. Scripts: `scripts/calor_sensibilidad.py` y `scripts/doc_calor_sensibilidad.py` (sin red). Tabla completa: `data/calor_sensibilidad_mensual.csv` (216 filas).

## 1. Modelo

`factor del mes = 1 + k × (días ≥35 °C promedio del mes / días del mes)`, con k ∈ {0, 0.1, 0.2}.

- **Fracción de días ≥35 °C: VERIFICADO.** Sale de `data/clima_mty_dias_calor.csv` (Open-Meteo, reanálisis de una celda, 2021-01 a 2026-09; promedio por mes calendario sobre 6 años, 5 para oct–dic; ver `docs/CALOR_DEMANDA.md` §3). Va de 0.000 (ene, dic) a 0.538 (ago).
- **k: SUPUESTO.** No hay en el repo ni encontré fuente pública con ventas de garrafón en Monterrey contra temperatura (`docs/CALOR_DEMANDA.md` §4). Referencia de orden de magnitud, no calibración: el coeficiente de EE. UU. de ese doc (+0.75 % por día ≥35 °C) daría k ≈ 0.225 con 30 días; k=0.2 es el techo del barrido y k=0.1 la mitad. Con k=0.2, agosto sube 10.7% y enero 0 %.
- **Base: ESTIMADO.** 30 garr/día × 30 días, recarga $12, renta $1,000/mes, luz+filtros+sal $0.30–$0.85 por garrafón, agua $2.50/garr plano (caso BASE de Nicolás) o tarifa SADM Cat. 6 con recuperación 80 % (OFICIAL sep-2026, `data/sadm_tarifas_sep2026_cat2_cat6.csv`). Todos los meses se toman de 30 días para coincidir con los 900 garr/mes del doc de unit economics. Sin precio de equipo, operador ni impuestos.
- **Dos formas de leer los 30 garr/día.** (a) `base_sin_calor`: 30/día es el nivel de un mes sin días calurosos; el calor sólo suma. Es la tabla de abajo. (b) `media_anual_30`: 30/día es el promedio del año; los factores se reescalan para que su media simple sea 1 (ene–dic quedan por debajo de 30 y ago por encima). Está en el CSV y en §3.

## 2. Margen mensual por estación, caso BASE $2.50 plano (modo a)

Rango = peor – mejor costo de luz/filtros/sal. Con k=0 reproduce $6,785 – $7,280 del doc de unit economics (VERIFICADO: mismo cálculo).

| Mes | Días ≥35 °C (prom.) | Fracción | Factor k=0.1 | Factor k=0.2 | Margen k=0 (peor – mejor) | Margen k=0.1 | Margen k=0.2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| ene | 0.0 | 0.000 | 1.000 | 1.000 | $6,785 – $7,280 | $6,785 – $7,280 | $6,785 – $7,280 |
| feb | 0.8 | 0.030 | 1.003 | 1.006 | $6,785 – $7,280 | $6,808 – $7,304 | $6,831 – $7,329 |
| mar | 1.8 | 0.059 | 1.006 | 1.012 | $6,785 – $7,280 | $6,831 – $7,329 | $6,877 – $7,378 |
| abr | 3.7 | 0.122 | 1.012 | 1.024 | $6,785 – $7,280 | $6,880 – $7,381 | $6,975 – $7,482 |
| may | 8.5 | 0.274 | 1.027 | 1.055 | $6,785 – $7,280 | $6,998 – $7,507 | $7,212 – $7,734 |
| jun | 10.5 | 0.350 | 1.035 | 1.070 | $6,785 – $7,280 | $7,057 – $7,570 | $7,330 – $7,860 |
| jul | 11.7 | 0.376 | 1.038 | 1.075 | $6,785 – $7,280 | $7,078 – $7,592 | $7,371 – $7,903 |
| ago | 16.7 | 0.538 | 1.054 | 1.107 | $6,785 – $7,280 | $7,204 – $7,725 | $7,622 – $8,170 |
| sep | 6.0 | 0.200 | 1.020 | 1.040 | $6,785 – $7,280 | $6,941 – $7,446 | $7,096 – $7,611 |
| oct | 0.4 | 0.013 | 1.001 | 1.003 | $6,785 – $7,280 | $6,795 – $7,291 | $6,805 – $7,301 |
| nov | 0.2 | 0.007 | 1.001 | 1.001 | $6,785 – $7,280 | $6,790 – $7,286 | $6,795 – $7,291 |
| dic | 0.0 | 0.000 | 1.000 | 1.000 | $6,785 – $7,280 | $6,785 – $7,280 | $6,785 – $7,280 |
| **Año** | | | | | $81,420 – $87,360 | $82,952 – $88,991 | $84,484 – $90,619 |

Lectura (cálculo sobre estos supuestos): el mes pico (ago) pasa de $6,785–$7,280 a $7,622–$8,170 con k=0.2 (+12.3 % en el peor caso). El año suma $81,420–$87,360 con k=0 y $84,484–$90,619 con k=0.2 (+3.8 % en el peor caso). El calor mueve el margen mucho menos que el volumen base: a 20 garr/día el margen cae ~38 % (`UNIT_ECONOMICS_RECONCILIADO.md` §3). Sigue siendo necesario un mes de ventas reales para fijar k.

### Mismo barrido con agua Cat. 6 @ 80 % (tarifa oficial; la tarifa por bloques sube el costo al subir el volumen)

| Mes | Días ≥35 °C (prom.) | Fracción | Factor k=0.1 | Factor k=0.2 | Margen k=0 (peor – mejor) | Margen k=0.1 | Margen k=0.2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| ene | 0.0 | 0.000 | 1.000 | 1.000 | $7,988 – $8,483 | $7,988 – $8,483 | $7,988 – $8,483 |
| feb | 0.8 | 0.030 | 1.003 | 1.006 | $7,988 – $8,483 | $8,018 – $8,514 | $8,048 – $8,546 |
| mar | 1.8 | 0.059 | 1.006 | 1.012 | $7,988 – $8,483 | $8,048 – $8,546 | $8,107 – $8,608 |
| abr | 3.7 | 0.122 | 1.012 | 1.024 | $7,988 – $8,483 | $8,111 – $8,612 | $8,234 – $8,741 |
| may | 8.5 | 0.274 | 1.027 | 1.055 | $7,988 – $8,483 | $8,263 – $8,772 | $8,451 – $8,973 |
| jun | 10.5 | 0.350 | 1.035 | 1.070 | $7,988 – $8,483 | $8,252 – $8,764 | $8,603 – $9,133 |
| jul | 11.7 | 0.376 | 1.038 | 1.075 | $7,988 – $8,483 | $8,278 – $8,792 | $8,656 – $9,188 |
| ago | 16.7 | 0.538 | 1.054 | 1.107 | $7,988 – $8,483 | $8,440 – $8,962 | $8,939 – $9,487 |
| sep | 6.0 | 0.200 | 1.020 | 1.040 | $7,988 – $8,483 | $8,189 – $8,694 | $8,302 – $8,817 |
| oct | 0.4 | 0.013 | 1.001 | 1.003 | $7,988 – $8,483 | $8,001 – $8,497 | $8,014 – $8,510 |
| nov | 0.2 | 0.007 | 1.001 | 1.001 | $7,988 – $8,483 | $7,995 – $8,490 | $8,002 – $8,497 |
| dic | 0.0 | 0.000 | 1.000 | 1.000 | $7,988 – $8,483 | $7,988 – $8,483 | $7,988 – $8,483 |
| **Año** | | | | | $95,856 – $101,796 | $97,571 – $103,609 | $99,332 – $105,466 |

### Modo b: 30 garr/día como promedio anual (BASE $2.50 plano)

| Mes | Días ≥35 °C (prom.) | Fracción | Factor k=0.1 | Factor k=0.2 | Margen k=0 (peor – mejor) | Margen k=0.1 | Margen k=0.2 |
|---|--:|--:|--:|--:|--:|--:|--:|
| ene | 0.0 | 0.000 | 0.984 | 0.968 | $6,785 – $7,280 | $6,659 – $7,146 | $6,538 – $7,017 |
| feb | 0.8 | 0.030 | 0.987 | 0.974 | $6,785 – $7,280 | $6,682 – $7,170 | $6,582 – $7,064 |
| mar | 1.8 | 0.059 | 0.990 | 0.980 | $6,785 – $7,280 | $6,705 – $7,195 | $6,627 – $7,112 |
| abr | 3.7 | 0.122 | 0.996 | 0.992 | $6,785 – $7,280 | $6,753 – $7,246 | $6,722 – $7,213 |
| may | 8.5 | 0.274 | 1.011 | 1.021 | $6,785 – $7,280 | $6,869 – $7,370 | $6,951 – $7,457 |
| jun | 10.5 | 0.350 | 1.018 | 1.036 | $6,785 – $7,280 | $6,927 – $7,431 | $7,065 – $7,578 |
| jul | 11.7 | 0.376 | 1.021 | 1.041 | $6,785 – $7,280 | $6,948 – $7,453 | $7,105 – $7,620 |
| ago | 16.7 | 0.538 | 1.037 | 1.072 | $6,785 – $7,280 | $7,071 – $7,584 | $7,348 – $7,879 |
| sep | 6.0 | 0.200 | 1.004 | 1.007 | $6,785 – $7,280 | $6,813 – $7,309 | $6,839 – $7,338 |
| oct | 0.4 | 0.013 | 0.985 | 0.971 | $6,785 – $7,280 | $6,669 – $7,157 | $6,557 – $7,038 |
| nov | 0.2 | 0.007 | 0.985 | 0.970 | $6,785 – $7,280 | $6,664 – $7,152 | $6,548 – $7,028 |
| dic | 0.0 | 0.000 | 0.984 | 0.968 | $6,785 – $7,280 | $6,659 – $7,146 | $6,538 – $7,017 |
| **Año** | | | | | $81,420 – $87,360 | $81,419 – $87,359 | $81,420 – $87,361 |

En este modo el año completo queda casi igual que k=0 ($81,420–$87,360) porque sólo redistribuye ventas entre meses: sirve para ver la forma (cuándo falta o sobra caja), no para ganar margen.

## 3. El ranking de colonias no cambia

- **Qué se calculó (solo lectura de `v2/data/colonias_v3.csv`, sin escribir v3):** se reconstruyó `score_base = 100 × (0.40·Demanda* + 0.30·Anclas* + 0.30·(1−Comp*))` desde las columnas del CSV (diferencia máxima con `score_base`: 0.006 puntos, redondeo). Luego se multiplicó Demanda* de todas las colonias por el factor de agosto con k=0.2 (1.1075) y se volvió a normalizar min-max como hace v3 (equivale a escalar la demanda cruda, porque Demanda* es una transformación lineal de ella).
- **Resultado (VERIFICADO en esa corrida):** Demanda* cambia como máximo 3e-17 (ruido de coma flotante), el score 0.0 puntos y **0 colonias de 167 cambian de posición**.
- **Por qué:** Demanda* es min-max sobre las 167 colonias: (f·D − f·Dmín)/(f·Dmáx − f·Dmín) = (D − Dmín)/(Dmáx − Dmín). Un factor que multiplica por igual a todas las colonias se cancela. El calor es casi igual en toda la ZMM (`CALOR_DEMANDA.md`: la celda de reanálisis es una sola), así que el factor es uniforme por construcción.
- **Cuándo sí cambiaría:** si el factor difiere por colonia (más exposición al sol, menos agua de llave, más gente en la calle). No hay dato para eso en el repo; sería otro parámetro SUPUESTO y movería sólo colonias cuya demanda esté a menos de la diferencia entre sus factores (como mucho 10.7% en el pico con k=0.2).
- **Error que evitar:** multiplicar Demanda* **ya normalizada** por el factor, sin volver a normalizar. Eso equivale a subir el peso de 0.40 a 0.443 y no es calor: en la prueba cambian 129 posiciones (Spearman 0.9982) y el top 30 cambia en 1 caso(s). Por eso el factor estacional se aplica sólo a ventas/margen y no entra al score.

## 4. Límites

- k no tiene dato propio. Con ventas diarias de una estación (3 meses) y la Tmax del día, que se baja con `scripts/clima_dias_calor_mty.py`, se estima k y se sustituye.
- Clima = reanálisis de una celda de ~10 km, no estación; octubre–diciembre promedian 5 años.
- El mismo calor sube el consumo de agua de llave y puede bajar la presión (`SADM_AGUA_CONFIABILIDAD.md`); el modelo no lo cuenta.
- Las ventas dependen del volumen por estación; el escenario no incluye canibalización ni competencia.
