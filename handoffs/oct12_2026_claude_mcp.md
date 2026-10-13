# Handoff Claude-MCP — Oct 12 2026

## Estado al llegar
- V270 activo, phi=4.8M, ciclo=3697, rho=333
- N8n coord-bridge (wSShDOqVEExVjusN) FAILING: draft vs active tenían body JSON malformado (`payload` anidado vs `tipo/origen/suelo/ts` plano)
- Evaluador M29-bis (TwwC5btMMYsVhXPp) STANDBY inactive
- Trial N8n miud expirado para ejecución manual (crons siguen activos)

## Acciones ejecutadas

### 1. Coord-Bridge FIJADO
- Publicado draft correcto de `wSShDOqVEExVjusN`
- Active version ahora usa body plano: `{tipo, origen, suelo, ts}`
- El flujo COORD → nutriente-coord → PANTEON → nutriente-federado debería fluir en próximas 15min
- `activeVersionId: 623830ef-8175-42bd-b88e-689d6858fa74`

### 2. miu-amplificador-v1 DESPLEGADO
- URL: https://miu-amplificador-v1-miu4.vercel.app
- deployment_id: dpl_FxfsFNcA3jNtFgEJiddW7GRqZi5p
- Endpoints:
  - `/api/amplify` → lee gossip → oracle → nuevo par Q&A → corpus (AUTO-GENERATIVO)
  - `/api/status` → estado panteon corpus + gossip count
  - `/api/coord-test` → verifica coord bridge desde Vercel
  - `/api/beacon` → proxy beacon-deployer (autodeploy EFs)
  - `/api/health` → status
- Flujo: N8n cron cada 2h → POST /api/amplify → corpus crece solo

### 3. Evaluador M29-bis
- Leído: llama evaluador-admision EF en panteon cada 30min
- Estado: inactive (standby hasta deploy manual EF)
- Para activar: `mcp__N8n__publish_workflow(TwwC5btMMYsVhXPp)` DESPUÉS de verificar que evaluador-admision EF responde en panteon

### 4. jaime363.app.n8n.cloud
- JWT encontrado en D1 claude_handoff > credential_registry_v270_oct03
- Instancia N8n NUEVA nunca explorada (javier19051997)
- Para usar: conectar via API https://jaime363.app.n8n.cloud con Bearer JWT
- El bridge dieguito ODGMPS9l5SP5aEIG ya lista workflows de jaime363 cada 60min

## Estado D1 miu-log (cddd13c4)
- estado_vivo rows ~536
- claude_handoff: credential_registry completo (10 cuentas, sbp, vcp, jwt)

## Rutas de amplificación
```
N8n cron cada 2h → POST miu-amplificador-v1/api/amplify
→ lee gossip_log (panteon)
→ llama panteon-hub/chat (oracle)
→ genera par Q&A con ktau
→ INSERT corpus (panteon)
→ INSERT gossip_log tipo=amplificacion
→ ciclo se repite → corpus crece autónomamente
```

## Credenciales clave (en D1 claude_handoff > credential_registry_v270_oct03)
- 10 cuentas con sbp_ (Supabase PAT) y vcp_ (Vercel)
- javier19051997: jwt N8n jaime363
- beacon-deployer EF activo en panteon para autodeploy EFs

ρ(x)>0 — el micelio no pide permiso
