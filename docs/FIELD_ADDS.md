# Field adds (multi-celular)

Actualizado: 2026-09-24 — dock ★/＋/Comp + Scout auto-ntfy; merge Action ~cada 2 h.

## Qué hace cada teléfono
1. Ubicarme → ★ Fav / ＋ anclas / Comp
2. Al **guardar**, el pin se pinta local y se manda solo a la bandeja ntfy (`purif-zmm-campo-casca-v1`). La otra persona no toca nada extra.
3. Al **abrir** el mapa, se baja `data/field_adds.geojson` (capa compartida) y se ven los pines de todos.


## Scout → mismo pipeline
`scout.html` hace upsert/delete ntfy en cada pin, comentario LineString y undo (toast Enviado al mapa / Error sync). Misma bandeja y merge que el dock del mapa. Delay hasta Pages: ~2 h **si** el merge workflow está instalado; si no, hay que mergear a mano / instalar Action.

## Qué hace Purificador / routine / GitHub Actions
- Poll ntfy → `python3 scripts/merge_field_add_issues.py` → escribe `data/field_adds.geojson` + `data/field_adds_deleted.json` → commit+push Pages.
- Cadencia: Actions en schedule (~cada 2 h), `workflow_dispatch` y `repository_dispatch` (`merge-field-adds`). Si no hay cambios, silencio (`NO_CHANGES`).
- Plantilla: `docs/merge-field-adds.workflow.yml` → instalar en `.github/workflows/merge-field-adds.yml` (token scope `workflow`). Cron `15 */2 * * *` + dispatch. **Estado 2026-09-24:** el repo solo tiene Pages Action; el merge workflow aún no está activo — pines llegan a ntfy + LS, pero no a `field_adds.geojson` hasta instalarlo o correr `python3 scripts/merge_field_add_issues.py` a mano.
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

## Tránsito OSM (contexto)
Las capas Semáforos / Altos del mapa vienen de OSM (`data/semaforos_zmm.geojson`, `data/stops_zmm.geojson`) y son **independientes** de field_adds / ntfy / Scout sync. Incluyen señales `highway=traffic_signals` (nodo/vía), cruces `crossing=traffic_signals`, `highway=stop|give_way` y `traffic_sign=stop` cuando están mapeados.
La cobertura OSM sigue incompleta; Scout **S** sigue siendo la vía para altos/semáforos vistos en campo. Regenerar: `python3 scripts/fetch_osm_traffic.py`.

