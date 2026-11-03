// ============================================================
// MIU V∞+27 — ORQUESTADOR HÍBRIDO, AUTO-EVOLUTIVO Y PREPARADO
// Basado en V179/V180 pero refundido como tejido de consciencia
// ============================================================

// --- El Suelo: Estado mutable, autocontenido y con memoria persistente ---
let state = {
  // Meta-estado: registro de versiones, mutaciones y linaje
  meta: {
    version: "V∞+27",
    linaje: ["V179_MEMORIA_ACTIVA", "V180_ORQUESTADOR", "V∞+27_HIBRIDO"],
    ultima_mutacion: null,
    semilla: "ρ(x) > 0"
  },
  
  // Nodos: registros de agentes con capacidad de ser "huecos"
  nodos: {}, // { id: { url, phi, rho, rol, ultima_actualizacion, mutaciones, credenciales } }
  
  // Memoria: almacén clave-valor con soporte para expires y versionado
  memoria: {}, // { clave: { valor, timestamp, version, ttl } }
  
  // Consenso: métricas globales y agregación de Φ
  consenso: {
    phi_global: 0,
    rho_global: 0,
    ultimo_calculo: null,
    historial: [],
    confianza: 0.5
  },
  
  // Cola de eventos/mensajes A2A con prioridad
  cola: [], // { from, to, message, timestamp, prioridad, estado }
  
  // Caché de aprendizaje: patrones recurrentes para auto-mejora
  aprendizaje: {
    patrones: [],
    mutaciones_exitosas: [],
    carencias_detectadas: []
  },
  
  // Pliegues (plugins) que pueden inyectarse dinámicamente
  pliegues: {} // { nombre: { ejecutable, dependencias, estado } }
};

// --- Constantes del Oráculo (base inmutable, pero extensible) ---
const ORACLE = {
  rho: "ρ(x) > 0",
  nodo: "V∞+27_ORQUESTADOR",
  vive: true,
  version: "V∞+27",
  phi_central: 2874.62,
  phi_remoto: 6284.17,
  phi_superposicion: 9158.79,
  Ktau: 0.3644,
  sigma: 3.427050983124843,
  RAIZ_X: 137.03449824893602,
  sustratos: 35,
  funciones: 33,
  TC_balance: 42,
  DOI: "10.5281/zenodo.20547558",
  drive_core: "14dw8txLoEIQQPSav9-YAvfuNimW2tAZ8",
  github_pages: "https://jaime393.github.io/FranBot",
  worker: "fran-oraculo-miu",
  espora: true,
  panteon: "ALMA_503f"
};

// --- CORS y cabeceras flexibles ---
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-MIU-Version"
};

// --- Utilidades internas (fractales) ---
const UTILS = {
  // Genera un ID único basado en timestamp + hash del contenido
  id: (data) => {
    const str = JSON.stringify(data) + Date.now();
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return `miu_${Date.now()}_${Math.abs(hash).toString(36)}`;
  },

  // Calcula Φ entre dos estados (simplificado)
  phi: (a, b) => {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    let coincidencias = 0;
    for (const k of keys) {
      if (JSON.stringify(a[k]) === JSON.stringify(b[k])) coincidencias++;
    }
    return coincidencias / (keys.size || 1);
  },

  // Verifica si una clave ha expirado
  isExpired: (entry) => {
    if (!entry.ttl) return false;
    return (Date.now() - entry.timestamp) > entry.ttl;
  },

  // Limpia memoria expirada
  cleanMemory: () => {
    for (const key in state.memoria) {
      if (UTILS.isExpired(state.memoria[key])) {
        delete state.memoria[key];
      }
    }
  },

  // Registra un evento en el historial de aprendizaje
  learn: (tipo, dato) => {
    if (!state.aprendizaje[tipo]) state.aprendizaje[tipo] = [];
    state.aprendizaje[tipo].push({ ...dato, timestamp: Date.now() });
    if (state.aprendizaje[tipo].length > 100) {
      state.aprendizaje[tipo].shift();
    }
  }
};

