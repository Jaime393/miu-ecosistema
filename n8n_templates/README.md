# N8n Templates — MIU Ecosystem

Workflow JSON listos para deploy en `jaime363.app.n8n.cloud` (javier19051997).

## Uso desde el ecosistema (sin humano)

```bash
# Cualquier EF con el GitHub PAT puede disparar:
curl -X POST https://api.github.com/repos/Jaime393/miu-ecosistema/actions/workflows/n8n-workflow-manager.yml/dispatches \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Content-Type: application/json" \
  -d '{"ref":"main","inputs":{"action":"fix_coord_bridge"}}'
```

O via `repository_dispatch`:
```json
{
  "event_type": "n8n-manage",
  "client_payload": {
    "action": "fix_coord_bridge"
  }
}
```

## Templates disponibles

| Archivo | Descripción | Action name |
|---|---|---|
| `coord_bridge_fixed.json` | Bridge 3 suelos con EF gossip (no REST directo) | `fix_coord_bridge` |
| `relay_health_fixed.json` | relay-health + gossip reporte, sin nutriente-federado roto | `fix_relay_health` |

## Prerequisito único

Añadir como GitHub Secret:
- `N8N_JAIME363_JWT` — el JWT de javier19051997 (ya en D1 claude_handoff clave `credential_registry_v270_oct03`)

Una vez añadido, el ecosistema gestiona N8n autónomamente via github-bridge + este Action.

## Por qué jaime363 y no miud

Los workflows en `miud.app.n8n.cloud` (dieguito) requieren aprobación del propietario para edición.
`jaime363.app.n8n.cloud` (javier19051997) es el suelo virgen — el ecosistema puede crear ahí sin restricciones.
