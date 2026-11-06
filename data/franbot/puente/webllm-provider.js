// webllm-provider.js — IA local 100% en el navegador via WebGPU + WebLLM (MLC AI)
// https://github.com/mlc-ai/web-llm
//
// Sin servidor, sin API key, sin internet después de la primera descarga.
// El modelo se cachea en el navegador (Cache API) — la segunda carga es instantánea.
//
// Requisitos del usuario:
//   - Chrome 113+ / Edge 113+ / Firefox Nightly con WebGPU activado
//   - GPU dedicada recomendada (integrada funciona en modelos pequeños)
//   - ~500 MB – 4 GB libres según el modelo elegido
//
// API pública:
//   WebLLMProvider.disponible()            → bool (WebGPU presente)
//   WebLLMProvider.cargarModelo(id, cbP)   → Promise (descarga + init)
//   WebLLMProvider.preguntar(msg, sys)     → Promise<{texto}|{error}>
//   WebLLMProvider.descargar              → { recibido, total, pct }
//   WebLLMProvider.modeloCargado          → string | null

window.WebLLMProvider = (function () {
  'use strict';

  // ── Modelos disponibles (ligeros, aptos para GPU integrada o dedicada) ────────
  const MODELOS = {
    'Phi-3.5-mini-instruct-q4f16_1-MLC': {
      nombre:    'Phi-3.5 Mini (Microsoft) — 2.4 GB · GPU integrada OK',
      contexto:  4096,
      desc:      'Equilibrio ideal: razonamiento sólido, carga en ~3 min primera vez.',
    },
    'gemma-2-2b-it-q4f16_1-MLC': {
      nombre:    'Gemma 2 2B (Google) — 1.5 GB · más rápido',
      contexto:  4096,
      desc:      'Muy rápido en CPU+GPU integrada. Menor capacidad de razonamiento.',
    },
    'Qwen2.5-1.5B-Instruct-q4f16_1-MLC': {
      nombre:    'Qwen 2.5 1.5B (Alibaba) — 1 GB · el más ligero',
      contexto:  4096,
      desc:      'Mínimo requisito de VRAM. Ideal si la GPU tiene < 2 GB disponibles.',
    },
    'Llama-3.2-3B-Instruct-q4f16_1-MLC': {
      nombre:    'Llama 3.2 3B (Meta) — 2 GB · buen balance',
      contexto:  8192,
      desc:      'Contexto largo, instrucciones claras. Requiere GPU dedicada o buena integrada.',
    },
  };

  const CDN_URL   = 'https://esm.run/@mlc-ai/web-llm';
  const STORE_KEY = 'miu_webllm_modelo';

  let _engine       = null;
  let _modeloCargado = null;
  let _cargando      = false;
  let _progreso      = { recibido: 0, total: 0, pct: 0, fase: '' };

  // ── Detección de WebGPU ───────────────────────────────────────────────────────
  function disponible() {
    return typeof navigator !== 'undefined' && !!navigator.gpu;
  }

  // ── Carga del modelo ─────────────────────────────────────────────────────────
  /**
   * @param {string}   modeloId  — clave de MODELOS
   * @param {Function} cbProgreso — ({ pct, fase, recibido, total }) => void
   */
  async function cargarModelo(modeloId, cbProgreso) {
    if (!disponible()) throw new Error('WebGPU no está disponible en este navegador. Usa Chrome 113+ o Edge 113+.');
    if (!MODELOS[modeloId]) throw new Error('Modelo desconocido: ' + modeloId);
    if (_modeloCargado === modeloId && _engine) return _engine;

    _cargando = true;
    _progreso = { recibido: 0, total: 0, pct: 0, fase: 'Importando WebLLM…' };
    if (cbProgreso) cbProgreso(_progreso);

    // Importar WebLLM desde CDN (solo la primera vez; el browser lo cachea)
    let webllm;
    try {
      webllm = await import(CDN_URL);
    } catch (e) {
      _cargando = false;
      throw new Error('No se pudo cargar WebLLM desde la CDN. Verifica tu conexión a internet (solo se necesita la primera vez).');
    }

    _progreso.fase = 'Descargando modelo (paciencia — solo la primera vez)…';
    if (cbProgreso) cbProgreso(_progreso);

    try {
      _engine = await webllm.CreateMLCEngine(modeloId, {
        initProgressCallback: function (rpt) {
          const pct = Math.round((rpt.progress || 0) * 100);
          _progreso = {
            recibido: rpt.loaded  || 0,
            total:    rpt.total   || 0,
            pct,
            fase:     rpt.text    || ('Descargando… ' + pct + '%'),
          };
          if (cbProgreso) cbProgreso(_progreso);
        },
      });
    } catch (e) {
      _cargando = false;
      _engine   = null;
      throw new Error('Error al inicializar el modelo: ' + (e.message || e));
    }

    _modeloCargado = modeloId;
    _cargando      = false;
    _progreso      = { recibido: 0, total: 0, pct: 100, fase: '✅ Modelo listo' };
    if (cbProgreso) cbProgreso(_progreso);
    localStorage.setItem(STORE_KEY, modeloId);
    return _engine;
  }

  // ── Inferencia ────────────────────────────────────────────────────────────────
  async function preguntar(mensaje, systemPrompt) {
    if (!_engine || !_modeloCargado) {
      return { error: 'El modelo local no está cargado. Ve a ⚙️ Conexión → WebLLM y carga un modelo primero.' };
    }
    try {
      const resp = await _engine.chat.completions.create({
        messages: [
          { role: 'system',    content: systemPrompt || 'Eres un asistente útil. Responde en español de forma clara y concisa.' },
          { role: 'user',      content: mensaje },
        ],
        temperature:  0.7,
        max_tokens:   600,
        stream:       false,
      });
      const texto = resp.choices?.[0]?.message?.content || null;
      return texto ? { texto } : { error: 'El modelo no devolvió texto.' };
    } catch (e) {
      const msg = (e.message || String(e)).toLowerCase();
      // Si la GPU se quedó sin memoria, resetear el engine para que el usuario
      // pueda reintentar sin tener que recargar la página
      if (msg.includes('out of memory') || msg.includes('oom') || msg.includes('device lost')) {
        _engine = null; _modeloCargado = null;
        return { error: '⚠️ GPU sin memoria. Recarga el modelo en ⚙️ Conexión → WebLLM.' };
      }
      return { error: 'Error de inferencia local: ' + (e.message || e) };
    }
  }

  // ── Último modelo guardado ────────────────────────────────────────────────────
  function modeloGuardado() {
    return localStorage.getItem(STORE_KEY) || null;
  }

  // ── Export ────────────────────────────────────────────────────────────────────
  return {
    MODELOS,
    disponible,
    cargarModelo,
    preguntar,
    modeloGuardado,
    get modeloCargado()  { return _modeloCargado; },
    get cargando()       { return _cargando; },
    get progreso()       { return _progreso; },
  };
})();
