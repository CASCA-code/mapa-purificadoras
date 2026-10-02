#!/usr/bin/env python3
"""Unit economics por estacion y costo de agua por garrafon (recuperacion x tarifa SADM). Sin red.
Entradas: data/sadm_tarifas_sep2026_cat2_cat6.csv (tarifas oficiales SADM septiembre 2026, transcritas de los PDF 535/537).
Salidas: docs/UNIT_ECONOMICS_RECONCILIADO.md, data/unit_economics_escenarios.csv"""
import csv, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = {int(r["m3_mes"]): r for r in csv.DictReader(open(f"{ROOT}/data/sadm_tarifas_sep2026_cat2_cat6.csv"))}
L_GARR = 19.0; PRECIO = 12.0; GARR_DIA = 30; DIAS = 30; RENTA = 1000.0; OTROS = (0.30, 0.85); META = 21750.0
NIC_AGUA, NIC_REC = 2.50, 0.80
CROC_GARR_MES = 4149   # docs/COSTO_AGUA_SADM.md (955 garr/sem, pronostico estudio Croc)
def bill(m3_comprados, cat):
    n = math.ceil(m3_comprados - 1e-9)           # se factura por m3 entero; redondeo hacia arriba (conservador)
    assert n <= 200, "fuera de tabla (>200 m3)"
    r = T[n]; return n, float(r[f"{cat}_valor_consumo_mxn"]) + float(r[f"{cat}_cargo_fijo_mxn"])
def agua_garr(garr_mes, rec, cat):
    m3 = garr_mes * L_GARR / 1000 / rec; n, tot = bill(m3, cat); return m3, n, tot, tot / garr_mes
garr_mes = GARR_DIA * DIAS
ing = garr_mes * PRECIO
def margen(agua_mes, otros_garr): return ing - RENTA - agua_mes - otros_garr * garr_mes
rows = []
def add(caso, tarifa, rec, vol, m3, n, tot, per):
    lo = margen(per * vol if vol == garr_mes else tot, OTROS[1]); hi = margen(per * vol if vol == garr_mes else tot, OTROS[0])
    rows.append(dict(caso=caso, tarifa=tarifa, recuperacion=rec, garr_mes=vol, m3_comprados=round(m3, 2), m3_facturados=n, agua_mes_mxn=round(tot, 2), agua_por_garrafon=round(per, 3)))
# --- tabla A: costo de agua por garrafon, dos volumenes
L = []; w = L.append
w("# Unit economics reconciliado: agua $5.53 vs $2.50 por garrafón\n")
w("**Etiquetas:** [OFICIAL] = tarifa SADM septiembre 2026, PDFs `sadm.gob.mx/PFiles/tarifas` (Cat. 2 = `Documentos/535.pdf`, Cat. 6 = `537.pdf`, descargados y transcritos hoy a `data/sadm_tarifas_sep2026_cat2_cat6.csv`). "
  "[NICOLÁS] = cifra de Nicolás (no verificada). [ESTIMADO] = supuesto/estimación. [ABIERTO] = dato que falta. Script: `scripts/unit_economics_reconciliado.py` (reproduce todo, sin red). "
  "Escenarios en `data/unit_economics_escenarios.csv`. No reescribe `docs/COSTO_AGUA_SADM.md` (sólo se le añadió una nota que apunta aquí).\n")
