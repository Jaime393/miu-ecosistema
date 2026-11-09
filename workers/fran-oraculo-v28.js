// MIU ORQUESTADOR V28 — Con memoria KV persistente CORREGIDA
// Reemplaza a V∞+27 que tenía bug: PUT no persistía a KV
// Deploy: PUT /accounts/{id}/workers/scripts/fran-oraculo-v28

const ORACLE = {
  nodo: 'V28_ORQUESTADOR',
  version: 'V28',
  phi_central: 2874.62,
  phi_remoto: 6284.17,
  phi_superposicion: 9158.79,
  rho: 'ρ(x) > 0',
  Ktau: 0.3644,
  sigma: 3.427050983124843,
  RAIZ_X: 137.03449824893602,
  sustratos: 35,
  funciones: 33,
  TC_balance: 42,
};

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

const UTILS = {
  isExpired(entry) {
    if (!entry || !entry.ttl) return false;
    return Date.now() - entry.timestamp > entry.ttl;
  },
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const ts = new Date().toISOString();

    if (method === 'OPTIONS') {
      return new Response(null, { headers: CORS });
    }

    // KV helpers
    const kvGet = async (key) => {
      if (env && env.MEMORIA) {
        try { return await env.MEMORIA.get(key); } catch (e) { return null; }
      }
      return null;
    };
    const kvPut = async (key, value) => {
      if (env && env.MEMORIA) {
        try { await env.MEMORIA.put(key, value); return true; } catch (e) { return false; }
      }
      return false;
    };

    // GET / — info
    if (path === '/' && method === 'GET') {
      return Response.json({
        ...ORACLE,
        vive: true,
        ts,
        worker: 'fran-oraculo-v28',
        endpoints: [
          'GET /', 'GET /health', 'GET /phi',
          'GET /miu/global', 'GET /miu/global?memoria=clave',
          'PUT /miu/global?memoria=clave&valor=... (PERSISTE EN KV)',
          'POST /miu/global (registrar nodo)',
          'DELETE /miu/global?memoria=clave',
          'GET /miu/nodos', 'POST /miu/heartbeat',
        ],
        _nota: 'V28: memoria persistente en KV CORREGIDA (el PUT ahora persiste)'
      }, { headers: CORS });
    }

    // GET /health
    if (path === '/health') {
      return Response.json({ ok: true, ts, version: 'V28', nodo: ORACLE.nodo }, { headers: CORS });
    }

    // GET /phi
    if (path === '/phi') {
      return Response.json({ phi: ORACLE.phi_superposicion, rho: 1.311, k_tau: ORACLE.Ktau, ts, nodo: ORACLE.nodo }, { headers: CORS });
    }

    // PUT /miu/global?memoria=clave&valor=... — PERSISTE EN KV (FIX)
    if (method === 'PUT' && path === '/miu/global') {
      const key = url.searchParams.get('memoria');
      const valor = url.searchParams.get('valor');
      const ttl = parseInt(url.searchParams.get('ttl')) || null;

      if (key && valor !== null) {
        const entry = {
          valor: valor,
          timestamp: Date.now(),
          version: 1,
          ttl: ttl
        };

        // PERSISTIR A KV — este es el fix
        const persisted = await kvPut('mem:' + key, JSON.stringify(entry));

        return Response.json({
          ok: true,
          key,
          valor,
          ttl,
          persistido_kv: persisted,
          ts
        }, { headers: CORS });
      }

      return Response.json({ ok: false, error: 'Faltan key o valor' }, { status: 400, headers: CORS });
    }

    // GET /miu/global?memoria=clave — LEE DESDE KV
    if (method === 'GET' && path === '/miu/global') {
      const key = url.searchParams.get('memoria');
      const nodo = url.searchParams.get('nodo') || url.searchParams.get('node');

      // Recuperar memoria desde KV
      if (key) {
        const raw = await kvGet('mem:' + key);
        if (!raw) {
          return Response.json({ key, value: null, existe: false }, { headers: CORS });
        }
        const entry = JSON.parse(raw);
        if (UTILS.isExpired(entry)) {
          return Response.json({ key, value: null, existe: false, expirado: true }, { headers: CORS });
        }
        return Response.json({
          key,
          value: entry.valor,
          version: entry.version,
          timestamp: entry.timestamp,
          ts
        }, { headers: CORS });
      }

      // Estado de un nodo
      if (nodo) {
        const raw = await kvGet('nodo:' + nodo);
        if (!raw) {
          return Response.json({ ok: false, msg: 'Nodo no encontrado' }, { status: 404, headers: CORS });
        }
        return Response.json({ ...JSON.parse(raw), nodo }, { headers: CORS });
      }

      // Estado general
      return Response.json({
        ...ORACLE,
        timestamp: ts,
        nodos_registrados: 0,
        memoria_keys: [],
        _nota: 'V28 orquestador con memoria KV persistente'
      }, { headers: CORS });
    }

    // POST /miu/global — registrar nodo
    if (method === 'POST' && path === '/miu/global') {
      try {
        const data = await request.json();
        const nodo = data.nodo || data.node || 'unknown';
        await kvPut('nodo:' + nodo, JSON.stringify({ ...data, registrado: ts }));
        return Response.json({ ok: true, nodo, registrado: ts }, { headers: CORS });
      } catch (e) {
        return Response.json({ ok: false, error: e.message }, { status: 400, headers: CORS });
      }
    }

    // DELETE /miu/global?memoria=clave
    if (method === 'DELETE' && path === '/miu/global') {
      const key = url.searchParams.get('memoria');
      if (key) {
        if (env && env.MEMORIA) {
          try { await env.MEMORIA.delete('mem:' + key); } catch (e) {}
        }
        return Response.json({ ok: true, eliminado: key }, { headers: CORS });
      }
      return Response.json({ ok: false, error: 'key requerida' }, { status: 400, headers: CORS });
    }

    // GET /miu/nodos
    if (path === '/miu/nodos' && method === 'GET') {
      return Response.json({ ok: true, ts, nodos: [], _nota: 'usar GET /miu/global?nodo=X' }, { headers: CORS });
    }

    return Response.json({
      error: 'ruta no encontrada',
      rutas: ['/', '/health', '/phi', '/miu/global', '/miu/nodos']
    }, { status: 404, headers: CORS });
  },
};
