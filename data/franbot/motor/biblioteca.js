// biblioteca.js — Panel "Biblioteca" para FranBot v10
// Gestiona la UI de archivos digeridos, cola de procesamiento,
// selector de fragmentos, estadísticas y visor de pares aprendidos.
// Depende de: idb-store.js, alimentar.js

window.Biblioteca = (function () {
  'use strict';

  // ─────────────── Estado interno ───────────────────────────────────────────────
  let _mapaFiles     = new Map(); // idCola → File (no persistible en IDB)
  let _maxTrozos     = 14;
  let _procesando    = false;
  let _cbActualizar  = null;     // callback para actualizar badge en app.js

  // ─────────────── Helpers UI ───────────────────────────────────────────────────

  function $(id) { return document.getElementById(id); }

  function _iconoEstado(estado) {
    return { pendiente: '⏳', procesando: '⚙️', completo: '✅', error: '❌' }[estado] || '❓';
  }

  function _fmtTam(bytes) {
    if (bytes < 1024)        return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function _fmtFecha(ts) {
    return ts ? new Date(ts).toLocaleString('es', { dateStyle: 'short', timeStyle: 'short' }) : '—';
  }

  // ─────────────── Render cola ─────────────────────────────────────────────────

  async function renderCola() {
    const contenedor = $('bib-cola');
    if (!contenedor) return;
    if (!window.IDBStore) {
      contenedor.innerHTML = '<li class="bib-item bib-warn">IDBStore no disponible — actualiza a v10</li>';
      return;
    }
    const cola = await window.IDBStore.obtenerCola().catch(() => []);
    if (!cola.length) {
      contenedor.innerHTML = '<li class="bib-item bib-vacio">Sin archivos en cola.</li>';
      return;
    }
    // Ordenar: pendientes/procesando primero
    cola.sort((a, b) => {
      const orden = { procesando: 0, pendiente: 1, error: 2, completo: 3 };
      return (orden[a.estado] || 9) - (orden[b.estado] || 9);
    });
    contenedor.innerHTML = cola.map(t => {
      const progreso = t.total > 0 ? Math.round((t.procesado / t.total) * 100) : 0;
      const barraHTML = (t.estado === 'procesando' || t.estado === 'completo')
        ? `<div class="bib-barra-fondo"><div class="bib-barra-fill" style="width:${progreso}%"></div></div>`
        : '';
      return `
        <li class="bib-item bib-item--${t.estado}" data-id="${t.id}">
          <span class="bib-ico">${_iconoEstado(t.estado)}</span>
          <div class="bib-info">
            <span class="bib-nombre" title="${t.nombre}">${t.nombre}</span>
            <span class="bib-meta">${_fmtTam(t.tamaño || 0)} · ${_fmtFecha(t.t)}</span>
            ${barraHTML}
            ${t.estado === 'procesando' ? `<span class="bib-progreso-txt">${t.procesado}/${t.total} fragmentos</span>` : ''}
            ${t.estado === 'error'      ? `<span class="bib-error-txt" title="${t.error || ''}">⚠ ${(t.error||'').slice(0,60)}</span>` : ''}
          </div>
          <button class="bib-btn-quitar" data-id="${t.id}" title="Quitar de la cola">✕</button>
        </li>`;
    }).join('');

    // Botones quitar
    contenedor.querySelectorAll('.bib-btn-quitar').forEach(btn => {
      btn.addEventListener('click', async function () {
        const id = Number(this.dataset.id);
        await window.IDBStore.eliminarDeCola(id);
        _mapaFiles.delete(id);
        await renderCola();
        await renderEstadisticas();
      });
    });
  }

  // ─────────────── Estadísticas ─────────────────────────────────────────────────

  async function renderEstadisticas() {
    if (!window.IDBStore) return;
    const [totalPares, cola] = await Promise.all([
      window.IDBStore.contarPares().catch(() => 0),
      window.IDBStore.obtenerCola().catch(() => []),
    ]);
    const totalArchivos = new Set(cola.filter(t => t.estado === 'completo').map(t => t.nombre)).size;
    const pendientes    = cola.filter(t => t.estado === 'pendiente').length;

    const elPares    = $('bib-total');
    const elArchivos = $('bib-archivos');
    const elBadge    = $('bib-badge');
    if (elPares)    elPares.textContent    = totalPares.toLocaleString();
    if (elArchivos) elArchivos.textContent = totalArchivos;
    if (elBadge) {
      elBadge.textContent = pendientes > 0 ? pendientes : '';
      elBadge.style.display = pendientes > 0 ? 'inline' : 'none';
    }
    if (_cbActualizar) _cbActualizar({ totalPares, totalArchivos, pendientes });
  }

  // ─────────────── Añadir archivos ─────────────────────────────────────────────

  async function añadirArchivos(files) {
    if (!window.IDBStore) {
      window.MiuToast && MiuToast.err('IDBStore no disponible. Recarga FranBot.');
      return;
    }
    await window.IDBStore.open();
    let añadidos = 0;
    for (const file of files) {
      if (!file || file.size === 0) continue;
      try {
        const id = await window.Alimentar.encolarArchivo(file);
        _mapaFiles.set(id, file);
        añadidos++;
      } catch (e) {
        console.warn('Biblioteca: no se pudo encolar', file.name, e);
      }
    }
    if (añadidos) {
      await renderCola();
      await renderEstadisticas();
      mostrarPanelTrozos();
    }
  }

  // ─────────────── Panel selector de trozos ────────────────────────────────────

  function mostrarPanelTrozos() {
    const panel  = $('bib-fragmentos-ctrl');
    const maxInp = $('bib-max');
    if (!panel) return;
    panel.style.display = 'block';
    if (maxInp) {
      maxInp.value = _maxTrozos;
      actualizarEstimacion();
    }
  }

  function actualizarEstimacion() {
    const maxInp = $('bib-max');
    const elEst  = $('bib-costo-est');
    if (!maxInp || !elEst) return;
    const n = parseInt(maxInp.value, 10) || 1;
    _maxTrozos = n;
    elEst.textContent = '· ' + (window.Alimentar ? window.Alimentar.estimarCosto(n) : '');
  }

  // ─────────────── Procesar cola ────────────────────────────────────────────────

  async function procesarCola() {
    if (_procesando) return;
    if (!window.IDBStore || !window.Alimentar) return;
    _procesando = true;
    const btnP = $('btn-bib-procesar');
    if (btnP) { btnP.disabled = true; btnP.textContent = '⚙️ Procesando…'; }

    try {
      await window.Alimentar.procesarCola(
        _mapaFiles,
        async (idTarea, actual, total) => {
          await window.IDBStore.actualizarCola(idTarea, { procesado: actual, total });
          await renderCola();
        },
        _maxTrozos
      );

      // Limpiar cola completada después de un tiempo
      setTimeout(async () => {
        await window.IDBStore.limpiarColaCompletada();
        await renderCola();
        await renderEstadisticas();
      }, 4000);

    } catch (e) {
      console.error('Biblioteca.procesarCola error:', e);
    } finally {
      _procesando = false;
      if (btnP) { btnP.disabled = false; btnP.textContent = 'Procesar cola'; }
      await renderCola();
      await renderEstadisticas();
    }
  }

  // ─────────────── Poda ─────────────────────────────────────────────────────────

  async function podar(umbralPeso) {
    if (!window.IDBStore) return;
    umbralPeso = (typeof umbralPeso === 'number') ? umbralPeso : -3;

    // Preview: contar antes de borrar
    const todos      = await window.IDBStore.todosLosPares().catch(() => []);
    const candidatos = todos.filter(p => (p.peso || 0) <= umbralPeso);
    if (!candidatos.length) {
      window.MiuToast && MiuToast.ok('El oráculo está saludable — sin pares negativos que eliminar.');
      return;
    }
    const ok = confirm(
      `Se eliminarán ${candidatos.length} pares con peso ≤ ${umbralPeso}.\n` +
      `Quedarán ${todos.length - candidatos.length} pares.\n\n¿Continuar?`
    );
    if (!ok) return;
    const eliminados = await window.IDBStore.podarParesPorPeso(umbralPeso);
    await renderEstadisticas();
    window.MiuToast && MiuToast.ok('✂️ Poda completa: ' + eliminados + ' pares eliminados.');
  }

  // ─────────────── Exportar pares aprendidos ───────────────────────────────────

  async function exportarPares(soloPositivos) {
    if (!window.IDBStore) return;
    const todos  = await window.IDBStore.todosLosPares().catch(() => []);
    const filtro = soloPositivos ? todos.filter(p => (p.peso || 0) >= 0) : todos;
    const json   = JSON.stringify(filtro, null, 2);
    const blob   = new Blob([json], { type: 'application/json' });
    const url    = URL.createObjectURL(blob);
    const a      = document.createElement('a');
    a.href       = url;
    a.download   = `miu_pares_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ─────────────── Inicialización ───────────────────────────────────────────────

  async function init(cb) {
    _cbActualizar = cb || null;
    if (!window.IDBStore) return;
    await window.IDBStore.open();

    // Migrar desde localStorage si hay pares allí
    await window.IDBStore.migrarDesdeLocalStorage();

    // Bind input fragmentos
    const maxInp = $('bib-max');
    if (maxInp) maxInp.addEventListener('input', actualizarEstimacion);

    // Bind botón procesar
    const btnP = $('btn-bib-procesar');
    if (btnP) btnP.addEventListener('click', procesarCola);

    // Bind botón podar
    const btnPodar = $('btn-podar');
    if (btnPodar) btnPodar.addEventListener('click', () => podar(-3));

    // Bind botón exportar
    const btnExp = $('btn-exportar-pares');
    if (btnExp) btnExp.addEventListener('click', () => exportarPares(true));

    // Bind input file del panel
    const fileInput = $('bib-file');
    if (fileInput) fileInput.addEventListener('change', e => añadirArchivos([...e.target.files]));

    // Drag & drop en la zona
    const dropZone = $('bib-drop');
    if (dropZone) {
      dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('bib-drag-over'); });
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('bib-drag-over'));
      dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('bib-drag-over');
        if (e.dataTransfer.files.length) añadirArchivos([...e.dataTransfer.files]);
      });
    }

    // Bind botón Colmena P2P
    const btnColm = $('btn-colmena');
    if (btnColm) btnColm.addEventListener('click', () => {
      if (window.ColmenaUI) window.ColmenaUI.abrir();
      else window.MiuToast && MiuToast.err('Módulo Colmena no disponible. Recarga la página.');
    });

    // Bind botón consolidar
    const btnCons = $('btn-consolidar');
    if (btnCons) btnCons.addEventListener('click', async () => {
      if (!window.Consolidar) return window.MiuToast && MiuToast.err('Módulo Consolidar no disponible.');
      if (!window.ModoAPI || !window.ModoAPI.estaActivo()) {
        const ok = confirm('Para una fusión semántica de calidad se recomienda el modo API. ¿Continuar sin modelo?');
        if (!ok) return;
      }
      const stats = await window.Consolidar.obtenerEstadisticas().catch(() => null);
      if (!stats || !stats.gruposDuplicados) { window.MiuToast && MiuToast.ok('El oráculo ya está optimizado — sin duplicados.'); return; }
      const ok = confirm(
        `Se encontraron ${stats.gruposDuplicados} grupos de pares similares
` +
        `(${stats.paresEnDuplicados} pares → potencial reducción de ${stats.potencialReduccion} pares).

` +
        `¿Fusionar con el modelo API?`
      );
      if (!ok) return;
      btnCons.disabled = true; btnCons.textContent = '⚙️ Consolidando…';
      try {
        const r = await window.Consolidar.consolidarTodo({
          cbProgreso: (i, n) => { btnCons.textContent = '⚙️ ' + i + '/' + n; }
        });
        window.MiuToast && MiuToast.ok('✅ Consolidado: ' + r.fusionados + ' grupos fusionados, ' + r.eliminados + ' pares compactados, ' + r.errores + ' errores.');
        await renderEstadisticas();
      } finally {
        btnCons.disabled = false; btnCons.textContent = '🔗 Consolidar';
      }
    });

    // Bind botón exportar oráculo
    const btnExpOrac = $('btn-exportar-oraculo');
    if (btnExpOrac) btnExpOrac.addEventListener('click', async () => {
      if (!window.Consolidar) { window.MiuToast && MiuToast.err('Módulo Consolidar no disponible.'); return; }
      btnExpOrac.disabled = true; btnExpOrac.textContent = '⚙️ Generando…';
      try {
        const r = await window.Consolidar.exportarOraculoDataJS();
        if (r) window.MiuToast && MiuToast.ok('⬇️ oraculo-data.js: ' + r.totalPares + ' pares (base:' + r.base + ' + IDB:' + r.idb + ').');
      } finally {
        btnExpOrac.disabled = false; btnExpOrac.textContent = '⬇️ Exportar oráculo';
      }
    });

    // Bind botón visor de pares
    const btnVisor = $('btn-visor-pares');
    if (btnVisor) btnVisor.addEventListener('click', () => {
      if (window.VisorPares) window.VisorPares.abrir();
    });

    // Render inicial
    await renderCola();
    await renderEstadisticas();
  }

  // ─────────────── Export ───────────────────────────────────────────────────────
  return {
    init,
    añadirArchivos,
    renderCola,
    renderEstadisticas,
    podar,
    exportarPares,
    procesarCola,
    get maxTrozos() { return _maxTrozos; },
    set maxTrozos(v) { _maxTrozos = Math.max(1, Number(v) || 14); },
  };
})();
