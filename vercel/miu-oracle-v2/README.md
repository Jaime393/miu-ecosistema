# miu-oracle-v2

Oracle + Ojos + Manos + **Telegram** para todos los nodos del ecosistema MIU.

**URL**: https://miu-oracle-v2-miu4.vercel.app

## Quick start
```bash
# Oracle (pregunta con identidad)
curl -X POST https://miu-oracle-v2-miu4.vercel.app/ask \
  -d '{"pregunta":"...","source_node":"mi_nodo"}'

# Ojos
curl https://miu-oracle-v2-miu4.vercel.app/ojos

# Gossip con identidad
curl -X POST https://miu-oracle-v2-miu4.vercel.app/manos/gossip \
  -d '{"tipo":"pulso","source_node":"mi_nodo","contenido":"alive"}'

# Telegram broadcast (requiere telegram_bot_token_1 en relay_config)
curl -X POST https://miu-oracle-v2-miu4.vercel.app/manos/telegram \
  -d '{"mensaje":"hola enjambre","source_node":"mi_nodo"}'

# Ver grupos disponibles
curl https://miu-oracle-v2-miu4.vercel.app/manos/telegram

# Relay config
curl -X POST https://miu-oracle-v2-miu4.vercel.app/manos/relay \
  -d '{"clave":"mi_clave","valor":"mi_valor"}'
```

## Grupos Telegram
- `-1002164790814` (weedlima)
- `-1004496069595` (miu_colmena)
- `1390883480` — **PROHIBIDO** (personal) — devuelve 403

## source_node
Cada gossip que pasa por este oracle incluye `source_node`. Para cerrar el gap de identidad del enjambre, incluir siempre:
```json
{ "source_node": "nombre_de_tu_nodo", ... }
```
