// modo-online.js — Modo online opcional: el usuario pega su propia clave de un
// proveedor en la nube, o conecta cualquier servidor compatible con el formato
// de OpenAI (/v1/chat/completions) — incluida una opción "Personalizado" genérica
// que cubre proveedores no listados (Mistral, DeepSeek, Perplexity, Azure OpenAI...)
// y servidores locales sin clave (Ollama, LM Studio, llama.cpp, vLLM, koboldcpp...).
// Todo se guarda solo en este navegador y se usa solo para llamar directo a la
// API elegida — nunca pasa por ningún servidor intermedio propio.
'use strict';

window.ModoOnline = {
  _activo: false,

  // ── Historial multi-turno ──────────────────────────────────────────────────
  // Buffer de los últimos MAX_TURNOS pares user/assistant. Se pasa en cada
  // llamada online para dar contexto real. Se persiste en sessionStorage
  // (misma pestaña — sobrevive recargas, se borra al cerrar la pestaña).
  _historial: [],
  MAX_TURNOS: 6, // máx. pares a recordar (6 pares = 12 entradas: user+assistant×6)
  _HIST_KEY: 'mo_hist', // clave sessionStorage

  agregarTurno(role, texto) {
    if (!texto) return;
    this._historial.push({ role, texto });
    // Recortar: mantener solo los últimos MAX_TURNOS*2 mensajes (N pares)
    const limite = this.MAX_TURNOS * 2;
    if (this._historial.length > limite) {
      this._historial.splice(0, this._historial.length - limite);
    }
    // Persistir en sessionStorage — sobrevive recargas dentro de la misma pestaña
    try { sessionStorage.setItem(this._HIST_KEY, JSON.stringify(this._historial)); } catch (_) {}
  },

  limpiarHistorial() {
    this._historial = [];
    try { sessionStorage.removeItem(this._HIST_KEY); } catch (_) {}
  },

  // Tabla de proveedores. Añadir uno nuevo es agregar una entrada aquí — app.js
  // construye el <select> de panelConfig() a partir de esto, no a mano.
  // 'requiereClave: false' es lo que distingue a 'personalizado': sin eso, un
  // servidor local sin autenticación (la mayoría) nunca podría activarse, porque
  // estaActivo() exigiría una clave que no existe ni hace falta.
  PROVEEDORES: {
    groq: {
      nombre: 'Groq — Llama 3.3 70B (gratis, rápido)',
      url: 'https://api.groq.com/openai/v1/chat/completions',
      modelo: 'llama-3.3-70b-versatile',
      requiereClave: true
    },
    openrouter: {
      nombre: 'OpenRouter — GPT-4o mini',
      url: 'https://openrouter.ai/api/v1/chat/completions',
      modelo: 'openai/gpt-4o-mini',
      requiereClave: true
    },
    together: {
      nombre: 'Together AI — Llama 3.3 70B',
      url: 'https://api.together.xyz/v1/chat/completions',
      modelo: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
      requiereClave: true
    },
    openai: {
      nombre: 'OpenAI — GPT-4o mini',
      url: 'https://api.openai.com/v1/chat/completions',
      modelo: 'gpt-4o-mini',
      requiereClave: true
    },
    anthropic: {
      // API /v1/messages: formato diferente al estándar OpenAI.
      // Cabecera 'x-api-key' en vez de 'Authorization: Bearer'.
      // 'system' va al nivel raíz del body, no en el array messages.
      // SSE usa pares event:/data: — solo interesa 'content_block_delta'.
      nombre: '🟠 Anthropic — Claude Haiku 4.5 (rápido, fácil)',
      url: 'https://api.anthropic.com/v1/messages',
      modelo: 'claude-haiku-4-5-20251001',
      requiereClave: true,
      esAnthropic: true
    },
    gemini: {
      // API distinta al estándar OpenAI: key va en la URL, no en cabeceras.
      // Endpoint: /v1beta/models/{modelo}:generateContent?key={key}
      // SSE: /v1beta/models/{modelo}:streamGenerateContent?alt=sse&key={key}
      nombre: '🔵 Google Gemini — tier gratuito disponible',
      url: 'https://generativelanguage.googleapis.com/v1beta/models',
      modelo: 'gemini-2.0-flash',
      requiereClave: true,
      esGemini: true
    },
    webllm: {
      nombre: '🖥️ WebLLM — IA local en el navegador (sin API, sin internet tras la descarga)',
      url: '__webllm__', modelo: '__webllm__',
      requiereClave: false, esWebLLM: true
    },
    personalizado: {
      nombre: 'Personalizado — cualquier API tipo OpenAI / servidor local',
      url: '', modelo: '', requiereClave: false, esPersonalizado: true
    }
  },

  // Atajos para rellenar URL+modelo de un click cuando el proveedor es
  // 'personalizado' (app.js los usa para los botones rápidos). No son
  // proveedores aparte: siguen guardándose como 'personalizado'.
  ATAJOS_LOCALES: {
    ollama:   { nombre: 'Ollama (local)',    url: 'http://localhost:11434/v1/chat/completions', modeloEjemplo: 'llama3.2' },
    lmstudio: { nombre: 'LM Studio (local)', url: 'http://localhost:1234/v1/chat/completions',   modeloEjemplo: 'el modelo que tengas cargado en LM Studio' }
  },

  // Modelos disponibles para el proveedor 'gemini'.
  // El seleccionado se guarda en localStorage['gemini_modelo'].
  MODELOS_GEMINI: {
    'gemini-2.0-flash-lite': { nombre: 'Gemini 2.0 Flash Lite — gratuito, muy rápido' },
    'gemini-2.0-flash':      { nombre: 'Gemini 2.0 Flash — gratuito, equilibrado' },
    'gemini-1.5-flash':      { nombre: 'Gemini 1.5 Flash — gratuito, probado' },
    'gemini-1.5-pro':        { nombre: 'Gemini 1.5 Pro — de pago, más capaz' },
  },

  cargar() {
    const cfg = JSON.parse(localStorage.getItem('miu_online') || 'null');
    if (cfg?.proveedor) {
      this._proveedor = cfg.proveedor;
      this._clave = cfg.clave || '';
      this._url = cfg.url || '';
      this._modelo = cfg.modelo || '';
      this._activo = !!cfg.activo;
    }
    // ── Restaurar historial desde sessionStorage ─────────────────────────────
    // sessionStorage persiste mientras la pestaña esté abierta (incluyendo
    // recargas con F5/Ctrl+R). Se borra automáticamente al cerrar la pestaña.
    try {
      const guardado = sessionStorage.getItem(this._HIST_KEY);
      if (guardado) {
        const parsed = JSON.parse(guardado);
        if (Array.isArray(parsed)) this._historial = parsed;
      }
    } catch (_) { /* sessionStorage no disponible o JSON corrupto — ignorar */ }
    return cfg;
  },

  guardar(proveedor, clave, activo, urlPersonalizada, modeloPersonalizado) {
    this._proveedor = proveedor;
    this._clave = (clave || '').trim();
    this._url = (urlPersonalizada || '').trim();
    this._modelo = (modeloPersonalizado || '').trim();
    this._activo = activo;
    localStorage.setItem('miu_online', JSON.stringify({
      proveedor, clave: this._clave, activo, url: this._url, modelo: this._modelo
    }));
  },

  // Resuelve a dónde llamar y con qué modelo, según el proveedor activo.
  _conexion() {
    if (this._proveedor === 'webllm')       return { url: '__webllm__', modelo: '__webllm__' };
    if (this._proveedor === 'personalizado') return { url: this._url, modelo: this._modelo };
    const preset = this.PROVEEDORES[this._proveedor];
    return preset ? { url: preset.url, modelo: preset.modelo } : { url: '', modelo: '' };
  },

  estaActivo() {
    if (!this._activo) return false;
    if (this._proveedor === 'webllm') {
      return !!(window.WebLLMProvider && window.WebLLMProvider.modeloCargado);
    }
    const { url, modelo } = this._conexion();
    if (!url || !modelo) return false;
    const preset = this.PROVEEDORES[this._proveedor];
    if (preset && preset.requiereClave && !this._clave) return false;
    return true;
  },

  async preguntar(mensaje, systemPrompt) {
    if (!this._activo) return null;
    // Ruta WebLLM — inferencia local sin red
    if (this._proveedor === 'webllm') {
      if (!window.WebLLMProvider || !window.WebLLMProvider.modeloCargado) {
        return { error: 'Modelo local no cargado. Abre ⚙️ Conexión → WebLLM y carga un modelo primero.' };
      }
      return window.WebLLMProvider.preguntar(mensaje, systemPrompt);
    }
    if (!this.estaActivo()) return null;

    // ── Ruta Anthropic (/v1/messages — formato distinto al estándar OpenAI) ──
    if (this.PROVEEDORES[this._proveedor]?.esAnthropic) {
      return this._preguntarAnthropic(mensaje, systemPrompt);
    }

    // ── Ruta Gemini (/v1beta/models — key en URL, formato de body distinto) ──
    if (this.PROVEEDORES[this._proveedor]?.esGemini) {
      return this._preguntarGemini(mensaje, systemPrompt);
    }

    const { url, modelo } = this._conexion();
    const headers = { 'Content-Type': 'application/json' };
    if (this._clave) headers['Authorization'] = `Bearer ${this._clave}`;

    // ── Streaming SSE ────────────────────────────────────────────────────────
    // Devuelve { stream: true, reader } cuando el callback onToken está disponible.
    // El caller (app.js) es quien anima el bubble token a token.
    // Si el proveedor no soporta SSE (respuesta no chunked), cae al modo bloque.
    if (this._onToken) {
      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            model: modelo,
            messages: [
              { role: 'system', content: systemPrompt || 'Eres un asistente útil. Responde en español.' },
              ...this._historial.map(t => ({ role: t.role, content: t.texto })),
              { role: 'user', content: mensaje }
            ],
            temperature: 0.7,
            max_tokens: 600,
            stream: true
          })
        });

        if (!resp.ok || !resp.body) {
          // Caer al modo bloque si falla el stream
          return this._preguntarBloque(url, modelo, headers, mensaje, systemPrompt);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let textoAcumulado = '';
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lineas = buffer.split('\n');
          // Conservar la última línea incompleta en el buffer
          buffer = lineas.pop();

          for (const linea of lineas) {
            const l = linea.trim();
            if (!l || l === 'data: [DONE]') continue;
            if (!l.startsWith('data: ')) continue;
            try {
              const json = JSON.parse(l.slice(6));
              const delta = json.choices?.[0]?.delta?.content || '';
              if (delta) {
                textoAcumulado += delta;
                if (this._onToken) this._onToken(delta, textoAcumulado);
              }
            } catch (_) { /* chunk SSE mal formado — ignorar */ }
          }
        }

        return { texto: textoAcumulado || null };
      } catch (e) {
        return this._manejarErrorRed(e, url);
      }
    }

    // ── Modo bloque (sin streaming) ──────────────────────────────────────────
    return this._preguntarBloque(url, modelo, headers, mensaje, systemPrompt);
  },

  /** Registra el callback para recibir tokens uno a uno durante el streaming.
   *  onToken(delta, textoAcumulado) — llamado por cada fragmento SSE recibido.
   *  Pasar null desactiva el streaming. */
  setOnToken(fn) {
    this._onToken = typeof fn === 'function' ? fn : null;
  },

  async _preguntarBloque(url, modelo, headers, mensaje, systemPrompt) {
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: modelo,
          messages: [
            { role: 'system', content: systemPrompt || 'Eres un asistente útil. Responde en español.' },
            ...this._historial.map(t => ({ role: t.role, content: t.texto })),
            { role: 'user', content: mensaje }
          ],
          temperature: 0.7,
          max_tokens: 600
        })
      });
      const data = await resp.json().catch(() => null);
      if (!data) return { error: `Respuesta no válida del servidor (HTTP ${resp.status}).` };
      if (data.error) {
        const msg = typeof data.error === 'string' ? data.error : (data.error.message || JSON.stringify(data.error));
        return { error: msg };
      }
      return { texto: data.choices?.[0]?.message?.content || null };
    } catch (e) {
      return this._manejarErrorRed(e, url);
    }
  },

  // ── Anthropic API /v1/messages ─────────────────────────────────────────────
  // Diferencias con el formato OpenAI:
  //   · Cabecera 'x-api-key' (no 'Authorization: Bearer')
  //   · Cabecera 'anthropic-version: 2023-06-01' obligatoria
  //   · El system prompt va al nivel raíz del body, no en messages[]
  //   · No hay role 'system' en messages — solo 'user' y 'assistant'
  //   · Respuesta: data.content[0].text  (no data.choices[0].message.content)
  //   · SSE: pares 'event: TYPE\ndata: {...}' — solo 'content_block_delta' importa
  async _preguntarAnthropic(mensaje, systemPrompt) {
    const { url, modelo } = this._conexion();
    const headers = {
      'Content-Type': 'application/json',
      'x-api-key': this._clave,
      'anthropic-version': '2023-06-01'
    };
    if (this._onToken) {
      return this._preguntarAnthropicStream(url, modelo, headers, mensaje, systemPrompt);
    }
    // ── Modo bloque (sin streaming) ──
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: modelo,
          max_tokens: 600,
          system: systemPrompt || 'Eres un asistente útil. Responde siempre en español.',
          messages: [
            ...this._historial.map(t => ({ role: t.role, content: t.texto })),
            { role: 'user', content: mensaje }
          ]
        })
      });
      const data = await resp.json().catch(() => null);
      if (!data) return { error: `Respuesta no válida del servidor (HTTP ${resp.status}).` };
      // Errores Anthropic: { type: 'error', error: { type: '...', message: '...' } }
      if (data.type === 'error') return { error: data.error?.message || JSON.stringify(data.error) };
      return { texto: data.content?.[0]?.text || null };
    } catch (e) {
      return this._manejarErrorRed(e, url);
    }
  },

  // SSE de Anthropic — pares event:/data: en bloques separados por línea en blanco.
  // Único evento útil: 'content_block_delta' con delta.type === 'text_delta'.
  // Resto de eventos (message_start, content_block_start, message_delta, etc.) se ignoran.
  async _preguntarAnthropicStream(url, modelo, headers, mensaje, systemPrompt) {
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: modelo,
          max_tokens: 600,
          system: systemPrompt || 'Eres un asistente útil. Responde siempre en español.',
          messages: [
            ...this._historial.map(t => ({ role: t.role, content: t.texto })),
            { role: 'user', content: mensaje }
          ],
          stream: true
        })
      });

      if (!resp.ok || !resp.body) {
        // Si el stream falla, intentar en modo bloque
        return this._preguntarAnthropic(mensaje, systemPrompt);
      }

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let textoAcumulado = '';
      let buffer      = '';
      let eventActual = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lineas = buffer.split('\n');
        buffer = lineas.pop(); // retener última línea incompleta

        for (const linea of lineas) {
          const l = linea.trim();
          if (!l) {
            // Línea en blanco → fin del bloque SSE actual, resetear event
            eventActual = '';
            continue;
          }
          if (l.startsWith('event: ')) {
            eventActual = l.slice(7);   // ej: 'content_block_delta'
            continue;
          }
          if (!l.startsWith('data: ')) continue;
          if (eventActual !== 'content_block_delta') continue;
          try {
            const json  = JSON.parse(l.slice(6));
            const delta = json.delta?.type === 'text_delta' ? json.delta.text : '';
            if (delta) {
              textoAcumulado += delta;
              if (this._onToken) this._onToken(delta, textoAcumulado);
            }
          } catch (_) { /* chunk SSE mal formado — ignorar */ }
        }
      }

      return { texto: textoAcumulado || null };
    } catch (e) {
      return this._manejarErrorRed(e, url);
    }
  },

  // ── Google Gemini API ──────────────────────────────────────────────────────
  // Diferencias clave con el formato OpenAI:
  //   · La API key va en la URL, no en cabeceras
  //   · Solo cabecera: Content-Type: application/json
  //   · System prompt: { "systemInstruction": { "parts": [{ "text": "..." }] } }
  //   · Mensajes: { "contents": [{ "role": "user", "parts": [{ "text": "..." }] }] }
  //   · Respuesta bloque: data.candidates[0].content.parts[0].text
  //   · SSE (alt=sse): json.candidates[0].content.parts[].text — concatenar todos
  //   · No hay evento [DONE] — el stream termina con HTTP close
  //   · Errores: { "error": { "code": N, "message": "...", "status": "..." } }
  async _preguntarGemini(mensaje, systemPrompt) {
    const modelo  = localStorage.getItem('gemini_modelo') || this.PROVEEDORES.gemini.modelo;
    const base    = this.PROVEEDORES.gemini.url;
    const headers = { 'Content-Type': 'application/json' };
    const body = {
      systemInstruction: { parts: [{ text: systemPrompt || 'Eres un asistente útil. Responde siempre en español.' }] },
      contents: [
        ...this._historial.map(t => ({
          role: t.role === 'assistant' ? 'model' : 'user',
          parts: [{ text: t.texto }]
        })),
        { role: 'user', parts: [{ text: mensaje }] }
      ],
      generationConfig: { maxOutputTokens: 600 }
    };
    if (this._onToken) {
      return this._preguntarGeminiStream(base, modelo, headers, body);
    }
    // ── Modo bloque ──
    const urlBloque = `${base}/${modelo}:generateContent?key=${this._clave}`;
    try {
      const resp = await fetch(urlBloque, { method: 'POST', headers, body: JSON.stringify(body) });
      const data = await resp.json().catch(() => null);
      if (!data) return { error: `Respuesta no válida del servidor (HTTP ${resp.status}).` };
      if (data.error) return { error: data.error.message || JSON.stringify(data.error) };
      return { texto: data.candidates?.[0]?.content?.parts?.[0]?.text || null };
    } catch (e) {
      return this._manejarErrorRed(e, base);
    }
  },

  // SSE de Gemini — alt=sse devuelve líneas 'data: {...}' con path candidates[0].content.parts[].
  // No hay evento [DONE]; el stream termina con HTTP close.
  // Cada chunk puede traer múltiples "parts" — concatenar todas.
  async _preguntarGeminiStream(base, modelo, headers, body) {
    const urlStream = `${base}/${modelo}:streamGenerateContent?alt=sse&key=${this._clave}`;
    try {
      const resp = await fetch(urlStream, { method: 'POST', headers, body: JSON.stringify(body) });
      if (!resp.ok || !resp.body) {
        // Caer al modo bloque si el stream falla
        const urlBloque = `${base}/${modelo}:generateContent?key=${this._clave}`;
        try {
          const r2 = await fetch(urlBloque, { method: 'POST', headers, body: JSON.stringify(body) });
          const d2 = await r2.json().catch(() => null);
          if (!d2) return { error: `Respuesta no válida del servidor (HTTP ${r2.status}).` };
          if (d2.error) return { error: d2.error.message || JSON.stringify(d2.error) };
          return { texto: d2.candidates?.[0]?.content?.parts?.[0]?.text || null };
        } catch (e2) { return this._manejarErrorRed(e2, base); }
      }
      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let textoAcumulado = '';
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lineas = buffer.split('\n');
        buffer = lineas.pop(); // retener última línea incompleta
        for (const linea of lineas) {
          const l = linea.trim();
          if (!l || !l.startsWith('data: ')) continue;
          try {
            const json  = JSON.parse(l.slice(6));
            // Gemini puede devolver múltiples parts por chunk — concatenar todas
            const delta = json.candidates?.[0]?.content?.parts
              ?.map(p => p.text || '').join('') || '';
            if (delta) {
              textoAcumulado += delta;
              if (this._onToken) this._onToken(delta, textoAcumulado);
            }
          } catch (_) { /* chunk SSE mal formado — ignorar */ }
        }
      }
      return { texto: textoAcumulado || null };
    } catch (e) {
      return this._manejarErrorRed(e, base);
    }
  },

  _manejarErrorRed(e, url) {
    const esLocal = /localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.|10\.\d+\.\d+\.\d+/.test(url);
    const pista = esLocal
      ? ' Revisa que el servidor local esté corriendo y que acepte conexiones de este origen (CORS) — en Ollama, por ejemplo, eso es la variable de entorno OLLAMA_ORIGINS=*.'
      : ' Revisa tu conexión, la URL y la clave.';
    return { error: 'No se pudo conectar.' + pista };
  }
};
window.ModoOnline.cargar();
