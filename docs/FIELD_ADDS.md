# Field adds (Ubicarme → ＋ Añadir)

En el mapa ZMM, con **Ubicarme** activo:

1. **＋ Añadir**
2. Elige: **Purificadora de agua** · **Ancla** · **Otra** (texto libre)
3. Guarda → pin local + issue `field-add` en GitHub
4. Action mergea a `data/field_adds.geojson` → Pages lo muestra

`Otra` queda con `nota_raw`; Purificador interpreta y reclasifica (no inventar score).

## Automatización (sin GitHub Actions workflow scope)

Purificador corre `scripts/merge_field_add_issues.py` (lee issues abiertos `field-add` / título `field-add:`, mergea GeoJSON, cierra issue, push Pages).
