# B4 · Economía con máquina real ($87,000): payback, 3–4 estaciones, SADM

**Etiquetas:** **[DATO]** = cifra dada o verificada. **[SUPUESTO]** = decisión/estimación mía o del doc de origen, no medida. **[ABIERTO]** = falta el dato. Todo es **BORRADOR B4**; no sustituye `UNIT_ECONOMICS_RECONCILIADO.md` ni `COSTO_AGUA_SADM.md` (no se editaron).
Reproducir: `python3 scripts/build_b4.py` (sin red) → `data/b4_escenarios.csv`, `data/b4_escalonado.csv`, `b4/data/economia.json`.

## 1. Entradas

| Concepto | Valor | Etiqueta |
|---|---|---|
| Precio de la máquina | **$87,000** por estación | **[DATO]** (Nicolás) |
| Precio de recarga (garrafón 19 L) | $12 | [DATO] (docs previos) |
| Meta | **$21,750/mes** | [DATO] usuario/reporte, no verificado |
| Renta del local | $1,000/mes | [DATO] usuario/reporte, no verificado (`UNIT_ECONOMICS_RECONCILIADO.md`) |
| Volumen por estación | 30 garr/día = 900/mes | **[SUPUESTO]** (`UNIT_ECONOMICS_RECONCILIADO.md`; sin validar con ventas) |
| Luz + filtros + sal | $0.30 (mejor) – $0.85 (peor) por garrafón | [SUPUESTO] (mismo doc) |
| Recuperación de la ósmosis | 80 % | [DATO] de Nicolás en `RECONCILIADO` (el $2.50 plano es a 80 %); no verificado con ficha del equipo → sensibilidades 65 % y 50 % |
| Tarifa agua | SADM sept-2026 Cat. 2 y Cat. 6, `data/sadm_tarifas_sep2026_cat2_cat6.csv` | [DATO] oficial (PDFs 535/537) |
| Margen mensual por estación | `ingreso − renta − agua − otros` | misma fórmula que `RECONCILIADO` §3; se reproducen sus cifras (ver §3) |

Agua: m³ comprados = garr/mes × 19 L ÷ 1000 ÷ recuperación, facturados redondeando arriba, + cargo fijo (igual que `RECONCILIADO`).

## 2. Decisión SADM: Cat. 6 (comercial) como base, Cat. 2 como sensibilidad — **[SUPUESTO]**

**Evidencia en el repo**
- `COSTO_AGUA_SADM.md`: Cat. 2 es el escenario «doméstica, sin comercial» y dice «no usar Cat. 6 si el recibo es doméstico» → el doc no resuelve cuál aplica a una purificadora.
- `UNIT_ECONOMICS_RECONCILIADO.md` §2: «Qué categoría aplica a una purificadora: **[NO VERIFICADO]**»; «un negocio con medidor propio normalmente se factura comercial (Cat. 6), pero la clasificación la decide SADM»; «por prudencia el caso Cat. 6 es el realista si hay giro comercial».
- `SADM_AGUA_CONFIABILIDAD.md` §4: la estación **toma el agua del anfitrión** (casa o negocio); no dice nada de categoría.

**Decisión B4.** Una estación de recarga **revende agua** (ingreso $12/garr) → es uso comercial/servicio, no doméstico. Aunque la toma esté en una casa, el giro es comercial y SADM puede reclasificar; Cat. 6 es además el caso **más caro** (≈$0.47/garr más que Cat. 2 a 900 garr/mes), o sea el conservador para un payback. **Cat. 2 queda como sensibilidad** (anfitrión doméstico y SADM no reclasifica).
Riesgo adicional **[ABIERTO]**: si la estación comparte medidor doméstico con la casa, la tarifa por bloques repricia **todo** el consumo del hogar + estación, y el costo real sería mayor que el de la tabla (no hay consumo del hogar en el repo → no se calcula). Preguntar a SADM con la dirección real.

## 3. Margen y payback por estación (30 garr/día, 80 %)

| Escenario | Agua $/mes | $/garr | Margen/mes (peor – mejor) | Payback 1 estación (meses) | Estaciones para $21,750 |
|---|--:|--:|--:|--:|--:|
| **BASE B4: Cat. 6 @80 %** | $1,046.72 | $1.16 | **$7,988 – $8,483** | **10.9 – 10.3** | 3 – 3 |
| Cat. 2 @80 % (sensibilidad SADM) | $625.62 | $0.70 | $8,409 – $8,904 | 10.3 – 9.8 | 3 – 3 |
| Cat. 6 @65 % | $1,453.23 | $1.61 | $7,582 – $8,077 | 11.5 – 10.8 | 3 – 3 |
| Cat. 6 @50 % | $2,458.04 | $2.73 | $6,577 – $7,072 | 13.2 – 12.3 | 4 – 4 |
| Cat. 2 @50 % | $1,594.16 | $1.77 | $7,441 – $7,936 | 11.7 – 11.0 | 3 – 3 |
| Agua plana $2.50 @80 % [NICOLÁS, sin tarifa] | $2,250.00 | $2.50 | $6,785 – $7,280 | 12.8 – 12.0 | 4 – 3 |

