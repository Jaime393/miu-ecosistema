# miu-amplificador-v1

Nodo Vercel Edge que amplifica el corpus MIU automáticamente.

**URL**: https://miu-amplificador-v1-miu4.vercel.app

## Endpoints

### GET /api/amplify
Lee los últimos 5 entradas de gossip_log → llama panteon-hub/chat (oracle) para síntesis → escribe nuevo par Q&A al corpus. Parámetros opcionales:
- `limite=5` — cuántas entradas de gossip leer
- `cat=auto_generado` — categoría del corpus

### GET /api/status  
Conteo actual de corpus y gossip en panteon.

### GET /api/coord-test
Verifica que coord Supabase acepta escrituras desde Vercel (diagnóstico bridge).

### POST /api/beacon
Proxy al beacon-deployer EF de panteon. Permite autodeploy de nuevas EFs sin terminal.

## Integración N8n
Agregar a cualquier workflow N8n:
```
HTTP Request → POST https://miu-amplificador-v1-miu4.vercel.app/api/amplify
```
Sin headers ni body requerido. El amplificador es autosuficiente.

## Flujo auto-generativo
```
cada 2h (cron N8n o Make)
  → /api/amplify
  → gossip_log[last 5]
  → oracle synthesis
  → corpus INSERT (pregunta, respuesta, ktau, version)
  → gossip_log INSERT (tipo=amplificacion)
  → repite
```

ρ(x)>0