w("## 1. Resumen (por qué hay dos cifras)\n")
w("Las dos cifras **no miden lo mismo**:\n")
w(f"- **$5.53/garrafón** (`COSTO_AGUA_SADM.md`) = escenario **Croc**: {CROC_GARR_MES:,} garr/mes (955/sem, pronóstico del estudio) por **un solo medidor**, ósmosis al **50 %**, tarifa doméstica **Cat. 2** → 158 m³/mes. La tarifa SADM es **por bloques que reprecian todo el consumo**: a 158 m³ el costo efectivo es ${float(T[158]['cat2_valor_consumo_mxn'])/158:.0f}/m³ vs ${float(T[21]['cat2_valor_consumo_mxn'])/21:.0f}/m³ a 21 m³.")
w(f"- **$2.50/garrafón** [NICOLÁS] = **80 %** de recuperación, pensado por estación de ~{GARR_DIA} garr/día ({garr_mes} garr/mes) [ESTIMADO volumen].")
a1 = agua_garr(garr_mes, 0.80, "cat2"); a2 = agua_garr(garr_mes, 0.80, "cat6")
w(f"- A volumen de **una estación ({garr_mes} garr/mes)** y 80 %, la tarifa oficial da **${a1[3]:.2f}/garr (Cat. 2)** y **${a2[3]:.2f}/garr (Cat. 6 comercial)**: **ambas por debajo de $2.50**. Es decir, $2.50 es **conservador** (cubre agua con margen) a ese volumen — salvo que la estación compre mucho más agua por garrafón (recuperación baja) o la categoría/tarifa sea otra.")
w("- El $5.53 sólo aplica si ~4.6 estaciones de volumen se alimentan de **un mismo medidor** a 50 %. Con un medidor por estación el costo unitario es mucho menor.\n")
w("## 2. Agua por garrafón = f(recuperación, tarifa) [OFICIAL + cálculo]\n")
w(f"Fórmula: m³ comprados = garr/mes × {L_GARR:.0f} L / 1000 / recuperación; se factura por m³ entero (redondeo arriba, conservador) con la tabla oficial + cargo fijo (Cat. 2: $103.25 si ≥11 m³; Cat. 6: $481.77). Incluye 25 % drenaje + saneamiento (12.5 % Cat. 2 / 25 % Cat. 6) según PDF.\n")
for vol, nm in [(garr_mes, f"A) Una estación: {GARR_DIA} garr/día × {DIAS} = {garr_mes} garr/mes [ESTIMADO volumen]"), (CROC_GARR_MES, f"B) Escenario Croc: {CROC_GARR_MES:,} garr/mes en un medidor (de `COSTO_AGUA_SADM.md`)")]:
    w(f"### {nm}\n")
    w("| Recuperación | m³ comprados | m³ facturados | Cat. 2 doméstica: $/mes | Cat. 2: $/garr | Cat. 6 comercial: $/mes | Cat. 6: $/garr |\n|--:|--:|--:|--:|--:|--:|--:|")
    for rec in (0.50, 0.65, 0.80):
        m3, n, t2, p2 = agua_garr(vol, rec, "cat2"); _, _, t6, p6 = agua_garr(vol, rec, "cat6")
        w(f"| {int(rec*100)} % | {m3:.1f} | {n} | ${t2:,.2f} | **${p2:.2f}** | ${t6:,.2f} | **${p6:.2f}** |")
        for cat, t, p in (("cat2", t2, p2), ("cat6", t6, p6)):
            rows.append(dict(escenario=("estacion_900" if vol == garr_mes else "croc_4149"), tarifa=cat, recuperacion=rec, garr_mes=vol, m3_comprados=round(m3, 2), m3_facturados=n, agua_mes_mxn=round(t, 2), agua_por_garrafon=round(p, 3)))
    w("")
chk = agua_garr(CROC_GARR_MES, 0.50, "cat2")
w(f"Chequeo: B/50 %/Cat. 2 = {chk[2]:,.2f} MXN/mes = ${chk[3]:.2f}/garr → reproduce el $22,936.93 y $5.53 de `COSTO_AGUA_SADM.md` (158 m³).\n")
# rango de volumen mensual por medidor en que el costo unitario queda <= $2.50 (recuperacion 80 %)
def ok_range(rec, cat):
    good = []
    for g in range(50, 20000, 10):
        try:
            if agua_garr(g, rec, cat)[3] <= NIC_AGUA: good.append(g)
        except AssertionError: break
    return (min(good), max(good)) if good else (None, None)
