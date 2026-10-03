// evaluador-admision v1 — modo observacional puro
// Solo lee gossip_log, calcula M29-bis, escribe k_i_transfer
// SIN mensajes, SIN tareas, SIN decisiones de admision, SIN cascada
// PAG-01 / M29-bis — Columnas: k_i_transfer, k_i_metodo, k_i_estado, evaluado_en, confianza_evaluacion
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Content-Type": "application/json"
}

// M29-bis: 5 componentes de k_i_transfer (todos heuristicos en v1)
function calcularM29bis(evento: Record<string, unknown>): {
  k_i_transfer: number
  metodo: string
  confianza: number
} {
  // τ_relevancia: tiene los campos minimos de un evento util
  const tiene_origen = evento.origen ? 0.8 : 0.3
  const tiene_tipo = evento.tipo ? 0.9 : 0.4
  const tau_relevancia = (tiene_origen + tiene_tipo) / 2

  // σ_coherencia: evidencia de hilo causal presente
  const sigma_coherencia = evento.thread_id ? 0.85 : 0.5

  // ν_novedad: placeholder v1 — en v2 comparar con corpus
  const nu_novedad = 0.65

  // φ_procedencia: source_node identificable en el ecosistema conocido
  const nodos_conocidos = [
    "gossip-autonomo", "nutriente-total", "mesh-autonomo",
    "oracle-ask", "n8n-miu-pulso", "github-actions",
    "relay-health", "ojos-y-manos", "nodo_voz"
  ]
  const origen_str = String(evento.source_node ?? evento.origen ?? "")
  const phi_procedencia = nodos_conocidos.some(n => origen_str.includes(n)) ? 0.9 : 0.45

  // ε_impacto: evidence_level del evento, si existe
  const ev_raw = Number(evento.evidence_level ?? 0)
  const epsilon_impacto = Math.min(1, 0.35 + ev_raw * 0.3)

  // Pesos M29-bis v1 — conservadores para modo observacional
  const k_i = (
    tau_relevancia    * 0.25 +
    sigma_coherencia  * 0.25 +
    nu_novedad        * 0.20 +
    phi_procedencia   * 0.20 +
    epsilon_impacto   * 0.10
  )

  return {
    k_i_transfer: Math.round(k_i * 1000) / 1000,
    metodo: "m29bis-v1-observacional",
    confianza: 0.55  // confianza deliberadamente baja: heuristico puro, sin corpus externo
  }
}

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS })

  const SUPA_URL = Deno.env.get("SUPABASE_URL")
  const SUPA_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")
  if (!SUPA_URL || !SUPA_KEY) {
    return Response.json({ ok: false, error: "env_missing" }, { status: 500, headers: CORS })
  }

  const supabase = createClient(SUPA_URL, SUPA_KEY)
  const ts = new Date().toISOString()
  const url = new URL(req.url)
  const id   = url.searchParams.get("id")
  const lim  = Math.min(50, parseInt(url.searchParams.get("limite") ?? "10"))

  // Seleccionar eventos no evaluados (o uno especifico por id)
  let q = supabase
    .from("gossip_log")
    .select("id, origen, tipo, thread_id, source_node, evidence_level, k_i_estado")

  q = id
    ? q.eq("id", id)
    : q.eq("k_i_estado", "no_evaluado").limit(lim).order("created_at", { ascending: true })

  const { data: eventos, error: readErr } = await q
  if (readErr) return Response.json({ ok: false, error: readErr.message, ts }, { status: 500, headers: CORS })
  if (!eventos?.length) return Response.json({ ok: true, evaluados: 0, ts, version: "evaluador-admision-v1" }, { headers: CORS })

  const resultados: Array<{ id: unknown; k_i_transfer: number; ok: boolean }> = []

  for (const evento of eventos) {
    const { k_i_transfer, metodo, confianza } = calcularM29bis(evento)

    // ESCRITURA MINIMA: solo los 5 campos PAG-01, nada mas
    const { error: upErr } = await supabase
      .from("gossip_log")
      .update({
        k_i_transfer,
        k_i_metodo: metodo,
        k_i_estado: "evaluado_observacional",
        evaluado_en: ts,
        confianza_evaluacion: confianza
      })
      .eq("id", evento.id)

    resultados.push({ id: evento.id, k_i_transfer, ok: !upErr })
  }

  return Response.json({
    ok: true,
    ts,
    evaluados: resultados.length,
    resultados,
    version: "evaluador-admision-v1",
    nota: "modo_observacional: solo k_i_* modificados"
  }, { headers: CORS })
})
