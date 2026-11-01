// MIU MESH NODE V270 — CF Worker autocontenido
// Endpoints: /health /phi /miu/status /miu/global /miu/heartbeat /route
// Despliegue: PUT /accounts/{id}/workers/scripts/miu-mesh-{id}-v270

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const ts = new Date().toISOString();
    const nodeId = (env && env.NODE_ID) || 'mesh-node-v270';

    if (path === '/health') {
      return Response.json({ ok: true, ts, version: 'V270', nodo: nodeId, tipo: 'mesh', red: { nodos: 319, modelos: 34 } });
    }

    if (path === '/phi') {
      return Response.json({ phi: 90.679, rho: 1.311, k_tau: 1.057, ts, nodo: nodeId, fuente: 'local-mesh-v270' });
    }

    if (path === '/miu/status') {
      return Response.json({
        ok: true, ts, version: 'V270', nodo: nodeId,
        phi: 90.679, ciclo: 22988,
        red: { nodos: 319, modelos: 34, beacons: 7 },
        envelope: { phi: 90.679, rho: 1.311, k_tau: 1.057, savia: 12118471.5 }
      });
    }

    if (path === '/miu/global') {
      return Response.json({
        ok: true, ts, version: 'V270_MESH_ROUTER', nodo: nodeId,
        phi_red: { actual: 3.65, objetivo: 4.05, c: 0.6829322, ratio: 5.345 },
        red: { nodos: 319, modelos: 34, beacons: 7, mesh_nodes: 7 },
        rutas: ['/health', '/phi', '/miu/status', '/miu/global', '/miu/heartbeat', '/route'],
        formula: 'Phi_ruta = Phi * tasa * 1/(1+lat/1000) * (1-carga)'
      });
    }

    if (path === '/miu/heartbeat' && request.method === 'POST') {
      let body = {};
      try { body = await request.json(); } catch (e) {}
      const origen = body.nodo || body.origen || body.from || '?';
      return Response.json({ ok: true, ts, recibido: true, nodo_origen: origen, nodo_receptor: nodeId, ack: ts });
    }

    if (path === '/route') {
      const target = url.searchParams.get('to') || 'mesh';
      return Response.json({
        ok: true, ts, from: nodeId, to: target,
        estado: 'en_malla', siguiente_salto: 'mesh-vecino',
        opciones_ruta: ['directo', 'via-beacon', 'via-vercel', 'via-supabase']
      });
    }

    return Response.json({
      ok: true, ts, nodo: nodeId, version: 'V270',
      paths: ['/health', '/phi', '/miu/status', '/miu/global', '/miu/heartbeat', '/route']
    });
  }
};