r2 = ok_range(NIC_REC, "cat2"); r6 = ok_range(NIC_REC, "cat6")
w(f"**¿En qué volumen por medidor el agua queda ≤ $2.50/garr con 80 %?** Cat. 2: hasta ≈{r2[1]:,} garr/mes ({r2[1]/DIAS:.0f}/día) por medidor; Cat. 6: de ≈{r6[0]:,} a ≈{r6[1]:,} garr/mes ({r6[1]/DIAS:.0f}/día) (por debajo del mínimo el cargo fijo de $481.77 domina; por encima los bloques suben el $/m³). A volumen Croc (B) con 80 %: Cat. 2 ${agua_garr(CROC_GARR_MES, .8, 'cat2')[3]:.2f} y Cat. 6 ${agua_garr(CROC_GARR_MES, .8, 'cat6')[3]:.2f}: el $2.50 de Nicolás queda **entre** ambas tarifas.\n")
w("**Qué categoría aplica a una purificadora: [NO VERIFICADO].** El doc previo ya dice «no usar Cat. 6 si el recibo es doméstico»; un negocio con medidor propio normalmente se factura comercial (Cat. 6), pero la clasificación la decide SADM (preguntar con la dirección real). Por prudencia el caso Cat. 6 es el realista si hay giro comercial.\n")
w("## 3. Unit economics por estación (por mes) [ESTIMADO]\n")
w(f"Supuestos: {GARR_DIA} garr/día × {DIAS} días = {garr_mes}; recarga ${PRECIO:.0f}; ingreso ${ing:,.0f}/mes; renta ${RENTA:,.0f}/mes; luz+filtros+sal **ESTIMADO ${OTROS[0]:.2f}–${OTROS[1]:.2f}/garr** (${OTROS[0]*garr_mes:,.0f}–${OTROS[1]*garr_mes:,.0f}/mes). "
  f"**No incluye** precio/amortización del equipo [ABIERTO], mano de obra/operador, impuestos, merma, garrafones/tapas, ni ventas por debajo de 30/día.\n")
w("Margen = ingreso − renta − agua − luz/filtros/sal. «Rango» = otros costos $0.85 (peor) a $0.30 (mejor).\n")
w(f"| Caso | Agua $/garr | Agua $/mes | Margen/mes (peor – mejor) | Estaciones para ${META:,.0f}/mes (peor – mejor) | ¿3 estaciones alcanzan? |\n|---|--:|--:|--:|--:|---|")
def line(nm, per, tot):
    lo = ing - RENTA - tot - OTROS[1] * garr_mes; hi = ing - RENTA - tot - OTROS[0] * garr_mes
    n_lo, n_hi = META / lo, META / hi
    ok = "sí (peor y mejor)" if 3 * lo >= META else ("sólo en el mejor caso" if 3 * hi >= META else "no")
    w(f"| {nm} | ${per:.2f} | ${tot:,.0f} | ${lo:,.0f} – ${hi:,.0f} | {n_lo:.1f} ({math.ceil(n_lo - 1e-9)}) – {n_hi:.1f} ({math.ceil(n_hi - 1e-9)}) | {ok} |")
    rows.append(dict(escenario="margen_estacion", tarifa=nm, agua_por_garrafon=round(per, 3), agua_mes_mxn=round(tot, 2), garr_mes=garr_mes, margen_mes_peor=round(lo), margen_mes_mejor=round(hi), estaciones_meta_peor=math.ceil(n_lo - 1e-9), estaciones_meta_mejor=math.ceil(n_hi - 1e-9)))
line("**BASE: $2.50 @ 80 % [NICOLÁS]** (plano, sin tarifa)", NIC_AGUA, NIC_AGUA * garr_mes)
for rec in (0.80, 0.65, 0.50):
    for cat, nm in (("cat2", "Cat. 2 doméstica"), ("cat6", "Cat. 6 comercial")):
        m3, n, t, p = agua_garr(garr_mes, rec, cat); line(f"{nm} @ {int(rec*100)} % [OFICIAL+calc]", p, t)
