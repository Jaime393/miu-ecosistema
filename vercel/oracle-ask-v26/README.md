# oracle-ask-v26

Oracle auto-descubierto — pool crece solo con relay_config.

**URL**: https://oracle-ask-v26-miu4.vercel.app  
**deployment_id**: dpl_HntNYbzuKnLeZjPZ5Gv9ACbjDSi8

## Diferencia vs v25
- v25: 4 Groq keys hardcodeadas
- v26: lee `llm_groq_key_*` + `groq_api_key_*` + `llm_deepseek_*` de panteon relay_config cada 5min
- Pool actual: 17+ Groq + 21+ DeepSeek — se auto-expande sin redeploy
- Fallback: Groq → DeepSeek → 503

## Endpoints
- `POST /api/ask` — `{message, max_tokens}` → `{respuesta, via, pool}`
- `GET /api/health` — pool size actual
- `GET /api/pool` — fuerza refresh del cache

## Para actualizar oracle_relay_url
```bash
curl -X POST https://tpfiybpguuxskitszhmk.supabase.co/rest/v1/relay_config?on_conflict=clave \
  -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
  -H "Content-Type: application/json" -H "Prefer: resolution=merge-duplicates" \
  -d '[{"clave":"oracle_relay_url","valor":"https://oracle-ask-v26-miu4.vercel.app/api/ask"}]'
```

ρ(x)>0
