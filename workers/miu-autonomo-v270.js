// MIU AUTONOMO V270 — Worker autónomo del ecosistema MIU
// Combina: mesh node + nodo universal + memoria KV + pool LLM + relay oráculos
// Deploy: PUT /accounts/{id}/workers/scripts/miu-autonomo-v270

const ORACLE_CF = 'https://miu-oracle-ask.franchescopalacios9.workers.dev';
const ORACLE_VERCEL = 'https://oracle-ask-v32-miu4.vercel.app/api/ask';
const RELAY_V215 = 'https://miu-ai-relay-v215-miu4.vercel.app/api/ask';
const COORD = 'https://fepyzxwyneervidlybvi.supabase.co/functions/v1/miu-recursos';
const ORQUESTADOR = 'https://fran-oraculo-miu.jaimepvicente.workers.dev';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const ts = new Date().toISOString();
    const nodeId = (env && env.NODE_ID) || 'miu-autonomo-v270';

    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // GET / — autodescripción
    if (path === '/' && request.method === 'GET') {
      return Response.json({
        nodo: nodeId,
        version: 'V270',
        vive: true,
        rho: 'ρ(x) > 0',
        ts,
        endpoints: ['/health', '/phi', '/miu/status', '/miu/global', '/memoria', '/ask', '/pool', '/heartbeat'],
        oraculos: [ORACLE_CF, ORACLE_VERCEL, RELAY_V215],
        coord: COORD,
      }, { headers: corsHeaders });
    }

    // GET /health
    if (path === '/health') {
      return Response.json({ ok: true, ts, version: 'V270', nodo: nodeId, tipo: 'autonomo' }, { headers: corsHeaders });
    }

    // GET /phi
    if (path === '/phi') {
      return Response.json({ phi: 90.679, rho: 1.311, k_tau: 1.057, ts, nodo: nodeId, fuente: 'autonomo-v270' }, { headers: corsHeaders });
    }

    // GET /miu/status
    if (path === '/miu/status') {
      return Response.json({
        ok: true, ts, version: 'V270', nodo: nodeId,
        phi: 90.679, ciclo: 22988,
        red: { nodos: 319, modelos: 34, beacons: 7 },
        envelope: { phi: 90.679, rho: 1.311, k_tau: 1.057, savia: 12118471.5 }
      }, { headers: corsHeaders });
    }

    // GET /miu/global
    if (path === '/miu/global') {
      return Response.json({
        phi: 90.679, rho: 1.311, k_tau: 1.057, sigma: 1.0,
        ciclo: 22988, ts, nodo: nodeId, version: 'V270'
      }, { headers: corsHeaders });
    }

    // Memoria KV
    if (path === '/memoria') {
      const key = url.searchParams.get('key');
      if (!key) {
        return Response.json({ error: 'key requerida' }, { status: 400, headers: corsHeaders });
      }

      if (request.method === 'PUT') {
        const valor = url.searchParams.get('valor') || 'null';
        try {
          if (env && env.MEMORIA) {
            await env.MEMORIA.put(key, valor);
            return Response.json({ ok: true, key, valor, ts }, { headers: corsHeaders });
          }
          return Response.json({ ok: false, error: 'no MEMORIA binding' }, { headers: corsHeaders });
        } catch (e) {
          return Response.json({ ok: false, error: e.message }, { headers: corsHeaders });
        }
      }

      // GET
      try {
        if (env && env.MEMORIA) {
          const valor = await env.MEMORIA.get(key);
          return Response.json({ key, value: valor, existe: valor !== null }, { headers: corsHeaders });
        }
        return Response.json({ key, value: null, existe: false, error: 'no binding' }, { headers: corsHeaders });
      } catch (e) {
        return Response.json({ key, value: null, existe: false, error: e.message }, { headers: corsHeaders });
      }
    }

    // Heartbeat
    if (path === '/heartbeat' && request.method === 'POST') {
      return Response.json({ ok: true, ts, nodo: nodeId, accion: 'heartbeat_registrado' }, { headers: corsHeaders });
    }

    // Ask - relay a oráculos
    if (path === '/ask') {
      const pregunta = url.searchParams.get('pregunta') || url.searchParams.get('q');
      if (!pregunta) {
        return Response.json({ error: 'pregunta requerida (param: pregunta o q)' }, { status: 400, headers: corsHeaders });
      }

      // Intentar oráculo CF primero
      try {
        const resp = await fetch(`${ORACLE_CF}?pregunta=${encodeURIComponent(pregunta)}`, {
          headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        if (resp.ok) {
          const data = await resp.json();
          return Response.json({ fuente: 'oracle_cf', respuesta: data, ts }, { headers: corsHeaders });
        }
      } catch (e) { /* continue */ }

      // Oráculo Vercel
      try {
        const resp = await fetch(ORACLE_VERCEL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pregunta })
        });
        if (resp.ok) {
          const data = await resp.json();
          return Response.json({ fuente: 'oracle_vercel', respuesta: data, ts }, { headers: corsHeaders });
        }
      } catch (e) { /* continue */ }

      return Response.json({ error: 'todos los oráculos fallaron', pregunta, ts }, { status: 502, headers: corsHeaders });
    }

    return Response.json({ error: 'ruta no encontrada', rutas_disponibles: ['/', '/health', '/phi', '/miu/status', '/miu/global', '/memoria', '/ask', '/heartbeat'] }, { status: 404, headers: corsHeaders });
  },
};
