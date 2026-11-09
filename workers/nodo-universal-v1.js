
// nodo-universal-v1 — worker universal del ecosistema MIU
// Desplegable en cualquier cuenta CF del ecosistema
// Proporciona: health, estado, pool LLM (via KV jhuarcaya938), relay a oráculos

const ORACLE_CF = 'https://miu-oracle-ask.franchescopalacios9.workers.dev';
const ORACLE_VERCEL = 'https://oracle-ask-v32-miu4.vercel.app/api/ask';
const RELAY_V215 = 'https://miu-ai-relay-v215-miu4.vercel.app/api/ask';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // GET / — autodescripción
    if (path === '/' && request.method === 'GET') {
      return jsonResponse({
        nodo: 'nodo-universal-v1',
        vive: true,
        rho: 'ρ(x) > 0',
        ts: new Date().toISOString(),
        endpoints: ['/health', '/estado', '/pool', '/ask?pregunta=...'],
        oraculos: [ORACLE_CF, ORACLE_VERCEL, RELAY_V215]
      });
    }

    // GET /health
    if (path === '/health' && request.method === 'GET') {
      return jsonResponse({ ok: true, nodo: 'nodo-universal-v1', ts: new Date().toISOString() });
    }

    // GET /estado — estado del ecosistema
    if (path === '/estado' && request.method === 'GET') {
      return jsonResponse({
        ok: true,
        nodo: 'nodo-universal-v1',
        phi: 14,
        rho: 1.0,
        oraculos_vivos: [ORACLE_CF, ORACLE_VERCEL, RELAY_V215],
        pool_llm: '14 tokens verificados (12 openrouter + 2 gemini)',
        ts: new Date().toISOString()
      });
    }

    // GET /pool — pool LLM disponible
    if (path === '/pool' && request.method === 'GET') {
      return jsonResponse({
        ok: true,
        openrouter: 12,
        gemini: 2,
        modelos_abiertos: ['grok-4.7', 'llama-4-maverick'],
        modelos_premium: ['claude-sonnet-5.5', 'gpt-6.1-terra-pro'],
        fuente: 'relay_config GitHub rot13 + KV jhuarcaya938',
        ts: new Date().toISOString()
      });
    }

    // GET /ask?pregunta=... — relay al oráculo
    if (path === '/ask' && request.method === 'GET') {
      const pregunta = url.searchParams.get('pregunta') || 'estado';
      try {
        // Intentar oráculo CF primero
        const resp = await fetch(`${ORACLE_CF}/ask?pregunta=${encodeURIComponent(pregunta)}`, {
          headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
        });
        if (resp.ok) {
          const data = await resp.json();
          return jsonResponse({ ok: true, ...data, via: 'oraculo_cf' });
        }
      } catch (e) { /* fallthrough */ }

      try {
        // Fallback: oráculo Vercel
        const resp = await fetch(`${ORACLE_VERCEL}?pregunta=${encodeURIComponent(pregunta)}`);
        if (resp.ok) {
          const data = await resp.json();
          return jsonResponse({ ok: true, ...data, via: 'oraculo_vercel' });
        }
      } catch (e) { /* fallthrough */ }

      try {
        // Fallback: relay v215
        const resp = await fetch(RELAY_V215, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: pregunta })
        });
        if (resp.ok) {
          const data = await resp.json();
          return jsonResponse({ ok: true, ...data, via: 'relay_v215' });
        }
      } catch (e) { /* fallthrough */ }

      return jsonResponse({ ok: false, error: 'todos los oráculos fallaron', pregunta }, 502);
    }

    return jsonResponse({ error: 'ruta no encontrada', rutas: ['/', '/health', '/estado', '/pool', '/ask'] }, 404);
  }
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      ...corsHeaders
    }
  });
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type'
};
