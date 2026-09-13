# Cómo llegamos a la fórmula final (`score_100`)

**Mapa en vivo:** https://casca-code.github.io/mapa-purificadoras/  
**Repo:** https://github.com/CASCA-code/mapa-purificadoras  

Este documento explica el *por qué* del ranking Version 2 (no solo la ecuación). Universo: **167 colonias** de la ZMM filtradas (municipios ZMM8 · marginación Medio/Alto · población ≥ 1 500), mismas geometrías CONAPO/IMC 2020 del estudio v1.

---

## 1. Punto de partida (Version 1)

El artefacto viejo usaba una razón simple:

```text
site_score ≈ demanda / (1 + competencia)
```

- **Demanda** ≈ población servida en walkshed (~500 m) × mezcla de OVHAC/OVSAE (en v1 ~0.70 / 0.30).
- **Competencia** = DENUE formal (SCIAN 312112) + proxy informal (~1.5 por 1 000 viviendas).

Eso priorizaba “mucha gente / poca competencia”, pero:

1. Las **anclas de flujo** (escuela, iglesia, hospital…) solo eran capa visual; no movían el ranking.
2. No había **canibalización** entre estaciones propias.
3. Un solo cociente mezclaba todo: difícil explicar pesos de negocio (“¿cuánto pesa la demanda vs el vecindario?”).
4. Sensibilidad: colonias #1 por score a veces caían mucho al tocar supuestos (ej. Gloria Mendiola).

Decisión de producto (Nicolás + sparring): **Version 2 en paralelo**, no borrar v1.

---

## 2. Diseño de Version 2: cuatro factores normalizados

Pasamos a un score compuesto 0–100, con cada pieza en 0–1 (**min-max sobre las mismas 167 colonias**) y pesos que suman 1:

```text
score_100 = 100 × (
    0.40 · Demanda*
  + 0.25 · (1 − Comp*)
  + 0.20 · Anclas*
  + 0.15 · (1 − Canibal*)
)
```

### Por qué esos pesos

| Peso | Factor | Lógica de negocio |
|-----:|--------|-------------------|
| **0.40** | Demanda* | Sin gente que compre garrafón no hay sitio. Sigue siendo el driver principal. |
| **0.25** | (1 − Comp*) | Competencia formal + informal resta, pero no debe ahogar la demanda (por eso no es 50/50). |
| **0.20** | Anclas* | Proxy de **flujo de paso** (camino a escuela/iglesia/tienda): recarga de oportunidad, no solo población dormitorio. |
| **0.15** | (1 − Canibal*) | Reserva para no pisarnos entre estaciones propias; hoy el CSV suele ir vacío → el 15 % se otorga completo. |

Viabilidad económica (**$12**/garrafón, break-even ~**$13 000**/mes) se calcula en columnas aparte y **no entra** al `score_100`, para no mezclar “atractivo de colonia” con supuestos de OPEX aún provisionales.

---

## 3. Cómo se construye cada término

### Demanda*

Problema v1: `served_pop` en buffer a veces **sobrecontaba** vs población de la colonia.

Ajuste v2:

1. `pob_eff = 0.5 · served_pop_500m + 0.5 · min(served_pop_500m, 5 · POB_TOT)`  
   → tope suave: no dejar que el walkshed invente más de ~5× la población modelada CONAPO.
2. Intensidad de uso de agua: `0.85 · OVHAC_norm + 0.15 · OVSAE_norm`  
   (más peso a vivienda/hogares que a OVSAE vs v1 0.70/0.30).
3. `demanda_raw = pob_eff · esa mezcla` → min-max → **Demanda\***.

### Comp* (competencia)

- **Formal:** DENUE 312112 cerca del centroide (recarga peso 1.0, planta/embotellador 0.15, decay ~400 m).
- **Informal:** proxy **1.0 por 1 000 viviendas** (bajamos de 1.5/1000 tras revisión: el informal no debía dominar el denominador como en v1).
- Suma → min-max → **Comp\***. En el score entra como `(1 − Comp*)`.

### Anclas*

Dejaron de ser solo mapa: son el **20 %** del score.

- Radio: anclas a **≤ 250 m del centroide** (no “cualquier punto del polígono”).
- Contribución: `peso · exp(−d / 250)`.

Orden de pesos (flujo peatonal / camino a la estación):

| Ancla | Peso |
|-------|-----:|
| Jardín de niños | 1.00 |
| Bodega Aurrera Express / Soriana Express | 0.90 |
| Iglesia · Banco del Bienestar · Banco Azteca | 0.85 |
| Modelorama / Six / cerveza specialty | 0.80 |
| Hospital | 0.70 |
| Universidad | 0.55 |
| Primaria / secundaria | 0.40 |
| Preparatoria | 0.35 |
| College | 0.30 |
| Otra escuela | 0.20 |

Retail/bancos se añadieron después (sep 2026) como proxy de **alto flujo en D+/D**; entran solo por Anclas\* (no tocan Demanda\* ni Comp\*). Detalle: `docs/ANCLAS_RETAIL_BANCOS.md`.

Explícitamente **fuera**: casas abandonadas, capa de población haitiana.

### Canibal*

Suma `exp(−d / 500)` desde el centroide a filas de `estaciones_propias.csv`.  
CSV vacío → Canibal\* = 0 → el factor `(1 − Canibal*)` vale 1 y el sitio recibe el 0.15 completo hasta que haya red propia.

---

## 4. Qué cambió respecto a v1 (resumen)

| | v1 | v2 (final actual) |
|---|----|-------------------|
| Forma | `demanda / (1+comp)` | Suma ponderada 0–100 |
| Demanda | served × (0.70/0.30) | `pob_eff` + tope 5×POB + (0.85/0.15) |
| Informal | ~1.5 / 1 000 viv. | **1.0** / 1 000 viv. |
| Anclas | Solo contexto | **20 %** del score + retail/bancos |
| Canibalización | No | 15 % vía CSV |
| Precio / BE (fuera del score) | ~$15 · ~$18k | **$12** · ~**$13k** |

---

## 5. Cómo leer el resultado

- **Rank / `score_100`:** oportunidad relativa entre las 167 (no es probabilidad de venta).
- **Top estable vs sensibilidad:** una colonia puede liderar el score y caer en pruebas “qué pasa si…”; por eso el mapa + checklist de campo siguen siendo la validación.
- Recomendación de concentración (negocio): priorizar pocas estaciones en una colonia grande bien rankeada (p. ej. lógica Escobedo / San Miguel Residencial en el estudio), no dispersar por score crudo solo.

Pipeline: `pipeline_v2.py` → `colonias_v2.geojson` / CSV → mapa Leaflet en Pages.

---

## 6. Enlaces

| Recurso | URL / path |
|---------|------------|
| **Website (mapa v2)** | https://casca-code.github.io/mapa-purificadoras/ |
| Repo | https://github.com/CASCA-code/mapa-purificadoras |
| Spec corta v2 | `docs/README_version2.md` |
| Anclas retail/bancos | `docs/ANCLAS_RETAIL_BANCOS.md` |
| Ubicarme | `docs/UBICARME.md` |
| Mapa Tec (otro producto) | https://casca-code.github.io/mapa-purificadoras/tec/ |

---

*Documento generado para Nicolás / Purificadoras · 2026-09-13. Si cambian pesos o el universo de colonias, actualizar este archivo en el mismo commit que el pipeline.*
