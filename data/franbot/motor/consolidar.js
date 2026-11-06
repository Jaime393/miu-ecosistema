// consolidar.js — Fusión semántica de pares Q/A duplicados o similares (v10)
// Usa el modelo API (si está activo) para reducir N pares similares a 1-2 de mayor calidad.
// Depende de: idb-store.js, modo-API.js
//
// API:
//   Consolidar.agruparPorSimilitud(pares)  → Array de grupos
//   Consolidar.fusionarGrupo(grupo)        → par mejorado (async, necesita modo API)
//   Consolidar.consolidarTodo(opts)        → { fusionados, eliminados, errores }
//   Consolidar.exportarOraculoDataJS()     → descarga nuevo oraculo-data.js

window.Consolidar = (function () {
  'use strict';

  // ─────────────── Tokenización ligera ─────────────────────────────────────────
  const STOP = new Set(['de','la','el','en','y','a','que','es','se','del','los','las',
    'un','una','con','por','para','como','más','pero','si','lo','le','su','sus',
    'no','al','me','mi','te','tu','yo','él','qué','cómo','cuál','hay','muy',
    'todo','esta','este','son','fue','ser','estar','ha','han','era','tiene',
    'también','ya','sobre','desde','hasta','entre','donde','o']);

  function _tokenizar(s) {
    return (s || '').toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter(t => t.length > 2 && !STOP.has(t));
  }

  function _jaccardSim(a, b) {
    const sa = new Set(_tokenizar(a));
    const sb = new Set(_tokenizar(b));
    if (!sa.size || !sb.size) return 0;
    let inter = 0;
    sa.forEach(t => { if (sb.has(t)) inter++; });
    return inter / (sa.size + sb.size - inter);
  }

  // ─────────────── Agrupación por similitud ────────────────────────────────────
  /**
   * Agrupa pares con preguntas muy similares (Jaccard ≥ umbral).
   * Complejidad O(n²) — solo se usa sobre el delta de pares recientes, no el corpus entero.
   * @param {Array}  pares   — pares { q, a }
   * @param {number} umbral  — similitud mínima (default 0.55)
   * @returns {Array<Array>} — array de grupos
   */
  function agruparPorSimilitud(pares, umbral) {
    umbral = umbral || 0.55;
    const usados = new Set();
    const grupos = [];

    for (let i = 0; i < pares.length; i++) {
      if (usados.has(i)) continue;
      const grupo = [pares[i]];
      usados.add(i);
      for (let j = i + 1; j < pares.length; j++) {
        if (usados.has(j)) continue;
        if (_jaccardSim(pares[i].q, pares[j].q) >= umbral) {
          grupo.push(pares[j]);
          usados.add(j);
        }
      }
      grupos.push(grupo);
    }
    return grupos;
  }

  // ─────────────── Fusión con el modelo API ─────────────────────────────────
  /**
   * Funde un grupo de pares similares en 1 par de mayor calidad.
   * Requiere ModoAPI activo. Si falla, devuelve el par con más texto.
   */
  async function fusionarGrupo(grupo) {
    if (!grupo || !grupo.length) return null;
    if (grupo.length === 1) return grupo[0];

    if (!window.ModoAPI || !window.ModoAPI.estaActivo()) {
      // Sin modelo: devolver el par con respuesta más larga
      return grupo.reduce((best, p) => ((p.a||'').length > (best.a||'').length ? p : best));
    }

    const pairesTexto = grupo.map((p, i) =>
      `Par ${i + 1}:\nPregunta: ${p.q}\nRespuesta: ${p.a}`
    ).join('\n\n---\n\n');

    const sys = 'Eres un editor de bases de conocimiento. Se te dan varios pares pregunta/respuesta ' +
      'sobre el mismo tema pero con diferente redacción. Tu trabajo es fusionarlos en UN SOLO PAR ' +
      'de mayor calidad: la pregunta más clara y la respuesta más completa y concisa (2-4 frases). ' +
      'Responde EXCLUSIVAMENTE con un objeto JSON: {"q":"pregunta","a":"respuesta"}. ' +
      'Sin texto extra, sin bloques de código, solo el JSON.';

    const msg = `Fusiona estos ${grupo.length} pares en uno solo:\n\n${pairesTexto}`;

    try {
      const r = await window.ModoAPI.preguntar(msg, sys);
      if (!r || r.error || !r.texto) throw new Error('Sin respuesta del modelo');
      const limpio = r.texto.trim().replace(/^```(json)?/i,'').replace(/```$/,'').trim();
      const obj = JSON.parse(limpio);
      if (typeof obj.q === 'string' && typeof obj.a === 'string') {
        return { q: obj.q.trim(), a: obj.a.trim(), origen: 'consolidado', t: Date.now() };
      }
      throw new Error('JSON inválido');
    } catch (e) {
      console.warn('Consolidar: fusión fallida, usando el par más largo', e);
      return grupo.reduce((best, p) => ((p.a||'').length > (best.a||'').length ? p : best));
    }
  }

  // ─────────────── Consolidación completa ──────────────────────────────────────
  /**
   * Carga todos los pares de IDB, agrupa los similares y fusiona con el modelo.
   * @param {Object} opts
   *   opts.umbral        {number}  similitud mínima (default 0.55)
   *   opts.soloGrupos    {boolean} si true, solo devuelve grupos sin ejecutar fusión
   *   opts.cbProgreso    {Function}(actual, total) => void
   * @returns {{ fusionados, eliminados, errores, grupos }}
   */
  async function consolidarTodo(opts) {
    opts = opts || {};
    if (!window.IDBStore) throw new Error('IDBStore no disponible');

    await window.IDBStore.open();
    const todos = await window.IDBStore.todosLosPares();
    if (!todos || !todos.length) return { fusionados: 0, eliminados: 0, errores: 0, grupos: [] };

    // Solo pares aprendidos (no los del oráculo base) con peso ≥ -2
    const elegibles = todos.filter(p => (p.peso || 0) >= -2);
    const grupos = agruparPorSimilitud(elegibles, opts.umbral || 0.55);
    const conDuplicados = grupos.filter(g => g.length > 1);

    if (opts.soloGrupos) return { fusionados: 0, eliminados: 0, errores: 0, grupos: conDuplicados };

    let fusionados = 0, eliminados = 0, errores = 0;
    const total = conDuplicados.length;

    for (let i = 0; i < conDuplicados.length; i++) {
      const grupo = conDuplicados[i];
      if (opts.cbProgreso) opts.cbProgreso(i + 1, total);
      try {
        const fusionado = await fusionarGrupo(grupo);
        if (!fusionado) { errores++; continue; }
        // Marcar los originales con peso muy bajo para que la poda los elimine
        for (const p of grupo) {
          if (p.id !== undefined) {
            await window.IDBStore.actualizarPeso(Number(p.id), -99);
          }
        }
        // Agregar el par fusionado
        await window.IDBStore.agregarPares([fusionado]);
        fusionados++;
        eliminados += grupo.length;
      } catch (e) {
        console.warn('Consolidar: error en grupo', e);
        errores++;
      }
    }

    // Si BuscarOraculo existe, reconstruir el índice
    if (window.BuscarOraculo && BuscarOraculo.iniciarConIDB) {
      await BuscarOraculo.iniciarConIDB().catch(() => {});
    }

    return { fusionados, eliminados, errores, grupos: conDuplicados };
  }

  // ─────────────── Exportar oraculo-data.js regenerado ─────────────────────────
  /**
   * Combina el oráculo base (de BuscarOraculo._pares) con los pares IDB de buena calidad
   * y genera un nuevo oraculo-data.js en formato base64 para descargar.
   * El usuario puede reemplazar el archivo en su repo para que el próximo arranque
   * incluya todo el conocimiento aprendido como base.
   */
  async function exportarOraculoDataJS() {
    // 1. Pares base actuales en el índice
    const paresBase = (window.BuscarOraculo && BuscarOraculo._pares)
      ? BuscarOraculo._pares.filter(p => p.origen !== 'idb' && p.origen !== 'aprendido' && p.origen !== 'consolidado')
      : [];

    // 2. Pares IDB con peso ≥ 0 (solo los validados)
    let paresIDB = [];
    if (window.IDBStore) {
      try {
        await window.IDBStore.open();
        const todos = await window.IDBStore.todosLosPares();
        paresIDB = todos
          .filter(p => (p.peso || 0) >= 0)
          .map(p => ({ q: p.q, a: p.a, origen: p.origen || 'aprendido' }));
      } catch (e) {
        console.warn('exportarOraculoDataJS: no se pudieron cargar pares IDB', e);
      }
    }

    // 3. Deduplicar por q normalizado
    const vistos = new Set();
    const combinados = [];
    [...paresBase, ...paresIDB].forEach(p => {
      const key = (p.q || '').trim().toLowerCase().slice(0, 80);
      if (key && !vistos.has(key)) {
        vistos.add(key);
        combinados.push({ q: p.q.trim(), a: p.a.trim() });
      }
    });

    if (!combinados.length) {
      window.MiuToast && MiuToast.warn('No hay pares para exportar.'); return;
      return;
    }

    // 4. Serializar igual que oraculo-data.js: base64 de JSON con {pares:[...]}
    const json   = JSON.stringify({ pares: combinados });
    const b64    = btoa(unescape(encodeURIComponent(json)));
    const js     = `window.ORACULO_BASE64 = "${b64}";\n`;

    // 5. Descargar
    const blob = new Blob([js], { type: 'application/javascript' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'oraculo-data.js';
    a.click();
    URL.revokeObjectURL(url);

    return { totalPares: combinados.length, base: paresBase.length, idb: paresIDB.length };
  }

  // ─────────────── Estadísticas de similitud ───────────────────────────────────
  async function obtenerEstadisticas() {
    if (!window.IDBStore) return null;
    await window.IDBStore.open();
    const todos = await window.IDBStore.todosLosPares().catch(() => []);
    const elegibles = todos.filter(p => (p.peso || 0) >= -2);
    const grupos = agruparPorSimilitud(elegibles, 0.55);
    const conDuplicados = grupos.filter(g => g.length > 1);
    return {
      totalPares: todos.length,
      elegibles: elegibles.length,
      gruposDuplicados: conDuplicados.length,
      paresEnDuplicados: conDuplicados.reduce((s, g) => s + g.length, 0),
      potencialReduccion: conDuplicados.reduce((s, g) => s + g.length - 1, 0),
    };
  }

  // ─────────────── Export ───────────────────────────────────────────────────────
  return {
    agruparPorSimilitud,
    fusionarGrupo,
    consolidarTodo,
    exportarOraculoDataJS,
    obtenerEstadisticas,
    _jaccardSim,
  };
})();
