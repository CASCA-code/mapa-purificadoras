# Field adds (multi-celular)

## Qué hace cada teléfono
1. Ubicarme → ★ Fav / ＋ anclas / Comp
2. Al **guardar**, el pin se pinta local y se manda solo a la bandeja ntfy (`purif-zmm-campo-casca-v1`). La otra persona no toca nada extra.
3. Al **abrir** el mapa, se baja `data/field_adds.geojson` (capa compartida) y se ven los pines de todos.

## Qué hace Purificador / routine / GitHub Actions
- Poll ntfy → `python3 scripts/merge_field_add_issues.py` → escribe `data/field_adds.geojson` + `data/field_adds_deleted.json` → commit+push Pages.
- Cadencia: Actions en schedule (~cada 2 h), `workflow_dispatch` y `repository_dispatch` (`merge-field-adds`). Si no hay cambios, silencio (`NO_CHANGES`).
- Plantilla del workflow: `docs/merge-field-adds.workflow.yml` → copiar a `.github/workflows/merge-field-adds.yml` (hace falta token con scope `workflow`; el OAuth de Agents no lo tiene).
- Deletes: si el `id` aún no está en el geojson, igual se persiste en `field_adds_deleted.json` (tombstone) para no re-mergear luego.

## ntfy topic (seguridad)
- Topic actual en cliente JS y script: `purif-zmm-campo-casca-v1` (público en el repo / Pages).
- **Rotar a un topic secreto** cuando se pueda sin cortar campo: generar string largo aleatorio, actualizar `NTFY_TOPIC` en `index.html` y `scripts/merge_field_add_issues.py`, redeploy Pages, y avisar a quien use el mapa en vivo.
- Ideal a medio plazo: topic solo en env/secrets del Action + config no commiteada; el cliente hoy necesita el topic en JS para POST — no hay proxy. No hardcodear un secret nuevo en el repo sin rotar el viejo.
- TODO en `index.html` junto a `NTFY_TOPIC`: mover a env / rotar.

## Notas
- Sin red al guardar: queda en localStorage; el próximo save con red / merge no lo recupera solo — por eso el auto-push al guardar importa.
- Plan B (botón “Subir mis pines”) si hace falta más adelante.
- Liked zones vs favoritos campo: si mismo `id` o mismas coords (~5 dec), el mapa no pinta el liked encima del favorito de `field_adds`.
