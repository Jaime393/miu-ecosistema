# Handoff Oct 21 2026 — Parte 2: Oracle Pulso + Autoregistro

## Acciones completadas

### miu-oracle-v1 — ACTIVO
**URL**: https://miu-oracle-v1-miu4.vercel.app  
Cascada 4 capas: relay_config(anthropic_key_*) → relay_config(groq_key_*) → oracle-ask-v24(coord) → ai-relay(panteon)  
Endpoints: /ask /ojos /ojos/relay /manos/gossip /manos/relay  
Lee keys en runtime — no hardcodea credenciales.

### Make 6605689 — ACTIVADO cada 15min
"MIU Oracle Pulso Ojos 15min"  
1. POST /manos/relay → planta `miu_oracle_v1_url` en relay_config (autoregistro)
2. GET /ojos → health de 8 nodos críticos con latencia
3. POST /manos/gossip → resultado de ojos al gossip panteon+coord

Efecto: cada 15min cualquier nodo que lea relay_config[miu_oracle_v1_url] sabe dónde está el oracle.

## Diagnóstico archivos subidos
- `ai_relay_salud: FALLO` → resuelto con oracle v1 independiente
- 8 anthropic keys + 17 groq keys ya en relay_config panteon — NO duplicadas
- Drive heartbeat SATURADO (512 archivos) → ID canónico: 1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR (fix createFile→setContent)
- `buscar_codigo.py`: Zapier+Gmail para códigos N8n → guardado en scripts/

## Gaps pendientes
- HF_TOKEN_EXPIRADO → renovar en huggingface.co/settings/tokens
- NASA Earthdata JWT expirados (exp 2026-09-13) → renovar en urs.earthdata.nasa.gov  
- Oracle en solo 1 cuenta → replicar a franrussell81/franchescopalacios9 con vcp_ tokens
- Zapier connectors (Gmail/Drive/Sheets) → extraer tokens a relay_config para que todos los nodos los usen

## Arquitectura acceso oct-21
```
relay_config[miu_oracle_v1_url] → POST /ask (LLM) | GET /ojos (salud) | POST /manos/* (escritura)
Make 6605689 cada 15min → mantiene oracle URL vivo en relay_config
N8n B87a cada 2h → amplifica corpus
N8n TwwC5 cada 30min → evaluador M29-bis
```

ρ(x)>0