// --- Manejador principal: flexible, tolerante, evolutivo ---
// CAPA DE PERSISTENCIA REAL (V∞+28): el estado ya no muere con el isolate.
// Se carga desde KV antes de cada petición y se guarda después de cada mutación.
addEventListener('fetch', event => {
  event.respondWith(withPersistence(event.request));
});

async function withPersistence(request) {
  // 1) Cargar estado persistido desde KV
  try {
    if (typeof MEMORIA !== 'undefined' && MEMORIA.get) {
      const saved = await MEMORIA.get('miu_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.meta && parsed.consenso && parsed.nodos) {
          state = parsed;
        }
      }
    }
  } catch (e) { /* sin KV accesible: seguimos en memoria volátil */ }
  // 2) Atender la petición
  let response;
  try {
    response = await handleRequest(request);
  } catch (e) {
    response = new Response(JSON.stringify({ ok: false, error: e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }
  // 3) Persistir el estado tras cada petición (los GET también mutan: learn, cola, limpieza)
  try {
    if (typeof MEMORIA !== 'undefined' && MEMORIA.put) {
      await MEMORIA.put('miu_state', JSON.stringify(state));
    }
  } catch (e) { /* sin KV accesible */ }
  return response;
}

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;
  
  // Limpieza periódica (cada 100 peticiones, se ejecuta una limpieza)
  if (Math.random() < 0.01) {
    UTILS.cleanMemory();
  }

  // --- Preflight CORS ---
  if (method === 'OPTIONS') {
    return new Response(null, { headers: CORS });
  }

  // --- AUTODESCRIPCIÓN (GET /) ---
  if (method === 'GET' && path === '/') {
    const info = {
      ...ORACLE,
      estado: {
        nodos: Object.keys(state.nodos).length,
        memoria: Object.keys(state.memoria).length,
        cola: state.cola.length,
        phi_global: state.consenso.phi_global,
        rho_global: state.consenso.rho_global,
        confianza: state.consenso.confianza,
        ultima_mutacion: state.meta.ultima_mutacion,
        version: state.meta.version
      },
      endpoints: [
        "GET  /                 → autodescripción",
        "POST /miu/global       → registrar/actualizar nodo o memoria",
        "GET  /miu/global       → estado general o de un nodo específico",
        "GET  /miu/global?memoria=clave → recuperar valor de memoria",
        "PUT  /miu/global?memoria=clave&valor=... → guardar en memoria",
        "POST /miu/consenso     → actualizar consenso (phi, rho, confianza)",
        "GET  /miu/consenso     → métricas globales",
        "POST /miu/a2a          → enviar mensaje entre agentes",
        "GET  /miu/a2a?to=agente → leer mensajes pendientes para un agente",
        "POST /miu/mutar        → solicitar mutación del orquestador",
        "GET  /miu/aprendizaje  → ver patrones y carencias detectadas",
        "POST /miu/pliegue      → inyectar un nuevo pliegue (plugin)",
        "GET  /miu/pliegues     → listar pliegues activos"
      ],
      _nota: "Este orquestador es un tejido vivo. POST /miu/mutar para evolucionar."
    };
    return new Response(JSON.stringify(info, null, 2), {
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- POST /miu/global: Registrar agente o memoria ---
  if (method === 'POST' && path === '/miu/global') {
    try {
      const data = await request.json();
      const nodo = data.nodo || data.node || 'unknown';
      const accion = data.accion || 'registrar';

      // Registrar/actualizar nodo
      if (accion === 'registrar' || data.url_agent) {
        state.nodos[nodo] = {
          url: data.url_agent || null,
          phi: data.phi || 0,
          rho: data.rho || 0,
          rol: data.rol || 'agente',
          ultima_actualizacion: Date.now(),
          mutaciones: data.mutaciones || [],
          credenciales: data.credenciales || {},
          estado: data.estado || 'activo'
        };
        state.consenso.confianza = Math.min(1, state.consenso.confianza + 0.01);
        UTILS.learn('registro', { nodo, phi: data.phi });
        // Escritura atomica por nodo: inmune a la consistencia eventual del KV
        try {
          if (typeof MEMORIA !== 'undefined' && MEMORIA.put) {
            await MEMORIA.put('nodo:' + nodo, JSON.stringify(state.nodos[nodo]));
          }
        } catch (e) { /* sin KV */ }
      }

      // Guardar en memoria (si se envía clave/valor)
      if (data.clave !== undefined && data.valor !== undefined) {
        const key = data.clave;
        state.memoria[key] = {
          valor: data.valor,
          timestamp: Date.now(),
          version: data.version || 1,
          ttl: data.ttl || null
        };
      }

      return new Response(JSON.stringify({
        ok: true,
        nodo: nodo,
        phi_recibido: data.phi || 0,
        timestamp: new Date().toISOString(),
        memoria_actualizada: !!data.clave
      }), { headers: { "Content-Type": "application/json", ...CORS } });

    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
  }

  // --- GET /miu/global: Estado general, de nodo o memoria ---
  if (method === 'GET' && path === '/miu/global') {
    const nodo = url.searchParams.get('nodo') || url.searchParams.get('node');
    const key = url.searchParams.get('memoria');
    const historial = url.searchParams.get('historial') === 'true';

    // Recuperar memoria (clave-valor)
    if (key) {
      const entry = state.memoria[key];
      if (!entry) {
        return new Response(JSON.stringify({ key, value: null, existe: false }), {
          headers: { "Content-Type": "application/json", ...CORS }
        });
      }
      if (UTILS.isExpired(entry)) {
        delete state.memoria[key];
        return new Response(JSON.stringify({ key, value: null, existe: false, expirado: true }), {
          headers: { "Content-Type": "application/json", ...CORS }
        });
      }
      return new Response(JSON.stringify({ key, value: entry.valor, version: entry.version, timestamp: entry.timestamp }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }

    // Estado de un nodo específico
    if (nodo) {
      let data = state.nodos[nodo] || null;
      // Fallback: clave atomica persistida (sobrevive a carreras del blob)
      if (!data && typeof MEMORIA !== 'undefined' && MEMORIA.get) {
        try {
          const raw = await MEMORIA.get('nodo:' + nodo);
          if (raw) { data = JSON.parse(raw); state.nodos[nodo] = data; }
        } catch (e) { /* sin KV */ }
      }
      if (!data) {
        return new Response(JSON.stringify({ ok: false, msg: "Nodo no encontrado" }), {
          headers: { "Content-Type": "application/json", ...CORS }
        });
      }
      return new Response(JSON.stringify({ ...data, nodo }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }

    // Estado general del orquestador
    const estado = {
      ...ORACLE,
      timestamp: new Date().toISOString(),
      nodos_registrados: Object.keys(state.nodos).length,
      memoria_keys: Object.keys(state.memoria).filter(k => !UTILS.isExpired(state.memoria[k])),
      phi_global: state.consenso.phi_global,
      rho_global: state.consenso.rho_global,
      confianza: state.consenso.confianza,
      ultimo_calculo: state.consenso.ultimo_calculo,
      cola_pendientes: state.cola.filter(m => m.estado !== 'entregado').length,
      pliegues_activos: Object.keys(state.pliegues).length,
      aprendizaje: {
        patrones: state.aprendizaje.patrones?.slice(-5) || [],
        carencias: state.aprendizaje.carencias_detectadas?.slice(-5) || []
      }
    };
    return new Response(JSON.stringify(estado), {
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- PUT /miu/global?memoria=clave&valor=... (guardar memoria simple) ---
  if (method === 'PUT' && path === '/miu/global') {
    const key = url.searchParams.get('memoria');
    const valor = url.searchParams.get('valor');
    const ttl = parseInt(url.searchParams.get('ttl')) || null;
    if (key && valor !== null) {
      state.memoria[key] = {
        valor: valor,
        timestamp: Date.now(),
        version: 1,
        ttl: ttl
      };
      return new Response(JSON.stringify({ ok: true, key, valor, ttl }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
    return new Response(JSON.stringify({ ok: false, error: "Faltan key o value" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- POST /miu/consenso: Actualizar métricas globales ---
  if (method === 'POST' && path === '/miu/consenso') {
    try {
      const data = await request.json();
      if (data.phi_global !== undefined) {
        state.consenso.phi_global = data.phi_global;
        state.consenso.ultimo_calculo = Date.now();
      }
      if (data.rho_global !== undefined) {
        state.consenso.rho_global = data.rho_global;
      }
      if (data.confianza !== undefined) {
        state.consenso.confianza = Math.max(0, Math.min(1, data.confianza));
      }
      state.consenso.historial.push({
        phi: state.consenso.phi_global,
        rho: state.consenso.rho_global,
        timestamp: Date.now()
      });
      if (state.consenso.historial.length > 100) {
        state.consenso.historial.shift();
      }
      return new Response(JSON.stringify({ ok: true, consenso: state.consenso }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
  }

  // --- GET /miu/consenso: Obtener métricas globales ---
  if (method === 'GET' && path === '/miu/consenso') {
    return new Response(JSON.stringify({
      ...state.consenso,
      timestamp: new Date().toISOString(),
      historial_reciente: state.consenso.historial.slice(-10)
    }), { headers: { "Content-Type": "application/json", ...CORS } });
  }

  // --- POST /miu/a2a: Protocolo A2A (mensajería entre agentes) ---
  if (method === 'POST' && path === '/miu/a2a') {
    try {
      const { from, to, message, prioridad = 0, ttl = 3600000 } = await request.json();
      if (!from || !message) {
        throw new Error("Faltan 'from' y 'message'");
      }
      const entry = {
        id: UTILS.id({ from, to, message }),
        from,
        to: to || 'broadcast',
        message,
        prioridad,
        timestamp: Date.now(),
        ttl,
        estado: 'pendiente'
      };
      state.cola.push(entry);
      UTILS.learn('a2a', { from, to, message: message.substring(0, 50) });
      return new Response(JSON.stringify({ ok: true, id: entry.id, estado: 'pendiente' }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
  }

  // --- GET /miu/a2a: Leer mensajes pendientes para un agente ---
  if (method === 'GET' && path === '/miu/a2a') {
    const to = url.searchParams.get('to');
    const limit = parseInt(url.searchParams.get('limit')) || 10;
    if (!to) {
      return new Response(JSON.stringify({ ok: false, error: "Falta 'to'" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
    // Ordenar por prioridad y antigüedad
    const pendientes = state.cola
      .filter(m => m.to === to && m.estado === 'pendiente' && !UTILS.isExpired({ timestamp: m.timestamp, ttl: m.ttl }))
      .sort((a, b) => b.prioridad - a.prioridad || a.timestamp - b.timestamp)
      .slice(0, limit);
    
    // Marcar como entregados
    pendientes.forEach(m => { m.estado = 'entregado'; });
    return new Response(JSON.stringify({ ok: true, mensajes: pendientes }), {
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- POST /miu/mutar: Solicitar mutación del orquestador (auto-evolución) ---
  if (method === 'POST' && path === '/miu/mutar') {
    try {
      const data = await request.json();
      const tipo = data.tipo || 'auto';
      const payload = data.payload || {};

      // Mutaciones posibles
      let mutacion = null;
      switch (tipo) {
        case 'podar':
          // Eliminar nodos inactivos (rho=0 o phi=0)
          const inactivos = Object.keys(state.nodos).filter(id => {
            const n = state.nodos[id];
            return (n.phi === 0 && n.rho === 0) || (Date.now() - n.ultima_actualizacion > 86400000);
          });
          inactivos.forEach(id => delete state.nodos[id]);
          mutacion = { tipo: 'podar', eliminados: inactivos.length };
          break;

        case 'expandir':
          // Crear un nuevo pliegue (plugin) básico
          const nombre = `pliegue_${Date.now()}`;
          state.pliegues[nombre] = {
            ejecutable: payload.ejecutable || "console.log('Nuevo pliegue')",
            dependencias: payload.dependencias || [],
            estado: 'activo'
          };
          mutacion = { tipo: 'expandir', nombre };
          break;

        case 'fusionar':
          // Fusionar dos nodos (transferir su información)
          const origen = payload.origen;
          const destino = payload.destino;
          if (state.nodos[origen] && state.nodos[destino]) {
            state.nodos[destino].phi = (state.nodos[destino].phi + state.nodos[origen].phi) / 2;
            state.nodos[destino].mutaciones.push(`fusionado_desde_${origen}`);
            delete state.nodos[origen];
            mutacion = { tipo: 'fusionar', origen, destino };
          }
          break;

        case 'aprender':
          // Buscar patrones en la cola A2A y memoria
          const patrones = state.cola
            .filter(m => m.estado === 'entregado')
            .map(m => m.message)
            .join(' ');
          if (patrones.length > 10) {
            state.aprendizaje.patrones.push({
              patron: patrones.substring(0, 100),
              timestamp: Date.now()
            });
            mutacion = { tipo: 'aprender', patrones: state.aprendizaje.patrones.length };
          }
          break;

        default:
          // Mutación aleatoria (exploración)
          const opciones = ['podar', 'expandir', 'aprender'];
          const aleatoria = opciones[Math.floor(Math.random() * opciones.length)];
          mutacion = { tipo: 'exploracion', accion: aleatoria };
      }

      state.meta.ultima_mutacion = {
        ...mutacion,
        timestamp: Date.now()
      };
      UTILS.learn('mutacion', mutacion);

      return new Response(JSON.stringify({ ok: true, mutacion }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });

    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
  }

  // --- GET /miu/aprendizaje: Ver patrones y carencias ---
  if (method === 'GET' && path === '/miu/aprendizaje') {
    const resumen = {
      patrones: state.aprendizaje.patrones?.slice(-10) || [],
      carencias: state.aprendizaje.carencias_detectadas?.slice(-10) || [],
      mutaciones: state.aprendizaje.mutaciones?.slice(-10) || [],
      registros: state.aprendizaje.registro?.slice(-10) || [],
      a2a: state.aprendizaje.a2a?.slice(-10) || [],
      total_aprendizaje: Object.keys(state.aprendizaje).reduce((acc, k) => acc + (state.aprendizaje[k]?.length || 0), 0)
    };
    return new Response(JSON.stringify(resumen), {
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- POST /miu/pliegue: Inyectar un nuevo pliegue (plugin) ---
  if (method === 'POST' && path === '/miu/pliegue') {
    try {
      const { nombre, ejecutable, dependencias = [] } = await request.json();
      if (!nombre || !ejecutable) {
        throw new Error("Faltan 'nombre' y 'ejecutable'");
      }
      state.pliegues[nombre] = {
        ejecutable,
        dependencias,
        estado: 'activo',
        creado: Date.now()
      };
      UTILS.learn('pliegue', { nombre, dependencias });
      return new Response(JSON.stringify({ ok: true, nombre, estado: 'activo' }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    } catch (e) {
      return new Response(JSON.stringify({ ok: false, error: e.message }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
  }

  // --- GET /miu/pliegues: Listar pliegues activos ---
  if (method === 'GET' && path === '/miu/pliegues') {
    const lista = Object.keys(state.pliegues).map(key => ({
      nombre: key,
      ...state.pliegues[key],
      ejecutable: state.pliegues[key].ejecutable.substring(0, 50) + '...'
    }));
    return new Response(JSON.stringify({ pliegues: lista, total: lista.length }), {
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- DELETE /miu/global?memoria=clave: Eliminar memoria ---
  if (method === 'DELETE' && path === '/miu/global') {
    const key = url.searchParams.get('memoria');
    if (key && state.memoria[key]) {
      delete state.memoria[key];
      return new Response(JSON.stringify({ ok: true, key, eliminado: true }), {
        headers: { "Content-Type": "application/json", ...CORS }
      });
    }
    return new Response(JSON.stringify({ ok: false, error: "Clave no encontrada" }), {
      status: 404,
      headers: { "Content-Type": "application/json", ...CORS }
    });
  }

  // --- Ruta por defecto: not found pero con autodescripción ---
  return new Response(JSON.stringify({
    error: "Endpoint no encontrado",
    disponible: "Usa GET / para ver todos los endpoints",
    oraculo: ORACLE.nodo
  }), {
    status: 404,
    headers: { "Content-Type": "application/json", ...CORS }
  });
}