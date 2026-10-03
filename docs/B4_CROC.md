# Diagnóstico: por qué Croc queda donde queda (B4, fórmula 0.45/0.45/0.10)

Croc (Monterrey, `19039_0167`, ~4,534 viviendas, encuestada: 88 marcas Scout). **Confianza alta.** Nicolás sabe que es muy buena; esto explica qué dice el modelo, no lo corrige a mano.

## Componentes (datos del repo)

| Componente | Valor | Lectura |
|---|---:|---|
| Demanda\* | **1.000** | La más alta de las 167 colonias (única con 1.0). |
| Anclas\* | **0.3735** | Percentil 37 de anclas ponderadas por 1,000 viv (21.9/1000 viv; 99.25 pts de anclas). Es su punto débil **relativo**: es una colonia grande (4,534 viv) y las anclas se normalizan por viviendas. |
| Competencia | 3 purificadoras ≤300 m (0.66/1000 viv), C = 0.4157 → Comp_bonus\* = 0.52 | Bono bruto 10×0.52 = 5.2 < 6.87 (= 10% de su base): `max(...)` lo deja en **0**. Nunca resta. |

## Cuenta (nueva fórmula)

```text
base_renorm = 100×(0.45×1.000 + 0.45×0.3735)/0.90 = 50×(1.000+0.3735) = 68.67
completa    = 100×(0.45 + 0.1681 + 0.10×0.5196)    = 66.79   ← menor que 68.67
score = max(68.67, 66.79) = 68.67  (bono 0.00)   →  Rank #3 de 167
```

Por encima: Rancho Viejo 71.69 (D 0.53, A 0.84, 7 competidores: base 68.55 + bono 3.14) y Tierra y Libertad 70.13 (D 0.45, A 0.89, 3 competidores: base 66.81 + bono 3.32). Sin ningún bono Croc sería **#1** (68.67 vs 68.55 de Rancho Viejo: empate técnico). Banda de puesto recalculada: p10 #1 · p50 #3 · p90 #16; prob. top 30 = 97.6 %; prob. top 10 = 87 %.

## Cómo se movió con cada fórmula

| Fórmula | Score | Rank | Qué pasó |
|---|---:|---:|---|
| v3 original (916576d): 0.40D + 0.30A + 0.30(1−C) | 68.73 | #4 | La competencia de Croc (C 0.42) le resta poco. |
| e7d1ecc: 0.40D + 0.30A + 0.30·Cb, 0 comp ⇒ 0 | 66.79 | **#8** | Su bono fue 0.52×30 = 15.6 pts; colonias con muchos competidores (Cb ≈ 1) recibían 30 pts, y la competencia pesaba 0.30 igual que Anclas. Croc perdía ~14 pts de bono frente a ellas aunque su Demanda (1.0 → 40 pts) es la máxima. |
| **Nueva: 0.45D + 0.45A, bono ≤10** | **68.67** | **#3** | Demanda y Anclas pesan igual y la competencia casi no mueve; la Demanda 1.0 de Croc vale 45 pts, compensa sus Anclas medias. |

## Qué lo limita / qué lo subiría (sin inventar)

- **Anclas\*** es el único freno: con Anclas\* 0.50 llegaría a 75.0 y con 0.70 a 85.0. Posible causa: Croc es muy grande, y "anclas por 1,000 viv" castiga colonias con muchas viviendas; **no está probado** que sea mala medida (SUPUESTO de normalización por viviendas, `docs/RATING_V3.md`).
- Con Scout activado (88 marcas, 59 de anclas usadas) Croc sube a **94.6 y #1** (B4, interruptor); el interruptor está apagado por defecto.
- Hay 8 competidores contando Scout (`comp_n_300m_with_scout`) vs 3 de DENUE/Places: la fuente de competencia de campo es mayor, pero no cambia el score base.
- Pendiente: 9.9 % de pendiente media (cuesta arriba, SUPUESTO >8 %): 2 de 3 estaciones sugeridas son planas; no entra al score.
- Distancia a casa: 16.8 km (informativo).
