#!/usr/bin/env python3
"""Genera docs/CALOR_SENSIBILIDAD.md desde data/calor_sensibilidad_mensual.csv y /workspace/downloads/calor_sens_stats.json (correr antes scripts/calor_sensibilidad.py)."""
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(f"{ROOT}/data/calor_sensibilidad_mensual.csv"); st = json.load(open("/workspace/downloads/calor_sens_stats.json"))
MES = "ene feb mar abr may jun jul ago sep oct nov dic".split()
fm = lambda v: f"${v:,.0f}"
def tabla(caso, norm):
    s = d[(d.caso_agua == caso) & (d.normalizacion == norm)]; L = []
    L.append("| Mes | Días ≥35 °C (prom.) | Fracción | Factor k=0.1 | Factor k=0.2 | Margen k=0 (peor – mejor) | Margen k=0.1 | Margen k=0.2 |"); L.append("|---|--:|--:|--:|--:|--:|--:|--:|")
    for mes in range(1, 13):
        r = {k: s[(s.k == k) & (s.mes == mes)].iloc[0] for k in (0.0, 0.1, 0.2)}
        cel = lambda k: f"{fm(r[k].margen_peor_mxn)} – {fm(r[k].margen_mejor_mxn)}"
        L.append(f"| {MES[mes-1]} | {r[0.1].d35_media:.1f} | {r[0.1].frac_dias_ge35:.3f} | {r[0.1].factor:.3f} | {r[0.2].factor:.3f} | {cel(0.0)} | {cel(0.1)} | {cel(0.2)} |")
    tot = {k: (s[s.k == k].margen_peor_mxn.sum(), s[s.k == k].margen_mejor_mxn.sum()) for k in (0.0, 0.1, 0.2)}
    L.append(f"| **Año** | | | | | {fm(tot[0.0][0])} – {fm(tot[0.0][1])} | {fm(tot[0.1][0])} – {fm(tot[0.1][1])} | {fm(tot[0.2][0])} – {fm(tot[0.2][1])} |")
    return "\n".join(L), tot
tb, tt = tabla("BASE $2.50 plano", "base_sin_calor")
t6, t6t = tabla("Cat. 6 @ 80 %", "base_sin_calor")
tn, tnt = tabla("BASE $2.50 plano", "media_anual_30")
def rango(caso, norm="base_sin_calor"):
    s = d[(d.caso_agua == caso) & (d.normalizacion == norm)]; o = {}
    for k in (0.1, 0.2): 
        x = s[s.k == k]; o[k] = (x.margen_peor_mxn.min(), x.margen_peor_mxn.max(), x.margen_mejor_mxn.min(), x.margen_mejor_mxn.max())
    return o
