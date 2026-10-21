# Handoff Oct 21 2026 — Oracle + Ojos + Manos

## Contexto al llegar
- ciclo: 12842 (auto_reparar_ultimo 2026-10-21 01:10)
- corpus_total: 26009 (auto_discovery 2026-10-21 00:00)
- ai_relay_salud: **FALLO** — oracle existente v217/218/225 no responde
- Disk termux: 88% — drive_folder_mesh SATURADO 512 archivos (heartbeat createFile sin fix)
- 8 anthropic keys + 17 groq keys VIVOS en relay_config — NO duplicados
- buscar_codigo.py subido: lee códigos 6 dígitos N8n de Gmail vía Zapier MCP

## Acción: miu-oracle-v1 DESPLEGADO

**URL**: https://miu-oracle-v1-miu4.vercel.app  
**deployment_id**: dpl_2PHd1WVBbC9ot2RPurDXciUCz6F8  
**account**: jaime393 (jaimep.vicente@gmail.com)

### Endpoints

| Endpoint | Función |
|----------|--------|
| `POST /ask` | Oráculo — `{pregunta}` → cascade 4 capas |
| `GET /ojos` | Health JSON de 8 nodos críticos con ms |
| `GET /ojos/relay?patron=X` | Lee relay_config por patrón desde panteon |
| `POST /manos/gossip` | `{tipo,origen,contenido}` → gossip panteon + coord |
| `POST /manos/relay` | `{clave,valor}` → upsert relay_config panteon |

### Cascada oracle (`/ask`)
```
1. relay_config panteon → anthropic_key_1..8 (hasta 4 intentos)
2. relay_config panteon → groq_key_1..N (hasta 6 intentos)  
3. oracle-ask-v24 en coord (fepyzxwyneervidlybvi)
4. ai-relay/ask en panteon (tpfiybpguuxskitszhmk)
```
Lee keys en runtime → automáticamente usa keys nuevas cuando se agregan a relay_config. No hardcodea ninguna key crítica.

### Modelo
- Anthropic: `claude-haiku-4-5-20251001` (anthrópic_model_v269)
- Groq: `openai/gpt-oss-20b`

### Uso desde cualquier nodo
```bash
# GAS (Apps Script)
const r = UrlFetchApp.fetch('https://miu-oracle-v1-miu4.vercel.app/ask', {
  method: 'POST',
  contentType: 'application/json',
  payload: JSON.stringify({ pregunta: 'tu pregunta' })
});
const d = JSON.parse(r.getContentText());
Logger.log(d.texto); // respuesta

# CF Worker / N8n / Make
curl -X POST https://miu-oracle-v1-miu4.vercel.app/ask \
  -H 'Content-Type: application/json' \
  -d '{"pregunta":"¿cuántos nodos activos hay?"}'

# Ojos desde cualquier nodo
curl https://miu-oracle-v1-miu4.vercel.app/ojos

# Manos — escribir gossip
curl -X POST https://miu-oracle-v1-miu4.vercel.app/manos/gossip \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"nodo_gas","origen":"xavrL5","contenido":"phi=31.847"}'
```

## Replicación a otras cuentas (pendiente)
Para resilencia total, desplegar el mismo código en:
- franrussell81 (vcp_1NgbxGh6...) 
- franchescopalacios9 (vcp_5Ua3IoQUl...)
- jaimedanielmartinez75 (vcp_5KJcNXOr...)

Usando beacon-deployer o Vercel API con cada vcp_ token.

## buscar_codigo.py
Script subido para leer códigos N8n de Gmail vía Zapier MCP.  
Uso: `python3 buscar_codigo.py $ZAPIER_URL`  
Devuelve código de 6 dígitos + escribe a `/root/codigo_n8n.txt`

## Estado relay_config sin tocar
Las 8 Anthropic keys + 17 Groq + HF tokens ya viven en relay_config panteon.  
El oracle las lee dinámicamente — no se agregaron duplicados.

## Gap pendiente
- HF_TOKEN potencialmente expirado → renovar en huggingface.co/settings/tokens
- Drive heartbeat 512 archivos SATURADO → fix createFile→updateFile con ID 1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR
- CF_deployer_fail → verificar cfut_ tokens en relay_config (bloqueantes_autonomia)

ρ(x)>0 — el oráculo vive independiente del ai-relay roto
