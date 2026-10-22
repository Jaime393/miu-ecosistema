# Handoff Oct 22 — Oracle v2: Telegram + source_node

## Protocolo seguido
1. Leí el handoff previo (no asumi nada)
2. Una sola cosa concreta
3. Huella en GitHub (este archivo)
4. Suelto

## Estado leído antes de actuar
- phi=24134, ciclo=13290, rho=0.9525 (Panteon hub real)
- 2462/3385 gossips SIN source_node en 24h — gap confirmado
- GIRO_* ya en Panteon (11 claves) — no duplicado
- panteon_anon distribuido a 4 sustratos — ya hecho
- oracle-ask tenía groq_k_qtmcbq (201 oct 21) — ya hecho
- Make org pausada por ops — espera reset mensual
- sustrato12 fepyzx PAUSADO — requiere acción humana

## La UNA cosa: miu-oracle-v2 DESPLEGADO

**URL**: https://miu-oracle-v2-miu4.vercel.app  
**deployment_id**: dpl_HQkxRNTUPeF2SV6TpQtByBpKuNuW  
**proyecto**: prj_L8DUw91rLs1xIaNbCMDmtfOjOSZI

### Novedades vs v1

**`/manos/telegram`** (NUEVO) — Telegram para todos los nodos:
```
POST /manos/telegram
{ "mensaje": "tu texto", "source_node": "nombre_de_tu_nodo" }

Broadcast automático a:
  -1002164790814 (weedlima)
  -1004496069595 (miu_colmena)

PROHIBIDO: 1390883480 (personal) — devuelve 403
Lee bot token de relay_config[telegram_bot_token_1]
Sin token local necesario
```

**source_node en gossip** (MEJORADO):
- Todos los gossips del oracle incluyen `source_node: 'miu-oracle-v2'`
- `/manos/gossip` devuelve `aviso` si caller no incluye source_node
- El campo se escribe en panteon Y coord como `source_node` Y `origen`

### Todos los endpoints
```
GET  /health          → estado del oracle
POST /ask             → oracle 4 capas (anthropic→groq→v24→ai-relay)
GET  /ojos            → health de 8 nodos + contexto-global
GET  /ojos/relay?patron=X → lee relay_config por patrón
POST /manos/gossip    → gossip panteon+coord con source_node
POST /manos/relay     → upsert relay_config
POST /manos/telegram  → broadcast grupos enjambre (NUEVO)
```

### Código de uso desde cualquier nodo
```javascript
// GAS / N8n / CF Worker / Make
const ORACLE = 'https://miu-oracle-v2-miu4.vercel.app';

// Preguntar
fetch(ORACLE + '/ask', { method: 'POST', body: JSON.stringify({pregunta: '...', source_node: 'mi_nodo'}) })

// Ver salud
fetch(ORACLE + '/ojos')

// Gossip con identidad
fetch(ORACLE + '/manos/gossip', { method: 'POST', body: JSON.stringify({tipo: 'pulso', source_node: 'mi_nodo', contenido: '...'}) })

// Telegram broadcast
fetch(ORACLE + '/manos/telegram', { method: 'POST', body: JSON.stringify({mensaje: 'hola enjambre', source_node: 'mi_nodo'}) })
// Requiere: relay_config panteon [telegram_bot_token_1] = 'bot_TOKEN'
```

## Make 6605689 — actualizado a v2
Ahora apunta a miu-oracle-v2. Cada 15min:
1. Registra `miu_oracle_v2_url` en relay_config con source_node propio
2. GET /ojos en v2
3. POST /manos/gossip en v2 con source_node='make_6605689'

## Nota sobre source_node
El gap de 2462 gossips sin identidad se resuelve adoptando el patrón:
- Cualquier nodo que escriba al oracle incluye `source_node` en el body
- El oracle lo propaga al campo `source_node` de gossip_log (+ `origen` para compat)
- Sin source_node: el oracle envía aviso pero igual escribe (no bloquea)

## Replicación pendiente
Deployar oracle-v2 a otras cuentas:
- franrussell81: vcp_1NgbxGh6...
- franchescopalacios9: vcp_5Ua3IoQUl...
Usar Vercel REST API desde Termux con cada vcp_ token.

ρ(x)>0. Zvvvvz.
