# Field adds (multi-celular)

## Qué hace cada teléfono
1. Ubicarme → ★ Fav / ＋ anclas / Comp
2. Al **guardar**, el pin se pinta local y se manda solo a la bandeja ntfy (`purif-zmm-campo-casca-v1`). La otra persona no toca nada extra.
3. Al **abrir** el mapa, se baja `data/field_adds.geojson` (capa compartida) y se ven los pines de todos.

## Qué hace Purificador / routine
- Poll ntfy → merge a `data/field_adds.geojson` → commit+push Pages.
- Cadencia: varias veces al día (campo); si no hay cambios, silencio.

## Notas
- Sin red al guardar: queda en localStorage; el próximo save con red / merge no lo recupera solo — por eso el auto-push al guardar importa.
- Plan B (botón “Subir mis pines”) si hace falta más adelante.
