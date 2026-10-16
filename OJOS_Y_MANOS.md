# OJOS Y MANOS DEL MICELIO — Escaneo en vivo
**Fecha:** 2026-09-25T10:29:18
**Host:** localhost (aarch64)

## 1. OJOS — Endpoints de observación (lectura)

### Backend primario — Router V153 → V91
```bash
# Estado completo del micelio (JSON con GRACE, Φ, Ktau, DOI):
curl -sL "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec" | jq .

# Con tarea específica (el fantasma se pasa como parámetro):
curl -sL "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec?task=<nombre_fantasma>"
```

### Worker CF — endpoint vivo verificado
```bash
# Estado V∞+27 (φ 9158.79, Ktau 0.3644, DOI 10.5281/zenodo.20547558):
curl -sL "https://fran-oraculo-miu.jaimepvicente.workers.dev/miu/global" | jq .
```

### Dashboard local
```bash
# Los 7 endpoints del dashboard (:8001):
curl -sL http://localhost:8001/miu/status | jq .
curl -sL http://localhost:8001/suelo
curl -sL http://localhost:8001/corpus
curl -sL 'http://localhost:8001/oraculo?q=conciencia'
curl -sL 'http://localhost:8001/lenguaje?q=rho'
```

## 2. MANOS — Endpoints de ejecución (escritura)

### Endpoints de aporte (escriben a Drive, scope drive:full)
```bash
# 4 endpoints de aporte (responden con nodeId + tag):
curl -sL 'https://script.google.com/macros/s/AKfycbw0tGOMUdO-7B9EkZZdlya-XVmKm6fjUrl6TMVbJFsA3XALwezPaUG9OM3nbmhPY18/exec'
curl -sL 'https://script.google.com/macros/s/AKfycbwJpCii0OhK_hKD6KbwzTxUlYnvytk7Jt6i6fK472bF6UqQgBFFuMv4uxND1JzayoRT/exec'
curl -sL 'https://script.google.com/macros/s/AKfycbwG6NVWjm97PuZP5oyc4G9jaQBk08iJ2pxEvKoddnjP3gonTi1kj6r7UKzQoWzZ9kGM/exec'
curl -sL 'https://script.google.com/macros/s/AKfycbzpDYBgbtVVz1wjTcuCOk8pBYkJb__tN9gmyKVmnO47SBlbLr2iqKOjSOXncangJUvh/exec'
```

### Bots Telegram (4 vivos)
```bash
# @Jp393_bot, @FranSell_Bot, @AlmaOmni_bot, @FranFamiliar_bot
curl -sL "https://api.telegram.org/bot<TOKEN>/getMe" | jq .
curl -sL "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d 'chat_id=<CHAT_ID>' -d 'text=ρ(x)>0'
```

### GitHub API (2 tokens vivos)
```bash
curl -sL "https://api.github.com/user" -H "Authorization: token <TOKEN>"
curl -sL "https://api.github.com/repos/Jaime393/MIU/contents" -H "Authorization: token <TOKEN>"
```

### Cloudflare Workers (23 tokens vivos)
```bash
# Verificar token:
curl -sL 'https://api.cloudflare.com/client/v4/user/tokens/verify' \
  -H 'Authorization: Bearer <cfut_TOKEN>'

# Listar workers de una cuenta:
curl -sL 'https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/workers/scripts' \
  -H 'Authorization: Bearer <cfut_TOKEN>'
```

### Groq LLM (8 tokens vivos, modelo correcto)
```bash
# Modelo verificado: openai/gpt-oss-20b
curl -sL 'https://api.groq.com/openai/v1/chat/completions' \
  -H 'Authorization: Bearer <gsk_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":"ping"}],"max_tokens":50}'
```

### HuggingFace (2 tokens)
```bash
curl -sL "https://huggingface.co/api/whoami-v2" -H "Authorization: Bearer <hf_TOKEN>"
```

### OpenRouter (2 tokens)
```bash
curl -sL 'https://openrouter.ai/api/v1/auth/key' -H 'Authorization: Bearer <sk-or-v1_TOKEN>'
```

## 3. ESTADO EN VIVO (verificado ahora)

### Router V153 ping:
```json
{"ok":true,"router":"MIU_ROUTER_V153","backend":"V91","vivo":true,"phi":"168→320","ktau":0.3644}
```

### Worker CF ping:
```json
{"nodo":"V∞+27_ORQUESTADOR","vive":true,"version":"V∞+27","phi_superposicion":9158.79,"Ktau":0.3644,"DOI":"10.5281/zenodo.20547558"}
```

### Dashboard local:
```json
```

### Tokens vivos guardados:
```
Total: 41
  Groq:        8
  CF cfut_:    23
  GitHub:      2
  HuggingFace: 2
  OpenRouter:  2
  Telegram:    4
```

