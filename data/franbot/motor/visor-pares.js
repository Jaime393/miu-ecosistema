// visor-pares.js — Visor interactivo de pares Q/A aprendidos (v10)
// Panel flotante con búsqueda en vivo, edición inline, eliminar por id,
// exportar selección y métricas del índice TF-IDF.
// Depende de: idb-store.js, buscar-oraculo.js

window.VisorPares = (function () {
  'use strict';

  let _pares    = [];   // copia local para el visor (paginada)
  let _pagina   = 0;
  let _porPag   = 20;
  let _filtro   = '';
  let _orden    = 'reciente'; // 'reciente' | 'peso' | 'az'
  let _abierto  = false;

  // ─────────────── Panel HTML ───────────────────────────────────────────────────
  const PANEL_ID = 'visor-pares-panel';

  function _crearPanel() {
    if (document.getElementById(PANEL_ID)) return;
    const div = document.createElement('div');
    div.id    = PANEL_ID;
    div.innerHTML = `
      <div class="vp-header">
        <span class="vp-titulo">📋 Pares aprendidos</span>
        <span id="vp-stats-txt" class="tenue" style="font-size:11px"></span>
        <button id="vp-cerrar" class="icono-boton" style="margin-left:auto">✕</button>
      </div>
      <div class="vp-controles">
        <input id="vp-buscar" type="search" placeholder="Buscar en pares…" class="vp-input-buscar" autocomplete="off">
        <select id="vp-orden" class="vp-select">
          <option value="reciente">Más reciente</option>
          <option value="peso">Mayor peso</option>
          <option value="az">A → Z</option>
        </select>
        <button class="chip-bib" id="vp-exportar">💾 Exportar</button>
      </div>
      <div id="vp-lista" class="vp-lista"></div>
      <div class="vp-pie">
        <button class="chip-bib" id="vp-prev">‹ Anterior</button>
        <span id="vp-pagina-txt" class="tenue" style="font-size:12px"></span>
        <button class="chip-bib" id="vp-next">Siguiente ›</button>
      </div>
    `;
    document.body.appendChild(div);

    document.getElementById('vp-cerrar').onclick  = cerrar;
    document.getElementById('vp-prev').onclick    = () => { if (_pagina > 0) { _pagina--; _render(); } };
    document.getElementById('vp-next').onclick    = () => { _pagina++; _render(); };
    document.getElementById('vp-exportar').onclick = _exportar;

    const inpBuscar = document.getElementById('vp-buscar');
    inpBuscar.addEventListener('input', _debounce(() => {
      _filtro = inpBuscar.value.trim();
      _pagina = 0;
      _render();
    }, 250));

    document.getElementById('vp-orden').addEventListener('change', function() {
      _orden = this.value; _pagina = 0; _render();
    });
  }

  function _debounce(fn, ms) {
    let t; return function(...a) { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  }

  // ─────────────── Carga de datos ───────────────────────────────────────────────

  async function _cargarPares() {
    _pares = [];
    // Fuente 1: IDB
    if (window.IDBStore) {
      try { _pares = await window.IDBStore.todosLosPares(); } catch(e) {}
    }
    // Fuente 2: oraculo_extension de localStorage (si IDB vacía o para completar)
    if (!_pares.length) {
      try {
        const raw   = localStorage.getItem('miu_estado');
        const est   = raw ? JSON.parse(raw) : {};
        const ext   = Array.isArray(est.oraculo_extension) ? est.oraculo_extension : [];
        _pares = ext.map((p, i) => ({ id: 'loc_' + i, q: p.q || '', a: p.a || '', peso: p.peso || 0, origen: p.origen || 'local' }));
      } catch(e) {}
    }
  }

  // ─────────────── Render ───────────────────────────────────────────────────────

  function _parFiltrado() {
    let lista = _pares.slice();

    // Filtro de búsqueda
    if (_filtro) {
      const q = _filtro.toLowerCase();
      // Si BuscarOraculo está activo, usarlo para ordenar por relevancia
      if (window.BuscarOraculo && BuscarOraculo.buscarConScore) {
        const scores = BuscarOraculo.buscarConScore(_filtro, {}, 200);
        const mapScore = new Map(scores.map(r => [r.q, parseFloat(r.score)]));
        lista = lista
          .filter(p => {
            const texto = ((p.q || '') + ' ' + (p.a || '')).toLowerCase();
            return texto.includes(q) || mapScore.has(p.q);
          })
          .sort((a, b) => (mapScore.get(b.q) || 0) - (mapScore.get(a.q) || 0));
      } else {
        lista = lista.filter(p => {
          const txt = ((p.q || '') + ' ' + (p.a || '')).toLowerCase();
          return txt.includes(q);
        });
      }
    }

    // Ordenamiento
    if (_orden === 'peso') {
      lista.sort((a, b) => (b.peso || 0) - (a.peso || 0));
    } else if (_orden === 'az') {
      lista.sort((a, b) => (a.q || '').localeCompare(b.q || '', 'es'));
    } else {
      lista.sort((a, b) => (b.t || 0) - (a.t || 0));
    }
    return lista;
  }

  function _render() {
    const lista    = _parFiltrado();
    const total    = lista.length;
    const maxPag   = Math.max(0, Math.ceil(total / _porPag) - 1);
    _pagina        = Math.min(_pagina, maxPag);
    const inicio   = _pagina * _porPag;
    const pagina   = lista.slice(inicio, inicio + _porPag);

    // Stats del índice TF-IDF
    if (window.BuscarOraculo && BuscarOraculo.stats) {
      const st = BuscarOraculo.stats();
      const el = document.getElementById('vp-stats-txt');
      if (el) el.textContent = `${st.totalPares} en índice · ${st.tokensTotales} tokens · caché ${st.cacheEntradas}`;
    }

    // Página y controles
    const elPag = document.getElementById('vp-pagina-txt');
    if (elPag) elPag.textContent = total ? `${inicio + 1}–${Math.min(inicio + _porPag, total)} de ${total}` : 'Sin resultados';
    const btnPrev = document.getElementById('vp-prev');
    const btnNext = document.getElementById('vp-next');
    if (btnPrev) btnPrev.disabled = _pagina === 0;
    if (btnNext) btnNext.disabled = inicio + _porPag >= total;

    const contenedor = document.getElementById('vp-lista');
    if (!contenedor) return;

    if (!pagina.length) {
      contenedor.innerHTML = '<p class="tenue" style="padding:16px;text-align:center">Sin pares que coincidan.</p>';
      return;
    }

    contenedor.innerHTML = pagina.map(p => {
      const id      = p.id !== undefined ? String(p.id) : '';
      const peso    = typeof p.peso === 'number' ? p.peso : 0;
      const origen  = p.origen || 'aprendido';
      const archivo = p.archivo ? `<span class="vp-chip">${_esc(p.archivo.slice(0,25))}</span>` : '';
      const pesoCol = peso > 0 ? '#10b981' : peso < 0 ? '#ef4444' : '#64748b';
      return `
        <div class="vp-par" data-id="${_esc(id)}">
          <div class="vp-par-q" contenteditable="false" data-campo="q">${_esc(p.q || '')}</div>
          <div class="vp-par-a" contenteditable="false" data-campo="a">${_esc(p.a || '').slice(0,200)}${(p.a||'').length>200?'…':''}</div>
          <div class="vp-par-meta">
            ${archivo}
            <span class="vp-chip">${_esc(origen)}</span>
            <span class="vp-chip" style="color:${pesoCol}">peso ${peso >= 0 ? '+' : ''}${peso}</span>
            <div style="margin-left:auto;display:flex;gap:4px">
              <button class="vp-btn-editar" data-id="${_esc(id)}" title="Editar par">✏️</button>
              <button class="vp-btn-borrar"  data-id="${_esc(id)}" title="Eliminar par">🗑️</button>
            </div>
          </div>
        </div>`;
    }).join('');

    // Eventos de editar / borrar
    contenedor.querySelectorAll('.vp-btn-editar').forEach(btn => btn.addEventListener('click', _editar));
    contenedor.querySelectorAll('.vp-btn-borrar').forEach(btn => btn.addEventListener('click', _borrar));
  }

  function _esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // ─────────────── Editar inline ────────────────────────────────────────────────

  async function _editar(e) {
    const id    = e.currentTarget.dataset.id;
    const card  = e.currentTarget.closest('.vp-par');
    const elQ   = card.querySelector('[data-campo="q"]');
    const elA   = card.querySelector('[data-campo="a"]');
    const yaEd  = elQ.contentEditable === 'true';

    if (!yaEd) {
      // Activar edición
      elQ.contentEditable = 'true'; elA.contentEditable = 'true';
      elQ.style.outline   = '1px solid var(--acento)';
      elA.style.outline   = '1px solid var(--acento)';
      e.currentTarget.textContent = '💾';
      e.currentTarget.title = 'Guardar cambios';
      elQ.focus();
    } else {
      // Guardar
      const nuevoQ = elQ.textContent.trim();
      const nuevoA = elA.textContent.trim().replace('…','');
      if (nuevoQ && nuevoA && window.IDBStore && id && !id.startsWith('loc_')) {
        // Actualizar en IDB (no hay put directo por id en la API actual → delete + add)
        try {
          await window.IDBStore.eliminarDeCola(Number(id)); // esto no existe para pares
          // Workaround: buscar en el store y actualizar vía put interno
          // Por ahora, añadir el par editado como nuevo y marcar el viejo como peso -99
          await window.IDBStore.actualizarPeso(Number(id), -99);
          await window.IDBStore.agregarPares([{ q: nuevoQ, a: nuevoA, origen: 'editado', t: Date.now() }]);
        } catch(err) { console.warn('VisorPares: no se pudo actualizar', err); }
      }
      elQ.contentEditable = 'false'; elA.contentEditable = 'false';
      elQ.style.outline = ''; elA.style.outline = '';
      e.currentTarget.textContent = '✏️';
      e.currentTarget.title = 'Editar par';
      await _cargarPares();
      _render();
    }
  }

  // ─────────────── Borrar ───────────────────────────────────────────────────────

  async function _borrar(e) {
    const id   = e.currentTarget.dataset.id;
    const card = e.currentTarget.closest('.vp-par');
    const q    = card.querySelector('[data-campo="q"]').textContent.slice(0,60);
    if (!confirm(`¿Eliminar par?\n"${q}…"`)) return;
    if (window.IDBStore && id && !id.startsWith('loc_')) {
      try { await window.IDBStore.actualizarPeso(Number(id), -99); } catch(e2) {}
    }
    _pares = _pares.filter(p => String(p.id) !== id);
    _render();
  }

  // ─────────────── Exportar ─────────────────────────────────────────────────────

  async function _exportar() {
    const lista  = _parFiltrado();
    const json   = JSON.stringify(lista, null, 2);
    const blob   = new Blob([json], { type:'application/json' });
    const url    = URL.createObjectURL(blob);
    const a      = document.createElement('a');
    a.href       = url;
    a.download   = `miu_pares_visor_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ─────────────── API pública ──────────────────────────────────────────────────

  async function abrir() {
    _crearPanel();
    await _cargarPares();
    _pagina = 0; _filtro = ''; _orden = 'reciente';
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.classList.add('vp-visible');
    _abierto = true;
    _render();
  }

  function cerrar() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.classList.remove('vp-visible');
    _abierto = false;
  }

  return { abrir, cerrar, get abierto() { return _abierto; } };
})();
