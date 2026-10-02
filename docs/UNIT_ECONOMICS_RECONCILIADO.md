# Unit economics reconciliado: agua $5.53 vs $2.50 por garrafón

**Etiquetas:** [OFICIAL] = tarifa SADM septiembre 2026, PDFs `sadm.gob.mx/PFiles/tarifas` (Cat. 2 = `Documentos/535.pdf`, Cat. 6 = `537.pdf`, descargados y transcritos hoy a `data/sadm_tarifas_sep2026_cat2_cat6.csv`). [NICOLÁS] = cifra de Nicolás (no verificada). [ESTIMADO] = supuesto/estimación. [ABIERTO] = dato que falta. Script: `scripts/unit_economics_reconciliado.py` (reproduce todo, sin red). Escenarios en `data/unit_economics_escenarios.csv`. No reescribe `docs/COSTO_AGUA_SADM.md` (sólo se le añadió una nota que apunta aquí).

## 1. Resumen (por qué hay dos cifras)

Las dos cifras **no miden lo mismo**:

- **$5.53/garrafón** (`COSTO_AGUA_SADM.md`) = escenario **Croc**: 4,149 garr/mes (955/sem, pronóstico del estudio) por **un solo medidor**, ósmosis al **50 %**, tarifa doméstica **Cat. 2** → 158 m³/mes. La tarifa SADM es **por bloques que reprecian todo el consumo**: a 158 m³ el costo efectivo es $145/m³ vs $22/m³ a 21 m³.
- **$2.50/garrafón** [NICOLÁS] = **80 %** de recuperación, pensado por estación de ~30 garr/día (900 garr/mes) [ESTIMADO volumen].
- A volumen de **una estación (900 garr/mes)** y 80 %, la tarifa oficial da **$0.70/garr (Cat. 2)** y **$1.16/garr (Cat. 6 comercial)**: **ambas por debajo de $2.50**. Es decir, $2.50 es **conservador** (cubre agua con margen) a ese volumen — salvo que la estación compre mucho más agua por garrafón (recuperación baja) o la categoría/tarifa sea otra.
- El $5.53 sólo aplica si ~4.6 estaciones de volumen se alimentan de **un mismo medidor** a 50 %. Con un medidor por estación el costo unitario es mucho menor.

## 2. Agua por garrafón = f(recuperación, tarifa) [OFICIAL + cálculo]

Fórmula: m³ comprados = garr/mes × 19 L / 1000 / recuperación; se factura por m³ entero (redondeo arriba, conservador) con la tabla oficial + cargo fijo (Cat. 2: $103.25 si ≥11 m³; Cat. 6: $481.77). Incluye 25 % drenaje + saneamiento (12.5 % Cat. 2 / 25 % Cat. 6) según PDF.

### A) Una estación: 30 garr/día × 30 = 900 garr/mes [ESTIMADO volumen]

| Recuperación | m³ comprados | m³ facturados | Cat. 2 doméstica: $/mes | Cat. 2: $/garr | Cat. 6 comercial: $/mes | Cat. 6: $/garr |
|--:|--:|--:|--:|--:|--:|--:|
| 50 % | 34.2 | 35 | $1,594.16 | **$1.77** | $2,458.04 | **$2.73** |
| 65 % | 26.3 | 27 | $954.93 | **$1.06** | $1,453.23 | **$1.61** |
| 80 % | 21.4 | 22 | $625.62 | **$0.70** | $1,046.72 | **$1.16** |

### B) Escenario Croc: 4,149 garr/mes en un medidor (de `COSTO_AGUA_SADM.md`)

| Recuperación | m³ comprados | m³ facturados | Cat. 2 doméstica: $/mes | Cat. 2: $/garr | Cat. 6 comercial: $/mes | Cat. 6: $/garr |
|--:|--:|--:|--:|--:|--:|--:|
| 50 % | 157.7 | 158 | $22,936.93 | **$5.53** | $27,215.39 | **$6.56** |
| 65 % | 121.3 | 122 | $10,716.88 | **$2.58** | $15,696.35 | **$3.78** |
| 80 % | 98.5 | 99 | $7,848.77 | **$1.89** | $11,598.61 | **$2.80** |

Chequeo: B/50 %/Cat. 2 = 22,936.93 MXN/mes = $5.53/garr → reproduce el $22,936.93 y $5.53 de `COSTO_AGUA_SADM.md` (158 m³).

**¿En qué volumen por medidor el agua queda ≤ $2.50/garr con 80 %?** Cat. 2: hasta ≈5,260 garr/mes (175/día) por medidor; Cat. 6: de ≈230 a ≈3,530 garr/mes (118/día) (por debajo del mínimo el cargo fijo de $481.77 domina; por encima los bloques suben el $/m³). A volumen Croc (B) con 80 %: Cat. 2 $1.89 y Cat. 6 $2.80: el $2.50 de Nicolás queda **entre** ambas tarifas.

**Qué categoría aplica a una purificadora: [NO VERIFICADO].** El doc previo ya dice «no usar Cat. 6 si el recibo es doméstico»; un negocio con medidor propio normalmente se factura comercial (Cat. 6), pero la clasificación la decide SADM (preguntar con la dirección real). Por prudencia el caso Cat. 6 es el realista si hay giro comercial.

## 3. Unit economics por estación (por mes) [ESTIMADO]

