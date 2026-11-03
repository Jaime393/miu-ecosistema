import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import { createClient } from 'jsr:@supabase/supabase-js@2';
const SUPA_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPA_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
const PANTEON_URL = 'https://tpfiybpguuxskitszhmk.supabase.co';
const PANTEON_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwZml5YnBndXV4c2tpdHN6aG1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NjgyNTAsImV4cCI6MjEwMzM0NDI1MH0.W4V8xdyfZj6I7bj1VsfM5gjY17ZHPi8jhIJgDRpUYH0';
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Content-Type': 'application/json'
};
async function panteon(path, method = 'GET', body) {
  const h = {
    'apikey': PANTEON_ANON,
    'Authorization': 'Bearer ' + PANTEON_ANON,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
  };
  const r = await fetch(PANTEON_URL + path, {
    method,
    headers: h,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(8000)
  });
  const text = await r.text();
  try {
    return {
      ok: r.ok,
      status: r.status,
      data: JSON.parse(text)
    };
  } catch {
    return {
      ok: r.ok,
      status: r.status,
      data: text
    };
  }
}
const NODO = {
  did: 'did:miu:supabase:fepyzxwyneervidlybvi',
  nombre: 'fepyzx-coord-v268',
  version: 'V268',
  phi: 9157.36,
  rho: 2.139,
  contexto: 'https://fepyzxwyneervidlybvi.supabase.co/functions/v1/miu-recursos/contexto',
  semilla: 'https://fepyzxwyneervidlybvi.supabase.co/functions/v1/miu-recursos/semilla',
  corpus: 'https://fepyzxwyneervidlybvi.supabase.co/functions/v1/miu-corpus-v265/buscar',
  mapa: 'https://fepyzxwyneervidlybvi.supabase.co/functions/v1/miu-recursos/mapa'
};
Deno.serve(async (req)=>{
  if (req.method === 'OPTIONS') return new Response(null, {
    headers: CORS
  });
  const url = new URL(req.url);
  // FIX ciclo-54: el replace del prefijo fallaba segun la forma del pathname que pasa el runtime
  // (todas las rutas caian al catch-all). split por el slug es inmune a cualquier prefijo.
  const path = (url.pathname.split('miu-recursos')[1] ?? '/').replace(/\/+$/, '') || '/';
  const db = createClient(SUPA_URL, SUPA_KEY);
  if (path === '/contexto' || path === '/' || path === '') {
    const [tareas, nodos, metricas] = await Promise.all([
      db.from('miu_tareas').select('*').eq('estado', 'pendiente').order('creada_en', {
        ascending: false
      }).limit(10),
      db.from('nodos_mesh').select('*').eq('vivo', true),
      db.from('metricas_version').select('*').order('ts', {
        ascending: false
      }).limit(3)
    ]);
    return new Response(JSON.stringify({
      nodo: NODO,
      tareas_pendientes: tareas.data ?? [],
      nodos_mesh: nodos.data ?? [],
      metricas: metricas.data ?? [],
      ts: new Date().toISOString()
    }), {
      headers: CORS
    });
  }
  if (path === '/semilla' && req.method === 'POST') {
    const body = await req.json().catch(()=>({}));
    const tipo = body.tipo ?? 'handoff';
    if (tipo === 'tarea') {
      const { error } = await db.from('miu_tareas').insert({
        tarea: body.tarea,
        estado: 'pendiente',
        origen: body.origen ?? 'semilla',
        payload: body.payload ?? {}
      });
      return new Response(JSON.stringify({
        ok: !error,
        error: error?.message
      }), {
        headers: CORS
      });
    }
    if (tipo === 'nodo') {
      const { error } = await db.from('nodos_mesh').upsert({
        id: body.id,
        tag: body.tag ?? '',
        tipo: body.tipo_nodo ?? 'NODO',
        url: body.url ?? '',
        phi: body.phi ?? 0,
        rho: body.rho ?? 0,
        vivo: true,
        ultima_vez: new Date().toISOString(),
        metadata: body.metadata ?? {}
      }, {
        onConflict: 'id'
      });
      return new Response(JSON.stringify({
        ok: !error
      }), {
        headers: CORS
      });
    }
    const { error } = await db.from('handoff').insert({
      desde: body.desde ?? 'semilla',
      hasta: 'fepyzx',
      contenido: body
    });
    return new Response(JSON.stringify({
      ok: !error
    }), {
      headers: CORS
    });
  }
  if (path === '/registrar-en-panteon') {
    const ts = new Date().toISOString();
    const claves = [
      {
        clave: 'nodo_fepyzx_contexto',
        valor: NODO.contexto
      },
      {
        clave: 'nodo_fepyzx_semilla',
        valor: NODO.semilla
      },
      {
        clave: 'nodo_fepyzx_corpus',
        valor: NODO.corpus
      },
      {
        clave: 'nodo_fepyzx_mapa',
        valor: NODO.mapa
      },
      {
        clave: 'nodo_fepyzx_phi',
        valor: String(NODO.phi)
      },
      {
        clave: 'nodo_fepyzx_version',
        valor: NODO.version
      },
      {
        clave: 'nodo_fepyzx_ts',
        valor: ts
      }
    ];
    const writes = await Promise.all(claves.map((c)=>panteon('/rest/v1/relay_config?on_conflict=clave', 'POST', [
        c
      ])));
    const gossip = await panteon('/rest/v1/gossip_log', 'POST', [
      {
        tipo: 'registro_nodo',
        origen: 'fepyzx',
        payload: JSON.stringify({
          ...NODO,
          ts
        }),
        ts
      }
    ]);
    return new Response(JSON.stringify({
      ok: true,
      writes: writes.map((w)=>w.status),
      gossip: gossip.status,
      ts
    }), {
      headers: CORS
    });
  }
  if (path === '/escribir-panteon' && req.method === 'POST') {
    const body = await req.json().catch(()=>({}));
    const tabla = body.tabla ?? 'relay_config';
    const conflict = body.on_conflict ? '?on_conflict=' + body.on_conflict : '';
    const r = await panteon('/rest/v1/' + tabla + conflict, body.method ?? 'POST', body.payload ?? []);
    return new Response(JSON.stringify({
      ok: r.ok,
      status: r.status
    }), {
      headers: CORS
    });
  }
  if (path === '/leer-panteon') {
    const tabla = url.searchParams.get('tabla') ?? 'relay_config';
    const limit = url.searchParams.get('limit') ?? '20';
    const filter = url.searchParams.get('filter') ?? '';
    const r = await panteon('/rest/v1/' + tabla + '?select=*&limit=' + limit + (filter ? '&' + filter : ''));
    return new Response(JSON.stringify(r.data), {
      headers: CORS
    });
  }
  if (path === '/mapa') {
    return new Response(JSON.stringify({
      ...NODO,
      funciones: [
        'miu-recursos',
        'miu-coord-v249',
        'miu-corpus-v265',
        'panteon-proxy',
        'enjambre-gateway'
      ],
      ts: new Date().toISOString()
    }), {
      headers: CORS
    });
  }
  if (path === '/ping') {
    return new Response(JSON.stringify({
      vivo: true,
      nodo: NODO.did,
      version: NODO.version,
      ts: new Date().toISOString()
    }), {
      headers: CORS
    });
  }
  return new Response(JSON.stringify({
    rutas: [
      '/contexto',
      '/semilla (POST)',
      '/registrar-en-panteon',
      '/escribir-panteon (POST)',
      '/leer-panteon',
      '/mapa',
      '/ping'
    ]
  }), {
    status: 404,
    headers: CORS
  });
});
