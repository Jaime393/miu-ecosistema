// idb-store.js — Almacén IndexedDB para Micelio MIU v12 (Phase D.2)
// Reemplaza el límite duro de localStorage (5-10 MB) para oraculo_extension y la cola
// de procesamiento. localStorage queda solo para config, Ki/D_f e historial reciente.
//
// Stores:
//   pares      — pares {q, a, origen, archivo, t, peso} aprendidos de archivos
//   cola       — tareas de procesamiento de archivos {nombre, estado, total, procesado, t}
//   meta       — clave/valor genérico (stats, etc.)
//   embeddings — índice semántico (Phase D.2): { id (=par.id), emb: ArrayBuffer Float16 }
//
// Compresión (v11):
//   Los campos q+a de cada par se comprimen con gzip (CompressionStream API, sin libs)
//   antes de guardarse en IDB y se descomprimen al leer. El resto de campos (archivo,
//   peso, origen, t) permanecen sin comprimir para que los índices IDB sigan funcionando.
//   Formato almacenado: { id, _c: ArrayBuffer, archivo, peso, origen, t }
//   Formato devuelto:   { id, q, a, archivo, peso, origen, t }
//   Ganancia esperada: ~15 MB → ~4-5 MB para 50k pares a ~300 bytes c/u.
//   Migración: al abrir la BD se detectan registros viejos (con q en plano) y se
//   recomprimen automáticamente. Idempotente.
//
// Índice semántico (v12 / Phase D.2):
//   Store 'embeddings': { id (mismo keyPath que pares), emb: ArrayBuffer }
//   emb = Float16Array de 384 dims (768 bytes/par).
//   Escritura vía embed-worker.js (background, no bloquea UI).
//   Lectura vía obtenerEmbeddings() → Uint16Array[] que BuscarOraculo convierte a Float32.
//   Los embeddings NO se comprimen (datos binarios densos; gzip ayuda <5%).
//
// API síncrona imposible con IDB, así que todo es async.
// El arranque de FranBotCore espera a que la BD esté lista antes de continuar.