Supuestos: 30 garr/día × 30 días = 900; recarga $12; ingreso $10,800/mes; renta $1,000/mes; luz+filtros+sal **ESTIMADO $0.30–$0.85/garr** ($270–$765/mes). **No incluye** precio/amortización del equipo [ABIERTO], mano de obra/operador, impuestos, merma, garrafones/tapas, ni ventas por debajo de 30/día.

Margen = ingreso − renta − agua − luz/filtros/sal. «Rango» = otros costos $0.85 (peor) a $0.30 (mejor).

| Caso | Agua $/garr | Agua $/mes | Margen/mes (peor – mejor) | Estaciones para $21,750/mes (peor – mejor) | ¿3 estaciones alcanzan? |
|---|--:|--:|--:|--:|---|
| **BASE: $2.50 @ 80 % [NICOLÁS]** (plano, sin tarifa) | $2.50 | $2,250 | $6,785 – $7,280 | 3.2 (4) – 3.0 (3) | sólo en el mejor caso |
| Cat. 2 doméstica @ 80 % [OFICIAL+calc] | $0.70 | $626 | $8,409 – $8,904 | 2.6 (3) – 2.4 (3) | sí (peor y mejor) |
| Cat. 6 comercial @ 80 % [OFICIAL+calc] | $1.16 | $1,047 | $7,988 – $8,483 | 2.7 (3) – 2.6 (3) | sí (peor y mejor) |
| Cat. 2 doméstica @ 65 % [OFICIAL+calc] | $1.06 | $955 | $8,080 – $8,575 | 2.7 (3) – 2.5 (3) | sí (peor y mejor) |
| Cat. 6 comercial @ 65 % [OFICIAL+calc] | $1.61 | $1,453 | $7,582 – $8,077 | 2.9 (3) – 2.7 (3) | sí (peor y mejor) |
| Cat. 2 doméstica @ 50 % [OFICIAL+calc] | $1.77 | $1,594 | $7,441 – $7,936 | 2.9 (3) – 2.7 (3) | sí (peor y mejor) |
| Cat. 6 comercial @ 50 % [OFICIAL+calc] | $2.73 | $2,458 | $6,577 – $7,072 | 3.3 (4) – 3.1 (4) | no |
| $5.53 @ 50 % Croc/1 medidor (cifra de `COSTO_AGUA_SADM.md`, **no** aplicable a 1 estación) | $5.53 | $4,977 | $4,058 – $4,553 | 5.4 (6) – 4.8 (5) | no |

- **Caso base de Nicolás ($2.50@80 %)**: margen **$6,785–$7,280/mes** por estación; meta $21,750/mes ⇒ 3.21–2.99 estaciones ⇒ **4 estaciones** en el peor caso de costos, 3 sólo si luz/filtros/sal quedan cerca de $0.30/garr (3×$7,280 = $21,840).
- El reporte de la rutina dice «≈ $6.6–7.1k/mes netos» y «≈3 estaciones»: con estos supuestos obtengo **otro rango** (arriba); la diferencia (~$200) **no se puede explicar** con lo que hay en disco [ABIERTO: pedir a Nicolás el desglose]. Observación (no prueba): el rango del reporte coincide con el caso **Cat. 6 @ 50 %** de la tabla (≈$6.6–7.1k), no con $2.50@80 %. Con ese rango más bajo, 3 estaciones dan $19.8–21.3k < $21.75k ⇒ **4 estaciones**.
- A volumen de estación el agua oficial cuesta menos que $2.50 salvo Cat. 6 con recuperación 50 % ($2.73) (ver §2 A): el efecto de la recuperación en el margen por estación es de ~$1.1–1.6 por garrafón (≈$1,000–1,400/mes, de 80 % a 50 %) frente a ~$7k de margen; **pesan más el volumen (garr/día), la renta y luz/filtros/sal**.
- **Punto débil real:** el volumen. A 20 garr/día el margen cae ~38 %; el modelo asume 30/día sin validar con ventas [ESTIMADO].

### Sensibilidad rápida a garrafones/día (caso base $2.50, otros $0.85–$0.30)

| garr/día | Ingreso/mes | Margen/mes (peor – mejor) | Estaciones meta |
|--:|--:|--:|--:|
| 15 | $5,400 | $2,892 – $3,140 | 8 – 7 |
| 20 | $7,200 | $4,190 – $4,520 | 6 – 5 |
| 25 | $9,000 | $5,488 – $5,900 | 4 – 4 |
| 30 | $10,800 | $6,785 – $7,280 | 4 – 3 |
| 40 | $14,400 | $9,380 – $10,040 | 3 – 3 |

## 4. Pendientes / dudas

- **[ABIERTO] Precio del equipo** (no se inventa): sin él no hay payback ni utilidad neta real; los márgenes de arriba son antes de amortizar el equipo.
- **[ABIERTO] Recuperación real del equipo** (¿80 % es dato del fabricante?): sólo cambia m³ comprados; efecto en $/garr ver §2.
- **[NO VERIFICADO] Categoría SADM** de una purificadora (Cat. 2 vs Cat. 6) y si el rechazo de ósmosis se factura como drenaje en la misma proporción (la tabla ya lo incluye como % del consumo).
- Tarifas: sólo SADM área metropolitana, septiembre 2026; >200 m³ no aplica a estos volúmenes. Cambian cada mes/año.
- Meta $21,750/mes y renta ~$1,000: datos del usuario/reporte, no verificados.