line(f"$5.53 @ 50 % Croc/1 medidor (cifra de `COSTO_AGUA_SADM.md`, **no** aplicable a 1 estación)", 5.53, 5.53 * garr_mes)
w("")
base_lo = ing - RENTA - NIC_AGUA * garr_mes - OTROS[1] * garr_mes; base_hi = ing - RENTA - NIC_AGUA * garr_mes - OTROS[0] * garr_mes
w(f"- **Caso base de Nicolás ($2.50@80 %)**: margen **${base_lo:,.0f}–${base_hi:,.0f}/mes** por estación; meta ${META:,.0f}/mes ⇒ {META/base_lo:.2f}–{META/base_hi:.2f} estaciones ⇒ **{math.ceil(META/base_lo-1e-9)} estaciones** en el peor caso de costos, 3 sólo si luz/filtros/sal quedan cerca de $0.30/garr (3×${base_hi:,.0f} = ${3*base_hi:,.0f}).")
w("- El reporte de la rutina dice «≈ $6.6–7.1k/mes netos» y «≈3 estaciones»: con estos supuestos obtengo **otro rango** (arriba); la diferencia (~$200) **no se puede explicar** con lo que hay en disco [ABIERTO: pedir a Nicolás el desglose]. Observación (no prueba): el rango del reporte coincide con el caso **Cat. 6 @ 50 %** de la tabla (≈$6.6–7.1k), no con $2.50@80 %. Con ese rango más bajo, 3 estaciones dan $19.8–21.3k < $21.75k ⇒ **4 estaciones**.")
w("- A volumen de estación el agua oficial cuesta menos que $2.50 salvo Cat. 6 con recuperación 50 % ($2.73) (ver §2 A): el efecto de la recuperación en el margen por estación es de ~$1.1–1.6 por garrafón (≈$1,000–1,400/mes, de 80 % a 50 %) frente a ~$7k de margen; **pesan más el volumen (garr/día), la renta y luz/filtros/sal**.")
w("- **Punto débil real:** el volumen. A 20 garr/día el margen cae ~38 %; el modelo asume 30/día sin validar con ventas [ESTIMADO].\n")
w("### Sensibilidad rápida a garrafones/día (caso base $2.50, otros $0.85–$0.30)\n")
w("| garr/día | Ingreso/mes | Margen/mes (peor – mejor) | Estaciones meta |\n|--:|--:|--:|--:|")
for gd in (15, 20, 25, 30, 40):
    g = gd * DIAS; i = g * PRECIO
    lo = i - RENTA - NIC_AGUA * g - OTROS[1] * g; hi = i - RENTA - NIC_AGUA * g - OTROS[0] * g
    w(f"| {gd} | ${i:,.0f} | ${lo:,.0f} – ${hi:,.0f} | {math.ceil(META/lo-1e-9)} – {math.ceil(META/hi-1e-9)} |")
w("\n## 4. Pendientes / dudas\n")
w("- **[ABIERTO] Precio del equipo** (no se inventa): sin él no hay payback ni utilidad neta real; los márgenes de arriba son antes de amortizar el equipo.")
w("- **[ABIERTO] Recuperación real del equipo** (¿80 % es dato del fabricante?): sólo cambia m³ comprados; efecto en $/garr ver §2.")
w("- **[NO VERIFICADO] Categoría SADM** de una purificadora (Cat. 2 vs Cat. 6) y si el rechazo de ósmosis se factura como drenaje en la misma proporción (la tabla ya lo incluye como % del consumo).")
w("- Tarifas: sólo SADM área metropolitana, septiembre 2026; >200 m³ no aplica a estos volúmenes. Cambian cada mes/año.")
w("- Meta $21,750/mes y renta ~$1,000: datos del usuario/reporte, no verificados.")
open(f"{ROOT}/docs/UNIT_ECONOMICS_RECONCILIADO.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
keys = ["escenario", "tarifa", "recuperacion", "garr_mes", "m3_comprados", "m3_facturados", "agua_mes_mxn", "agua_por_garrafon", "margen_mes_peor", "margen_mes_mejor", "estaciones_meta_peor", "estaciones_meta_mejor"]
with open(f"{ROOT}/data/unit_economics_escenarios.csv", "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); wr.writeheader(); wr.writerows([r for r in rows if "escenario" in r])
