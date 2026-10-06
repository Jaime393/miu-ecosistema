/**
 * provider_probe.ts — Capacidad de autoidentificacion de proveedores LLM
 * El ecosistema invoca esto; NUNCA confiar en prefijos como verdad definitiva.
 * Prueba el endpoint real y deja que la respuesta dicte el proveedor.
 *
 * Uso desde cualquier EF:
 *   import { probeKey, PROVIDERS } from '../_shared/provider_probe.ts'
 *   const result = await probeKey(someKey)
 *   // result.provider, result.endpoint, result.models, result.valid
 */

export interface ProbeResult {
  key_prefix: string
  provider: string | null
  endpoint: string | null
  models: string[]
  valid: boolean
  error?: string
  latency_ms?: number
  raw_status?: number
}

/** Proveedores conocidos en orden de prueba por prefijo */
export const PROVIDERS: Record<string, { provider: string; endpoints: string[]; auth: 'bearer' | 'x-api-key' | 'query' }[]> = {
  'AQ.': [
    // Google AI Studio — Gemini
    { provider: 'google_ai_studio', endpoints: ['https://generativelanguage.googleapis.com/v1beta/models'], auth: 'query' }
  ],
  'sk-ant-': [
    { provider: 'anthropic', endpoints: ['https://api.anthropic.com/v1/models'], auth: 'x-api-key' }
  ],
  'nvapi-': [
    { provider: 'nvidia_nim', endpoints: ['https://integrate.api.nvidia.com/v1/models'], auth: 'bearer' }
  ],
  'sk-or-v1-': [
    { provider: 'openrouter', endpoints: ['https://openrouter.ai/api/v1/models'], auth: 'bearer' }
  ],
  'rqsty-sk-': [
    { provider: 'requesty', endpoints: ['https://router.requesty.ai/v1/models'], auth: 'bearer' }
  ],
  'gsk_': [
    { provider: 'groq', endpoints: ['https://api.groq.com/openai/v1/models'], auth: 'bearer' }
  ],
  'sk-': [
    // Prefijo ambiguo — probar en orden de probabilidad
    { provider: 'deepseek', endpoints: ['https://api.deepseek.com/v1/models'], auth: 'bearer' },
    { provider: 'together', endpoints: ['https://api.together.xyz/v1/models'], auth: 'bearer' },
    { provider: 'perplexity', endpoints: ['https://api.perplexity.ai/models'], auth: 'bearer' },
    { provider: 'openai', endpoints: ['https://api.openai.com/v1/models'], auth: 'bearer' }
  ]
}

/** Detecta el bloque de proveedores a intentar segun prefijo */
function getCandidates(key: string) {
  for (const [prefix, candidates] of Object.entries(PROVIDERS)) {
    if (key.startsWith(prefix)) return candidates
  }
  // Sin prefijo reconocido — intentar todo
  return Object.values(PROVIDERS).flat()
}

/** Prueba una clave contra su endpoint real */
export async function probeKey(key: string, timeoutMs = 8000): Promise<ProbeResult> {
  const prefix = key.slice(0, 10)
  const candidates = getCandidates(key)

  for (const { provider, endpoints, auth } of candidates) {
    for (const endpoint of endpoints) {
      const t0 = Date.now()
      try {
        let url = endpoint
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }

        if (auth === 'bearer') headers['Authorization'] = `Bearer ${key}`
        else if (auth === 'x-api-key') headers['x-api-key'] = key
        else if (auth === 'query') url = `${endpoint}?key=${key}`

        const res = await fetch(url, { headers, signal: AbortSignal.timeout(timeoutMs) })
        const latency_ms = Date.now() - t0

        if (res.ok) {
          const data = await res.json().catch(() => ({}))
          // Extraer lista de modelos segun formato del proveedor
          const models = (
            data.models?.map((m: Record<string, unknown>) => m.id || m.name) ??
            data.data?.map((m: Record<string, unknown>) => m.id) ??
            []
          ).slice(0, 5) as string[]

          return { key_prefix: prefix, provider, endpoint, models, valid: true, latency_ms, raw_status: res.status }
        }

        // 401/403 = clave invalida para este proveedor; seguir intentando
        if (res.status === 401 || res.status === 403) continue
        // Otro error = proveedor respondio pero hay problema
        if (res.status >= 400) continue
      } catch (_) {
        // timeout o red — seguir
      }
    }
  }

  return { key_prefix: prefix, provider: null, endpoint: null, models: [], valid: false, error: 'no_provider_accepted_key' }
}

/** Prueba un lote de claves en paralelo */
export async function probeBatch(keys: string[]): Promise<ProbeResult[]> {
  return Promise.all(keys.map(k => probeKey(k)))
}
