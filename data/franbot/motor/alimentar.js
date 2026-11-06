// alimentar.js v2.1 — Digiere archivos en pares Q/A para el oráculo.
// Cambios sobre v2:
//   · BUG FIX: regex /g en streaming ya no comparte lastIndex entre lecturas
//   · BUG FIX: buffer.slice(p - 50) protegido contra índice negativo
//   · BUG FIX: partirEnTrozos divide párrafos mayores que TAM_TROZO a nivel de frase
//   · BUG FIX: lookbehind (?<=[.!?]) reemplazado por alternativa compatible (Safari, Node <10)
//   · MEJORA: jsonATexto detecta formatos adicionales (Claude.ai export, Gemini, {title+messages})
//   · MEJORA: extraerOffline detecta estructura Q/A preexistente en el texto
//   · MEJORA: deduplicación de pares dentro de procesarArchivo (por huella q+a)
//   · MEJORA: limpieza de fence cubre ~~~json y fences de 4 backticks
//   · MEJORA: estimarCosto incluye tokens de salida estimados
//   · Retrocompatible: procesarArchivo() sigue funcionando igual que en v2

window.Alimentar = (function () {
  'use strict';

  const LIMITE_TROZOS_DEFAULT = 14;
  const TAM_TROZO             = 1600;
  const UMBRAL_STREAM         = 500 * 1024;

  // ─────────────── Parseo de formatos de chat ───────────────────────────────

  function _textoPlanoDeCualquierJSON(val, prof) {
    prof = prof || 0;
    if (prof > 8) return '';
    if (typeof val === 'string') return val.trim();
    if (Array.isArray(val))
      return val.map(v => _textoPlanoDeCualquierJSON(v, prof + 1)).filter(Boolean).join('\n\n');
    if (val && typeof val === 'object')
      return Object.values(val).map(v => _textoPlanoDeCualquierJSON(v, prof + 1)).filter(Boolean).join('\n\n');
    return '';
  }

  function _etiquetaRol(rol) {
    const r = (rol || '').toString().toLowerCase();
    if (/user|usuario|human|person|humano/.test(r))                              return 'Usuario';
    if (/assistant|asistente|bot|^ai$|model|claude|gpt|gemini|copilot/.test(r)) return 'Asistente';
    if (/system|sistema/.test(r))                                                return 'Sistema';
    return rol ? String(rol) : 'Mensaje';
  }

  function _textoDesdeMapping(conv) {
    if (!conv || !conv.mapping) return '';
    return Object.values(conv.mapping).map(nodo => {
      const msg   = nodo && nodo.message;
      const parts = msg && msg.content && Array.isArray(msg.content.parts) ? msg.content.parts : null;
      if (!parts) return '';
      const texto = parts.filter(p => typeof p === 'string').join('\n').trim();
      return texto ? `${_etiquetaRol(msg.author && msg.author.role)}: ${texto}` : '';
    }).filter(Boolean).join('\n\n');
  }

  function _textoDesdeArray(arr) {
    return arr.map(m => {
      if (typeof m === 'string') return m;
      if (!m || typeof m !== 'object') return '';
      const rol = m.role || m.author || m.sender || m.from;
      const contenido =
        typeof m.content  === 'string' ? m.content  :
        typeof m.text     === 'string' ? m.text     :
        typeof m.body     === 'string' ? m.body     :  // Gemini export
        _textoPlanoDeCualquierJSON(m.content || m.parts || '');
      const txt = contenido.trim();
      return txt ? `${_etiquetaRol(rol)}: ${txt}` : '';
    }).filter(Boolean).join('\n\n');
  }

  function jsonATexto(obj) {
    // Formato ChatGPT (array de conversaciones con mapping)
    if (Array.isArray(obj) && obj[0] && obj[0].mapping)
      return obj.map(_textoDesdeMapping).filter(Boolean).join('\n\n---\n\n');
    if (obj && obj.mapping)
      return _textoDesdeMapping(obj);

    // Formato Claude.ai export: { name, chat_messages }
    if (obj && Array.isArray(obj.chat_messages))
      return _textoDesdeArray(obj.chat_messages);
    if (Array.isArray(obj) && obj[0] && Array.isArray(obj[0].chat_messages))
      return obj.map(c => _textoDesdeArray(c.chat_messages)).filter(Boolean).join('\n\n---\n\n');

    // Formato genérico { messages: [...] } o { title, messages: [...] }
    if (obj && Array.isArray(obj.messages))
      return _textoDesdeArray(obj.messages);

    // Formato Gemini: { conversations: [{messages}] } o { items: [{body}] }
    if (obj && Array.isArray(obj.conversations))
      return obj.conversations.map(c => _textoDesdeArray(c.messages || [])).filter(Boolean).join('\n\n---\n\n');
    if (obj && Array.isArray(obj.items))
      return obj.items.map(it => (typeof it.body === 'string' ? it.body : _textoPlanoDeCualquierJSON(it))).filter(Boolean).join('\n\n');

    // Array plano de mensajes { role, content/text }
    if (Array.isArray(obj) && obj[0] && (obj[0].role || obj[0].content || obj[0].text))
      return _textoDesdeArray(obj);

    return _textoPlanoDeCualquierJSON(obj);
  }

  // ─────────────── Extracción de texto ──────────────────────────────────────

  async function extraerTextoDeArchivo(file) {
    const crudo = await file.text();
    if (!crudo || !crudo.trim()) throw new Error('El archivo está vacío.');
    const pareceJSON = /\.json$/i.test(file.name) || /^\s*[\[{]/.test(crudo);
    if (!pareceJSON) return crudo;
    try {
      const parsed = JSON.parse(crudo);
      // Array vacío o null → devolver crudo para procesamiento heurístico
      if (!parsed || (Array.isArray(parsed) && parsed.length === 0)) return crudo;
      const txt = jsonATexto(parsed);
      return (txt && txt.trim().length > 50) ? txt : crudo;
    } catch (e) { return crudo; }
  }

  async function extraerTextoStreaming(file) {
    const reader  = file.stream().getReader();
    const decoder = new TextDecoder('utf-8');
    // FIX: no usar regex /g global entre lecturas — construir nueva instancia por bloque
    const PATRON  = /"(?:content|text|message|body|parts)"\s*:\s*"((?:[^"\\]|\\.)*)"/;
    let buffer = '', resultado = '', n = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Extraer todos los matches del buffer actual con nueva RegExp en cada bloque
      const rex = new RegExp(PATRON.source, 'g');
      let m;
      while ((m = rex.exec(buffer)) !== null) {
        const txt = m[1]
          .replace(/\\n/g, '\n').replace(/\\t/g, ' ')
          .replace(/\\"/g, '"').replace(/\\\\/g, '\\').trim();
        if (txt && txt.length > 20) { resultado += txt + '\n\n'; n++; }
      }

      // FIX: proteger slice contra índice negativo
      const p = buffer.lastIndexOf('"');
      if (p > 65536) buffer = buffer.slice(Math.max(0, p - 50));
    }

    if (n < 5) return extraerTextoDeArchivo(file);
    return resultado;
  }

  // ─────────────── Troceo ───────────────────────────────────────────────────

  // FIX: divide frases usando split compatible con Safari (sin lookbehind)
  function _partirEnFrases(texto) {
    // Insertar marca tras puntuación de cierre seguida de espacio+mayúscula
    return texto
      .replace(/([.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡"'])/g, '$1\x00')
      .split('\x00')
      .map(s => s.trim())
      .filter(Boolean);
  }

  function partirEnTrozos(texto, tam) {
    tam = tam || TAM_TROZO;
    const parrafos = texto.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
    const trozos = []; let actual = '';

    parrafos.forEach(p => {
      // FIX: párrafo individual más largo que tam → dividir a nivel de frase
      if (p.length > tam) {
        if (actual.trim()) { trozos.push(actual.trim()); actual = ''; }
        const frases = _partirEnFrases(p);
        frases.forEach(fr => {
          if ((actual + ' ' + fr).length > tam && actual) {
            trozos.push(actual.trim()); actual = fr;
          } else {
            actual = actual ? actual + ' ' + fr : fr;
          }
        });
        return;
      }
      if ((actual + '\n\n' + p).length > tam && actual) {
        trozos.push(actual.trim()); actual = p;
      } else {
        actual = actual ? actual + '\n\n' + p : p;
      }
    });

    if (actual.trim()) trozos.push(actual.trim());
    return trozos;
  }

  // ─────────────── Extracción de pares ──────────────────────────────────────

  // Detecta si el trozo ya tiene estructura de diálogo o Q/A explícita
  function _yaEsDialogo(trozo) {
    return /^(Usuario|Asistente|Human|Assistant|Q:|P:)\s*:/im.test(trozo)
        || /\?\s*\n+[^\n]{20,}/.test(trozo);
  }

  function extraerOffline(trozo) {
    // Si el trozo ya es un diálogo estructurado, generar par directo
    if (_yaEsDialogo(trozo)) {
      const lineas = trozo.split('\n').filter(l => l.trim().length > 15);
      const pregunta = lineas.find(l => /[?？]/.test(l)) || lineas[0] || '';
      const respuesta = lineas.filter(l => l !== pregunta).join(' ').slice(0, 700);
      if (pregunta && respuesta)
        return [{ q: pregunta.replace(/^[^:]+:\s*/, '').trim(),
                  a: respuesta.trim(), origen: 'local-dialogo' }];
    }
    // Fallback heurístico
    // FIX: split sin lookbehind para compatibilidad
    const oraciones = _partirEnFrases(trozo).filter(s => s.length > 25);
    if (!oraciones.length) return [];
    const primeras = oraciones[0].split(/\s+/).slice(0, 9).join(' ').replace(/[.,;:]$/, '');
    return [{ q: `¿Qué dice el texto sobre "${primeras}…"?`,
              a: trozo.length > 700 ? trozo.slice(0, 700).trim() + '…' : trozo,
              origen: 'local-heuristico' }];
  }

  async function extraerOnline(trozo, nombreArchivo) {
    if (!window.ModoOnline || !window.ModoOnline.estaActivo()) return extraerOffline(trozo);

    const sys = [
      'Extraes pares pregunta/respuesta de un texto.',
      'Responde SOLO con un array JSON válido, sin texto adicional ni bloques markdown.',
      'Formato exacto: [{"q":"pregunta autocontenida en español","a":"respuesta de 1-3 frases basada en el texto"}].',
      'Genera entre 1 y 4 pares. Prioriza preguntas que alguien podría buscar realmente.',
      'Si el texto no tiene contenido informativo claro, responde [].',
    ].join(' ');

    const msg = `Archivo: ${nombreArchivo || '(sin nombre)'}\n\nTexto:\n"""${trozo}"""`;

    try {
      const r = await window.ModoOnline.preguntar(msg, sys);
      if (!r || r.error || !r.texto) return extraerOffline(trozo);

      // FIX: limpiar fences de backticks (3 o 4) y tildes
      const limpio = r.texto.trim()
        .replace(/^`{3,4}(json)?\s*/i, '')
        .replace(/\s*`{3,4}$/, '')
        .replace(/^~{3,4}(json)?\s*/i, '')
        .replace(/\s*~{3,4}$/, '')
        .trim();

      const arr = JSON.parse(limpio);
      if (!Array.isArray(arr)) return extraerOffline(trozo);
      return arr
        .filter(p => p && typeof p.q === 'string' && typeof p.a === 'string'
                       && p.q.trim().length > 5 && p.a.trim().length > 5)
        .map(p => ({ q: p.q.trim(), a: p.a.trim(), origen: 'en-linea' }));
    } catch (e) {
      return extraerOffline(trozo);
    }
  }

  // ─────────────── Estimación de costo ──────────────────────────────────────

  function estimarCosto(numTrozos) {
    if (!window.ModoOnline || !window.ModoOnline.estaActivo())
      return `${numTrozos} fragmento(s) · procesado localmente (sin API, sin costo)`;

    const cfg  = window.ModoOnline.cargar() || {};
    const prov = cfg.proveedor || 'groq';

    if (prov === 'groq' || prov === 'personalizado')
      return `${numTrozos} llamada(s) a ${prov} · sin costo monetario`;

    // FIX: incluir tokens de salida (~300 por llamada además de ~700 de entrada)
    const tokensEntrada = numTrozos * 700;
    const tokensSalida  = numTrozos * 300;
    const totalTokens   = tokensEntrada + tokensSalida;
    return `${numTrozos} llamada(s) a ${prov} · ~${tokensEntrada.toLocaleString()} tokens entrada + ~${tokensSalida.toLocaleString()} salida = ~${totalTokens.toLocaleString()} tokens totales estimados`;
  }

  // ─────────────── procesarArchivo ──────────────────────────────────────────

  async function procesarArchivo(file, onProgreso, opts) {
    opts = opts || {};
    const maxTrozos  = (typeof opts.maxTrozos === 'number' && opts.maxTrozos > 0)
      ? opts.maxTrozos : LIMITE_TROZOS_DEFAULT;
    const usarStream = opts.usarStream !== undefined ? opts.usarStream : (file.size > UMBRAL_STREAM);
    const idCola     = opts.idCola || null;

    let texto;
    if (usarStream && /\.json$/i.test(file.name)) texto = await extraerTextoStreaming(file);
    else                                           texto = await extraerTextoDeArchivo(file);
    if (!texto || !texto.trim()) throw new Error('No se pudo extraer texto utilizable.');

    let trozos = partirEnTrozos(texto);
    const totalOriginal = trozos.length;
    const truncado      = trozos.length > maxTrozos;
    trozos = trozos.slice(0, maxTrozos);

    if (idCola && window.IDBStore)
      await window.IDBStore.actualizarCola(idCola, { total: trozos.length, estado: 'procesando' });

    const todos  = [];
    // FIX: deduplicar pares por huella normalizada (q+a) dentro del mismo archivo
    const vistos = new Set();

    for (let i = 0; i < trozos.length; i++) {
      if (onProgreso) onProgreso(i + 1, trozos.length);
      if (idCola && window.IDBStore)
        await window.IDBStore.actualizarCola(idCola, { procesado: i + 1 });

      const pares = await extraerOnline(trozos[i], file.name);
      pares.forEach(p => {
        const huella = (p.q + '|' + p.a).toLowerCase().replace(/\s+/g, ' ');
        if (!vistos.has(huella)) {
          vistos.add(huella);
          todos.push(Object.assign({ archivo: file.name, t: Date.now() }, p));
        }
      });
    }

    if (window.IDBStore && todos.length > 0) {
      const guardados = await window.IDBStore.agregarPares(todos);
      if (idCola) await window.IDBStore.actualizarCola(idCola, { estado: 'completo' });
      // D.2b: re-indexar solo los pares recién guardados (tienen _idb_id asignado)
      if (typeof window._reindexarNuevosPares === 'function' && Array.isArray(guardados)) {
        window._reindexarNuevosPares(guardados);
      }
    }

    return { pares: todos, truncado, trozosProcesados: trozos.length, totalOriginal };
  }

  // ─────────────── Cola ─────────────────────────────────────────────────────

  async function encolarArchivo(file) {
    if (!window.IDBStore) throw new Error('IDBStore no disponible');
    await window.IDBStore.open();
    return window.IDBStore.encolar({
      nombre: file.name, tamaño: file.size,
      estado: 'pendiente', total: 0, procesado: 0, t: Date.now()
    });
  }

  async function procesarCola(mapaFiles, cbProgreso, maxTrozos) {
    if (!window.IDBStore) return [];
    const cola       = await window.IDBStore.obtenerCola();
    const pendien    = cola.filter(t => t.estado === 'pendiente');
    const resultados = [];
    for (const tarea of pendien) {
      const file = mapaFiles.get(tarea.id);
      if (!file) continue;
      try {
        const r = await procesarArchivo(
          file,
          (i, n) => { if (cbProgreso) cbProgreso(tarea.id, i, n); },
          { maxTrozos: maxTrozos || LIMITE_TROZOS_DEFAULT, idCola: tarea.id }
        );
        resultados.push({ id: tarea.id, ...r });
      } catch (err) {
        await window.IDBStore.actualizarCola(tarea.id, { estado: 'error', error: err.message });
      }
    }
    return resultados;
  }

  // ─────────────── Export ───────────────────────────────────────────────────
  return {
    partirEnTrozos, extraerOffline, extraerOnline,
    extraerTextoDeArchivo, extraerTextoStreaming, jsonATexto,
    procesarArchivo, estimarCosto,
    encolarArchivo, procesarCola,
    LIMITE_TROZOS: LIMITE_TROZOS_DEFAULT,
    UMBRAL_STREAM,
  };
})();