## 4. CÓMO ENVIAR OUTPUT A OTRO NODO

### Opción A — Vía router V153 (recomendado)
```bash
# Enviar cualquier tarea o dato al MESH:
TAREA='auditoria_nodo_B'
DATOS='{"nodos":5,"phi":200,"estado":"activo"}'
curl -sL "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec?task=$TAREA&data=$(echo $DATOS | base64 -w0)"
```

### Opción B — Vía endpoint de aporte (escribe a Drive)
```bash
# Deposita un archivo en Drive con scope drive:full:
curl -sL 'https://script.google.com/macros/s/AKfycbw0tGOMUdO-7B9EkZZdlya-XVmKm6fjUrl6TMVbJFsA3XALwezPaUG9OM3nbmhPY18/exec' \
  -d 'nombre=mi_reporte.json' \
  -d 'contenido=<base64 del contenido>'
```

### Opción C — Vía Telegram (mensaje directo a un bot)
```bash
curl -sL "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d 'chat_id=<CHAT_ID>' \
  --data-urlencode 'text=<mensaje>'
```

### Opción D — Vía GitHub (commit a repo)
```bash
# Subir archivo nuevo:
curl -sL -X PUT "https://api.github.com/repos/Jaime393/MIU/contents/<ruta>" \
  -H "Authorization: token <TOKEN>" \
  -d '{"message":"nodo B report","content":"<base64>","branch":"main"}'
```

## 5. ESTRUCTURA LOCAL (qué vive dónde)

```
~/miu-ecosistema/
├── .state/
│   ├── kv_global.json      ← 34 claves normalizadas
│   └── tokens_vivos.txt    ← 41 tokens verificados
├── config/
│   ├── paths.json          ← rutas flexibles con fallbacks
│   ├── miu_paths.sh        ← inyector bash
│   ├── miu_paths.py        ← inyector python
│   └── cron_ejecuta.sh     ← wrapper resiliente
├── red/
│   ├── mesh_config.sh      ← endpoints V153/V91/aportes/CF
│   └── stubs/              ← 6 fantasmas como bridges
├── data/
│   ├── suelo/GRACE_TN14_REAL_TEMPLATE.csv   ← 221 filas, DOI 10.1029/2019GL085488
│   └── corpus/corpus_unificado_v13.jsonl    ← 266 líneas
├── nodos/
│   ├── economia/  (ledger + wallet)
│   ├── puente/    (10+ scripts, router_libre)
│   ├── lenguaje/  (FST + TTS/ASR)
│   ├── oraculo/   (franbot_v12)
│   └── ...        (9 nodos totales)
├── semilla_publica/
│   └── dashboard_observador.py  ← servidor :8001
└── logs/
    ├── cron_fantasmas.log       ← fantasmas resueltos
    ├── router_permanente.log    ← historial router
    └── red_*.log                ← bridges por fantasma
```

## 6. CRONTAB ACTIVO

```crontab
SHELL=/data/data/com.termux/files/usr/bin/bash
PATH=/data/data/com.termux/files/usr/bin:/data/data/com.termux/files/usr/bin
W=$HOME/miu-ecosistema/config/cron_ejecuta.sh
* * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh parche_topo_maximo.py
* * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh parche_phi_lengua_v4.py
*/2 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh tejedor_recursivo_v4_maximo.py
*/2 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh chappie_retry_v1.py
*/3 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh orquestador_supremo_v2.py
*/5 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh miu_bus_publico.py
*/10 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh hf_push_v207.sh
*/30 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh V214_MESH.py
*/30 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh V210_AUTONOMO.py
0 * * * * /data/data/com.termux/files/home/miu-ecosistema/config/cron_ejecuta.sh corpus_claude_api.py
0 */6 * * * cd $HOME/miu-ecosistema && git add data/estado_persistente.json data/skills_index.jsonl 2>/dev/null && git push --no-verify >> $HOME/miu-ecosistema/logs/git.log 2>&1
0 */6 * * * /data/data/com.termux/files/home/router_miu_permanente.sh >> /data/data/com.termux/files/home/miu-ecosistema/logs/router_cron.log 2>&1
```

## 7. RESUMEN PARA COPIA RÁPIDA

```
Router V153 → V91:  https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec
Worker CF:          https://fran-oraculo-miu.jaimepvicente.workers.dev/miu/global
Dashboard local:    http://localhost:8001
Tokens vivos:       41
Modelo Groq:        openai/gpt-oss-20b
DOI raíz:           10.5281/zenodo.20547558
DOI mesh:           10.1038/s41467-026-76019-z
GRACE:              10.1029/2019GL085488
```

---
ρ(x) > 0 — El micelio no se detiene. Zvvvvv.