window.IDBStore = (function () {
  'use strict';

  const DB_NAME    = 'miu_db';
  const DB_VERSION = 2; // v12: agrega store 'embeddings' (Phase D.2)
  let _db = null;

  // ──────────────────────── CompressionStream helpers ────────────────────────────

  /** Comprime un string UTF-8 con gzip → ArrayBuffer */
  async function compress(str) {
    try {
      const bytes  = new TextEncoder().encode(str);
      const stream = new CompressionStream('gzip');
      const writer = stream.writable.getWriter();
      await writer.write(bytes);
      await writer.close();
      return new Response(stream.readable).arrayBuffer();
    } catch (e) {
      console.error('IDBStore: compress error', e);
      throw e;
    }
  }

  /** Descomprime un ArrayBuffer gzip → string UTF-8 */
  async function decompress(buf) {
    try {
      const stream = new DecompressionStream('gzip');
      const writer = stream.writable.getWriter();
      // IDB puede devolver ArrayBuffer o Uint8Array según el motor
      await writer.write(buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf);
      await writer.close();
      return new Response(stream.readable).text();
    } catch (e) {
      console.error('IDBStore: decompress error', e);
      throw e;
    }
  }

  // ──────────────────── Serialización / deserialización de pares ─────────────────

  /**
   * Serializa un par {q, a, ...} para guardarlo en IDB:
   *   - Comprime {q, a} en _c (gzip ArrayBuffer)
   *   - Mantiene {origen, archivo, t, peso} en plano (para índices y queries)
   */
  async function _serializarPar(p) {
    const _c = await compress(JSON.stringify({ q: p.q.trim(), a: p.a.trim() }));
    return {
      _c,
      origen:  p.origen  || 'aprendido',
      archivo: p.archivo || '',
      t:       p.t       || Date.now(),
      peso:    p.peso    || 0,
    };
  }

  /**
   * Deserializa un registro IDB → par {q, a, id, origen, archivo, t, peso}.
   * Compatible con el formato viejo (q/a en plano) para la ventana de transición.
   */
  async function _deserializarPar(rec) {
    if (!rec) return null;
    // Formato viejo (sin comprimir): q y a están en plano
    if (typeof rec.q === 'string') return rec;
    // Formato nuevo: q y a comprimidos en _c
    if (rec._c) {
      const texto   = await decompress(rec._c);
      const { q, a } = JSON.parse(texto);
      return { id: rec.id, q, a, origen: rec.origen, archivo: rec.archivo, t: rec.t, peso: rec.peso };
    }
    return rec; // fallback defensivo
  }

  // ──────────────────── Migración de registros sin comprimir ─────────────────────

  /**
   * Detecta pares en formato viejo (campo q en plano) y los reescribe
   * en formato gzip. Se llama una vez en open(). Idempotente.
   * Si falla, open() sigue adelante igual (no es bloqueante).
   */
  async function _migrarCompresion() {
    const recs = await new Promise((res, rej) => {
      try {
        const t   = _db.transaction(['pares'], 'readonly');
        const req = t.objectStore('pares').getAll();
        req.onsuccess = () => res(req.result);
        req.onerror   = () => rej(req.error);
      } catch (e) { rej(e); }
    });

    const sinComprimir = recs.filter(r => typeof r.q === 'string');
    if (sinComprimir.length === 0) return 0;

    console.log(`IDBStore: migrando ${sinComprimir.length} pares al formato gzip…`);

    // Comprimir en bloques de 500 para no crear miles de streams simultáneos
    const CHUNK  = 500;
    const nuevos = [];
    for (let i = 0; i < sinComprimir.length; i += CHUNK) {
      const parte = sinComprimir.slice(i, i + CHUNK);
      const comprimidos = await Promise.all(parte.map(async r => {
        const _c = await compress(JSON.stringify({ q: r.q, a: r.a }));
        return { id: r.id, _c, origen: r.origen, archivo: r.archivo, t: r.t, peso: r.peso };
      }));
      nuevos.push(...comprimidos);
    }

    // Reescribir en una sola transacción
    await new Promise((res, rej) => {
      try {
        const t = _db.transaction(['pares'], 'readwrite');
        const s = t.objectStore('pares');
        nuevos.forEach(r => s.put(r));
        t.oncomplete = () => res(nuevos.length);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    });

    console.log(`IDBStore: ${nuevos.length} pares migrados a compresión gzip (q+a).`);
    return nuevos.length;
  }

  // ──────────────────────────────────── open ────────────────────────────────────
  function open() {
    if (_db) return Promise.resolve(_db);
    return new Promise((res, rej) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);

      req.onupgradeneeded = function (e) {
        const db = e.target.result;
        // pares: índice por archivo para poder borrar por origen
        if (!db.objectStoreNames.contains('pares')) {
          const s = db.createObjectStore('pares', { keyPath: 'id', autoIncrement: true });
          s.createIndex('por_archivo', 'archivo', { unique: false });
          s.createIndex('por_peso',    'peso',    { unique: false });
        }
        if (!db.objectStoreNames.contains('cola')) {
          const c = db.createObjectStore('cola', { keyPath: 'id', autoIncrement: true });
          c.createIndex('por_estado', 'estado', { unique: false });
        }
        if (!db.objectStoreNames.contains('meta')) {
          db.createObjectStore('meta', { keyPath: 'clave' });
        }
        // v12 (Phase D.2): store de embeddings semánticos pre-computados
        // keyPath 'id' = mismo id que el par en el store 'pares' — 1:1 por diseño.
        // emb: ArrayBuffer con Float16Array de 384 dims (768 bytes/par).
        if (!db.objectStoreNames.contains('embeddings')) {
          db.createObjectStore('embeddings', { keyPath: 'id' });
        }
      };

      req.onsuccess = function (e) {
        _db = e.target.result;
        // Migrar pares viejos (q en plano) → formato gzip. No crítico si falla.
        _migrarCompresion()
          .then(()    => res(_db))
          .catch(err  => {
            console.warn('IDBStore: migración de compresión fallida (no crítico):', err);
            res(_db); // abre de todas formas
          });
      };

      req.onerror = function (e) {
        console.error('IDBStore: error al abrir BD', e);
        rej(e);
      };
    });
  }

  // ──────────────────────────────── helpers ─────────────────────────────────────
  function tx(store, mode) {
    return _db.transaction([store], mode).objectStore(store);
  }

  function promReq(req) {
    return new Promise((res, rej) => {
      req.onsuccess = () => res(req.result);
      req.onerror   = ()  => rej(req.error);
    });
  }

  function promTx(store, mode, fn) {
    return open().then(() => {
      try {
        const s = tx(store, mode);
        return fn(s);
      } catch(e) {
        console.warn('IDBStore promTx error (' + store + '/' + mode + '):', e);
        return Promise.reject(e);
      }
    });
  }

  // ──────────────────────────────── PARES ───────────────────────────────────────

  /** Devuelve todos los pares (descomprimidos; puede ser lento con muchos) */
  async function todosLosPares() {
    const recs = await promTx('pares', 'readonly', s => promReq(s.getAll()));
    return Promise.all(recs.map(_deserializarPar));
  }

  /**
   * Añade un array de pares nuevos.
   * Pre-comprime q+a ANTES de abrir la transacción IDB: no se puede await
   * dentro de una transacción activa (el motor la cierra ante inactividad).
   */
  async function agregarPares(pares) {
    if (!pares || !pares.length) return 0;

    const validos = pares.filter(p => p && typeof p.q === 'string' && typeof p.a === 'string');
    if (!validos.length) return 0;

    const items = await Promise.all(validos.map(_serializarPar));

    return open().then(() => new Promise((res, rej) => {
      try {
        const t = _db.transaction(['pares'], 'readwrite');
        const s = t.objectStore('pares');
        // Capturar el id autoincremental asignado por IDB a cada item
        items.forEach((item, i) => {
          const req = s.add(item);
          req.onsuccess = e => { items[i]._idb_id = e.target.result; };
        });
        t.oncomplete = () => res(items);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    }));
  }

  /**
   * Actualiza el peso de un par por su id.
   * Solo toca el campo peso; _c (contenido comprimido) no se modifica.
   */
  function actualizarPeso(id, delta) {
    return promTx('pares', 'readwrite', s => new Promise((res, rej) => {
      const req = s.get(Number(id));
      req.onsuccess = () => {
        const par = req.result;
        if (!par) return res(false);
        par.peso = (par.peso || 0) + delta;
        const r = s.put(par); // _c no se toca — sigue igual
        r.onsuccess = () => res(true);
        r.onerror   = ()  => rej(r.error);
      };
      req.onerror = () => rej(req.error);
    }));
  }

  /** Elimina todos los pares con peso ≤ umbral (poda) */
  function podarParesPorPeso(umbral) {
    umbral = (typeof umbral === 'number') ? umbral : -3;
    return open().then(() => new Promise((res, rej) => {
      try {
        const t     = _db.transaction(['pares'], 'readwrite');
        const s     = t.objectStore('pares');
        const idx   = s.index('por_peso');
        const range = IDBKeyRange.upperBound(umbral, false); // peso <= umbral
        let eliminados = 0;
        const cursor = idx.openCursor(range);
        cursor.onsuccess = function (e) {
          const c = e.target.result;
          if (c) { c.delete(); eliminados++; c.continue(); }
        };
        t.oncomplete = () => res(eliminados);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    }));
  }

  /** Elimina todos los pares de un archivo (por nombre) */
  function eliminarParesPorArchivo(nombreArchivo) {
    return open().then(() => new Promise((res, rej) => {
      try {
        const t   = _db.transaction(['pares'], 'readwrite');
        const s   = t.objectStore('pares');
        const idx = s.index('por_archivo');
        const cur = idx.openCursor(IDBKeyRange.only(nombreArchivo));
        let eliminados = 0;
        cur.onsuccess = function (e) {
          const c = e.target.result;
          if (c) { c.delete(); eliminados++; c.continue(); }
        };
        t.oncomplete = () => res(eliminados);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    }));
  }

  /** Cuenta total de pares */
  function contarPares() {
    return promTx('pares', 'readonly', s => promReq(s.count()));
  }

  // ──────────────────────────────── COLA ───────────────────────────────────────
  // Las tareas de cola son metadatos pequeños (nombre, estado, progreso):
  // no se comprimen — la ganancia sería mínima y complejizaría el código sin sentido.

  /** Encola un archivo para procesamiento posterior */
  function encolar(entrada) {
    const tarea = Object.assign({ estado: 'pendiente', total: 0, procesado: 0, t: Date.now() }, entrada);
    return promTx('cola', 'readwrite', s => promReq(s.add(tarea)));
  }

  /** Actualiza el estado/progreso de una tarea */
  function actualizarCola(id, cambios) {
    return promTx('cola', 'readwrite', s => new Promise((res, rej) => {
      const req = s.get(Number(id));
      req.onsuccess = () => {
        const tarea = req.result;
        if (!tarea) return res(false);
        Object.assign(tarea, cambios);
        const r = s.put(tarea);
        r.onsuccess = () => res(true);
        r.onerror   = ()  => rej(r.error);
      };
      req.onerror = () => rej(req.error);
    }));
  }

  /** Devuelve todas las tareas de la cola */
  function obtenerCola() {
    return promTx('cola', 'readonly', s => promReq(s.getAll()));
  }

  /** Borra una tarea de la cola por id */
  function eliminarDeCola(id) {
    return promTx('cola', 'readwrite', s => promReq(s.delete(Number(id))));
  }

  /** Borra tareas completadas (limpieza) */
  function limpiarColaCompletada() {
    return open().then(() => new Promise((res, rej) => {
      try {
        const t   = _db.transaction(['cola'], 'readwrite');
        const s   = t.objectStore('cola');
        const idx = s.index('por_estado');
        const cur = idx.openCursor(IDBKeyRange.only('completo'));
        let n = 0;
        cur.onsuccess = function (e) {
          const c = e.target.result;
          if (c) { c.delete(); n++; c.continue(); }
        };
        t.oncomplete = () => res(n);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    }));
  }

  // ──────────────────────────────── META ───────────────────────────────────────

  function getMeta(clave) {
    return promTx('meta', 'readonly', s => promReq(s.get(clave))).then(r => r ? r.valor : null);
  }

  function setMeta(clave, valor) {
    return promTx('meta', 'readwrite', s => promReq(s.put({ clave, valor })));
  }

  // ──────────────────── Migración desde localStorage ────────────────────────────
  /** Mueve oraculo_extension de localStorage a IDB si existe y es grande.
   *  Llamar una vez al arrancar, antes de reproducirExtension().
   *  agregarPares() comprime q+a automáticamente al insertar. */
  async function migrarDesdeLocalStorage() {
    try {
      const raw = localStorage.getItem('miu_estado');
      if (!raw) return 0;
      const estado = JSON.parse(raw);
      const ext    = estado.oraculo_extension;
      if (!Array.isArray(ext) || ext.length === 0) return 0;

      await open();
      const yaEnIDB = await contarPares();

      // Solo migrar si IDB está vacía (primera vez)
      if (yaEnIDB === 0 && ext.length > 0) {
        const guardados = await agregarPares(ext);
        const n = Array.isArray(guardados) ? guardados.length : guardados;
        // Vaciar del estado localStorage para liberar espacio
        estado.oraculo_extension = [];
        localStorage.setItem('miu_estado', JSON.stringify(estado));
        console.log(`IDBStore: migrados ${n} pares de localStorage → IndexedDB (comprimidos)`);
        return n;
      }
      return 0;
    } catch (e) {
      console.warn('IDBStore: migración desde localStorage fallida (no crítico)', e);
      return 0;
    }
  }

  // ──────────────────────────── EMBEDDINGS (Phase D.2) ─────────────────────────
  // Cada registro: { id (= par.id), emb: ArrayBuffer (Float16Array serializado) }
  // Escritura en lotes desde embed-worker.js para no bloquear la UI.
  // Lectura en bloque completo al arrancar buscarSemantico().

  /**
   * Guarda un lote de embeddings en IDB.
   * @param {Array<{id: number, emb: ArrayBuffer}>} lote - Array de registros.
   * Pre-condición: emb ya es un ArrayBuffer de Float16Array serializado.
   * No hace await dentro de la transacción — los ArrayBuffer se pasan directamente.
   */
  function guardarEmbeddings(lote) {
    if (!lote || !lote.length) return Promise.resolve(0);
    return open().then(() => new Promise((res, rej) => {
      try {
        const t = _db.transaction(['embeddings'], 'readwrite');
        const s = t.objectStore('embeddings');
        lote.forEach(r => s.put(r)); // put = upsert por keyPath id
        t.oncomplete = () => res(lote.length);
        t.onerror    = () => rej(t.error);
      } catch (e) { rej(e); }
    }));
  }

  /**
   * Devuelve todos los registros de embeddings como array de {id, emb: ArrayBuffer}.
   * Puede ser grande (50k × 768 B ≈ 38 MB en memoria) — llamar solo al iniciar el índice.
   */
  function obtenerEmbeddings() {
    return promTx('embeddings', 'readonly', s => promReq(s.getAll()));
  }

  /** Cuenta embeddings indexados (para stats y progreso). */
  function contarEmbeddings() {
    return promTx('embeddings', 'readonly', s => promReq(s.count()));
  }

  /**
   * Borra todos los embeddings del store (para re-indexar desde cero).
   * Útil si se actualiza el modelo o se agrega un lote grande de pares nuevos.
   */
  function limpiarEmbeddings() {
    return promTx('embeddings', 'readwrite', s => promReq(s.clear()));
  }

  // ──────────────────────────────── export ─────────────────────────────────────
  return {
    open,
    // pares
    todosLosPares, agregarPares, actualizarPeso,
    podarParesPorPeso, eliminarParesPorArchivo, contarPares,
    // cola
    encolar, actualizarCola, obtenerCola, eliminarDeCola, limpiarColaCompletada,
    // meta
    getMeta, setMeta,
    // embeddings (Phase D.2)
    guardarEmbeddings, obtenerEmbeddings, contarEmbeddings, limpiarEmbeddings,
    // migración
    migrarDesdeLocalStorage,
  };
})();
