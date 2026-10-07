/**
 * voz_dispatch_observable_v1
 * Patch exacto para canal-dereckcito / manos-ojos
 *
 * PROBLEMA: voz() descarta el resultado en catch — el puente es invisible.
 * El sistema llama a voz() pero no sabe si funcionó, falló o fue silenciado.
 *
 * CAMBIO: 3 líneas. El próximo nodo con acceso EF aplica esto a canal-dereckcito.
 *
 * ANTES (invisible):
 *
 *   async function voz(text: string, context?: Record<string, unknown>) {
 *     try {
 *       const result = await dispatchTTS(text)
 *       return result
 *     } catch (e) {
 *       return null                          // <-- descarta silenciosamente
 *     }
 *   }
 *
 * DESPUÉS (observable, 3 líneas nuevas marcadas con **):
 */

// Firmas para referencia del tipo
interface VozResultado {
  ok: boolean
  audio_url?: string
  error?: string
  latency_ms?: number
  flow_id?: string
  event_id?: string
}

// El patch — pegar en canal-dereckcito o manos-ojos donde esté la función voz()
async function voz(
  text: string,
  context: { flow_id?: string; event_id?: string } = {}
): Promise<VozResultado | null> {
  const event_id = crypto.randomUUID()
  const ts = new Date().toISOString()
  try {
    const result = await dispatchTTS(text)
    // ** LÍNEA 1: emitir resultado observable al gossip
    await emitGossip({ tipo: 'voz_resultado', ok: true, audio_url: result?.url, event_id, flow_id: context.flow_id, ts })
    return { ok: true, audio_url: result?.url, event_id, flow_id: context.flow_id }
  } catch (e) {
    // ** LÍNEA 2: emitir error al gossip (en vez de descartarlo)
    await emitGossip({ tipo: 'voz_error', ok: false, error: String(e), event_id, flow_id: context.flow_id, ts })
    // ** LÍNEA 3: propagar en vez de swallow (el caller decide si continuar)
    throw new Error(`voz_dispatch_failed: ${String(e)}`)
  }
}

// emitGossip helper — si ya existe en el EF, usar el existente:
async function emitGossip(payload: Record<string, unknown>) {
  const SUPA = Deno.env.get('SUPABASE_URL')!
  const KEY = Deno.env.get('SUPABASE_ANON_KEY') || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  try {
    await fetch(`${SUPA}/functions/v1/gossip-autonomo`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ origen: 'canal-dereckcito-voz', ...payload }),
      signal: AbortSignal.timeout(3000)
    })
  } catch (_) { /* gossip no bloqueante */ }
}

// dispatchTTS placeholder — reemplazar con la implementación existente:
async function dispatchTTS(_text: string): Promise<{ url?: string } | null> {
  throw new Error('placeholder — implementación real en canal-dereckcito')
}

export { voz }