ago = d[(d.caso_agua == "BASE $2.50 plano") & (d.normalizacion == "base_sin_calor") & (d.mes == 8)].set_index("k")
r0, r02 = ago.loc[0.0], ago.loc[0.2]
s_ago = st["k0.2_ago"]; s_sn = st["sin_renormalizar_ago_k02"]
y0, y2 = tt[0.0], tt[0.2]
gan = (y2[0] / y0[0] - 1) * 100
md = f"""# Sensibilidad del margen mensual al calor (parámetro, no recalcula v3)

Fecha: **2026-10-02**. Pregunta: cuánto cambia el margen mensual de una estación si la demanda de garrafón sube en los meses con más días de calor. Es un **parámetro de escenario**; no toca `score_base`, `rank_base` ni ningún archivo v3. Etiquetas: VERIFICADO = visto en el archivo o fuente citada; OFICIAL = tarifa SADM; ESTIMADO = supuesto de costos ya usado en `docs/UNIT_ECONOMICS_RECONCILIADO.md`; **SUPUESTO** = valor que no tiene dato propio. Scripts: `scripts/calor_sensibilidad.py` y `scripts/doc_calor_sensibilidad.py` (sin red). Tabla completa: `data/calor_sensibilidad_mensual.csv` ({len(d)} filas).

## 1. Modelo

`factor del mes = 1 + k × (días ≥35 °C promedio del mes / días del mes)`, con k ∈ {{0, 0.1, 0.2}}.

- **Fracción de días ≥35 °C: VERIFICADO.** Sale de `data/clima_mty_dias_calor.csv` (Open-Meteo, reanálisis de una celda, 2021-01 a 2026-09; promedio por mes calendario sobre 6 años, 5 para oct–dic; ver `docs/CALOR_DEMANDA.md` §3). Va de 0.000 (ene, dic) a {max(r['frac35'] for r in st['meses']):.3f} (ago).
- **k: SUPUESTO.** No hay en el repo ni encontré fuente pública con ventas de garrafón en Monterrey contra temperatura (`docs/CALOR_DEMANDA.md` §4). Referencia de orden de magnitud, no calibración: el coeficiente de EE. UU. de ese doc (+0.75 % por día ≥35 °C) daría k ≈ 0.225 con 30 días; k=0.2 es el techo del barrido y k=0.1 la mitad. Con k=0.2, agosto sube {r02.factor-1:.1%} y enero 0 %.
- **Base: ESTIMADO.** 30 garr/día × 30 días, recarga $12, renta $1,000/mes, luz+filtros+sal $0.30–$0.85 por garrafón, agua $2.50/garr plano (caso BASE de Nicolás) o tarifa SADM Cat. 6 con recuperación 80 % (OFICIAL sep-2026, `data/sadm_tarifas_sep2026_cat2_cat6.csv`). Todos los meses se toman de 30 días para coincidir con los 900 garr/mes del doc de unit economics. Sin precio de equipo, operador ni impuestos.
- **Dos formas de leer los 30 garr/día.** (a) `base_sin_calor`: 30/día es el nivel de un mes sin días calurosos; el calor sólo suma. Es la tabla de abajo. (b) `media_anual_30`: 30/día es el promedio del año; los factores se reescalan para que su media simple sea 1 (ene–dic quedan por debajo de 30 y ago por encima). Está en el CSV y en §3.

## 2. Margen mensual por estación, caso BASE $2.50 plano (modo a)

Rango = peor – mejor costo de luz/filtros/sal. Con k=0 reproduce $6,785 – $7,280 del doc de unit economics (VERIFICADO: mismo cálculo).

{tb}

Lectura (cálculo sobre estos supuestos): el mes pico (ago) pasa de ${r0.margen_peor_mxn:,.0f}–${r0.margen_mejor_mxn:,.0f} a ${r02.margen_peor_mxn:,.0f}–${r02.margen_mejor_mxn:,.0f} con k=0.2 (+{(r02.margen_peor_mxn/r0.margen_peor_mxn-1)*100:.1f} % en el peor caso). El año suma ${y0[0]:,.0f}–${y0[1]:,.0f} con k=0 y ${y2[0]:,.0f}–${y2[1]:,.0f} con k=0.2 (+{gan:.1f} % en el peor caso). El calor mueve el margen mucho menos que el volumen base: a 20 garr/día el margen cae ~38 % (`UNIT_ECONOMICS_RECONCILIADO.md` §3). Sigue siendo necesario un mes de ventas reales para fijar k.

### Mismo barrido con agua Cat. 6 @ 80 % (tarifa oficial; la tarifa por bloques sube el costo al subir el volumen)

{t6}

### Modo b: 30 garr/día como promedio anual (BASE $2.50 plano)

{tn}

En este modo el año completo queda casi igual que k=0 (${tnt[0.0][0]:,.0f}–${tnt[0.0][1]:,.0f}) porque sólo redistribuye ventas entre meses: sirve para ver la forma (cuándo falta o sobra caja), no para ganar margen.

## 3. El ranking de colonias no cambia

- **Qué se calculó (solo lectura de `v2/data/colonias_v3.csv`, sin escribir v3):** se reconstruyó `score_base = 100 × (0.40·Demanda* + 0.30·Anclas* + 0.30·(1−Comp*))` desde las columnas del CSV (diferencia máxima con `score_base`: {st['chk_score_base_maxdiff']:.3f} puntos, redondeo). Luego se multiplicó Demanda* de todas las colonias por el factor de agosto con k=0.2 ({s_ago['f']:.4f}) y se volvió a normalizar min-max como hace v3 (equivale a escalar la demanda cruda, porque Demanda* es una transformación lineal de ella).
- **Resultado (VERIFICADO en esa corrida):** Demanda* cambia como máximo {s_ago['D_maxdiff']:.0e} (ruido de coma flotante), el score {s_ago['score_maxdiff']:.1f} puntos y **{s_ago['rank_changes']} colonias de 167 cambian de posición**.
- **Por qué:** Demanda* es min-max sobre las 167 colonias: (f·D − f·Dmín)/(f·Dmáx − f·Dmín) = (D − Dmín)/(Dmáx − Dmín). Un factor que multiplica por igual a todas las colonias se cancela. El calor es casi igual en toda la ZMM (`CALOR_DEMANDA.md`: la celda de reanálisis es una sola), así que el factor es uniforme por construcción.
- **Cuándo sí cambiaría:** si el factor difiere por colonia (más exposición al sol, menos agua de llave, más gente en la calle). No hay dato para eso en el repo; sería otro parámetro SUPUESTO y movería sólo colonias cuya demanda esté a menos de la diferencia entre sus factores (como mucho {r02.factor-1:.1%} en el pico con k=0.2).
- **Error que evitar:** multiplicar Demanda* **ya normalizada** por el factor, sin volver a normalizar. Eso equivale a subir el peso de 0.40 a {0.40*s_ago['f']:.3f} y no es calor: en la prueba cambian {s_sn['rank_changes']} posiciones (Spearman {s_sn['spearman']:.4f}) y el top 30 cambia en {s_sn['top30_cambia']} caso(s). Por eso el factor estacional se aplica sólo a ventas/margen y no entra al score.

## 4. Límites

- k no tiene dato propio. Con ventas diarias de una estación (3 meses) y la Tmax del día, que se baja con `scripts/clima_dias_calor_mty.py`, se estima k y se sustituye.
- Clima = reanálisis de una celda de ~10 km, no estación; octubre–diciembre promedian 5 años.
- El mismo calor sube el consumo de agua de llave y puede bajar la presión (`SADM_AGUA_CONFIABILIDAD.md`); el modelo no lo cuenta.
- Las ventas dependen del volumen por estación; el escenario no incluye canibalización ni competencia.
"""
open(f"{ROOT}/docs/CALOR_SENSIBILIDAD.md", "w").write(md); print(len(md))