Chequeo: los márgenes coinciden con `RECONCILIADO` §3 (Cat. 6 @80 % $7,988–$8,483; Cat. 2 @80 % $8,409–$8,904; plano $6,785–$7,280; Cat. 6 @50 % $6,577–$7,072).
Payback = $87,000 ÷ margen (peor – mejor caso de «otros costos»). **No incluye** operador, impuestos, garrafones/tapas, merma, instalación ni permisos **[ABIERTO]** → el payback real es **mayor**.

## 4. Meta $21,750/mes y 4 estaciones (BASE: Cat. 6 @80 %, 30 garr/día)

| | Peor | Mejor |
|---|--:|--:|
| Margen por estación | $7,988 | $8,483 |
| **3 estaciones**: margen/mes (meta $21,750) | **$23,964** (cubre, +$2,214) | **$25,449** |
| 3 estaciones: capital | $261,000 | $261,000 |
| **4 estaciones**: margen/mes | **$31,953** | **$33,933** |
| 4 estaciones: capital ($87,000 × 4) | **$348,000** | $348,000 |
| **Payback 4 estaciones, a plena desde el día 1** | **10.9 meses** | **10.3 meses** |
| Payback 3 estaciones, a plena | 10.9 meses | 10.3 meses |

- Con 4 estaciones iguales el payback en meses **es el mismo que el de una** (capital y margen escalan igual); lo que cambia es el capital expuesto ($348,000) y el colchón sobre la meta (+$10,203 a +$12,183/mes).
- **3 estaciones bastan para la meta en el caso base**; hacen falta 4 si el agua cae a Cat. 6 @50 % o con el agua plana $2.50 en el peor caso, o si el volumen baja (ver §5).
- **Escalonado [SUPUESTO]** (`data/b4_escalonado.csv`): una estación abre por mes, cada una con rampa 50 %/75 %/100 % de 30 garr/día en sus meses 1/2/3. Meses desde la primera apertura hasta recuperar el capital: 1 estación **12 (peor y mejor)**; 3 estaciones **13**; **4 estaciones 14 (peor) – 13 (mejor)**; con Cat. 2: 12–11, 13–12, 13–13. La rampa y el ritmo de apertura son inventados para ilustrar; no hay ventas reales.

## 5. Sensibilidad al volumen (Cat. 6 @80 %) — el punto débil

| garr/día | Margen/mes (peor – mejor) | Payback 1 est. (meses) | Estaciones para meta | ¿4 estaciones cubren $21,750? |
|--:|--:|--:|--:|---|
| 40 | $10,742 – $11,402 | 8.1 – 7.6 | 3 – 2 | sí |
| **30 (base)** | $7,988 – $8,483 | 10.9 – 10.3 | 3 – 3 | sí |
| 25 | $6,435 – $6,847 | 13.5 – 12.7 | 4 – 4 | sí (justo: $25,740–$27,390) |
| 20 | $4,864 – $5,194 | 17.9 – 16.7 | 5 – 5 | **no** ($19,457–$20,777) |
| 15 | $3,271 – $3,518 | 26.6 – 24.7 | 7 – 7 | no |

Con Cat. 2 a 20 garr/día: margen $5,300 – $5,630, payback 16.4 – 15.5 meses, 5–4 estaciones. Conclusión **[SUPUESTO sobre volumen]**: el payback depende casi todo de vender ≥25 garr/día; la categoría SADM mueve ~0.6 mes. Validar con las ventas de la primera estación antes de comprar la 2.ª–4.ª (coherente con `GAPS_RATING_DENSIDAD.md`/`BANDA_CONFIANZA.md`: sin ventas reales, el modelo es de juicio).

## 6. Qué es dato y qué supuesto (resumen)

- **Dato:** $87,000 (máquina); tarifas SADM sept-2026 Cat. 2/6; $12/garr; meta $21,750 y renta $1,000 (de usuario/reporte, sin verificar).
- **Supuesto:** 30 garr/día; otros costos $0.30–$0.85/garr; Cat. 6 como base; 80 % de recuperación (dato de Nicolás pero sin ficha); escalonado y rampa; separación entre estaciones (ver `B4_MEZCLA.md` §Separación).
- **Abierto:** operador/mano de obra, impuestos, garrafones, merma, instalación, permisos, consumo del hogar anfitrión, ventas reales.
