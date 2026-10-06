# LLM Key Prober

El ecosistema NO debe etiquetar manualmente claves LLM. Debe probar el endpoint real.

## Principio

```
NO: prefijo -> etiqueta -> asignar endpoint
SI: clave -> probar endpoints -> el resultado manda -> registrar
```

## Prefijos conocidos (punto de partida, no verdad definitiva)

| Prefijo | Proveedor probable | Endpoint a probar |
|---|---|---|
| `AQ.` | Google AI Studio (Gemini) | generativelanguage.googleapis.com |
| `sk-ant-` | Anthropic | api.anthropic.com |
| `nvapi-` | NVIDIA NIM | integrate.api.nvidia.com |
| `sk-or-v1-` | OpenRouter | openrouter.ai |
| `rqsty-sk-` | Requesty | router.requesty.ai |
| `gsk_` | Groq | api.groq.com |
| `sk-` (generico) | DeepSeek / Together / OpenAI | probar en orden |

Nota: `AQ.` es Google AI Studio — NO Anthropic (que usa `sk-ant-`).

## Cómo disparar desde el ecosistema

```bash
# El ecosistema dispara con GITHUB_PAT de relay_config:
curl -X POST https://api.github.com/repos/Jaime393/miu-ecosistema/actions/workflows/llm-key-prober.yml/dispatches \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Content-Type: application/json" \
  -d '{"ref":"main","inputs":{"keys_json":"[\"sk-xxx\",\"nvapi-yyy\"]"}}'
```

O via `repository_dispatch`:
```json
{ "event_type": "probe-llm-keys", "client_payload": { "keys_json": "[...]" } }
```

## Resultado

`observabilidad/key_registry.json` — actualizado por cada ejecucion.
Cada entrada tiene: `provider`, `endpoint`, `models`, `valid`, `latency_ms`.

El ecosistema lee esto para actualizar `relay_config` con los endpoints correctos.

## Módulo TypeScript compartido

`supabase/functions/_shared/provider_probe.ts` — importable desde cualquier EF:
```typescript
import { probeKey, probeBatch } from '../_shared/provider_probe.ts'
const result = await probeKey(someKey)
// result.provider es el proveedor real, verificado
```
