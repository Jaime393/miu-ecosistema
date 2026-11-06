// buscar-oraculo.js v5+F — Motor semántico MIU + BM25 + Índice invertido + Caché LRU
//                          + Reranking semántico con transformers.js (Phase D.1)
//                          + Índice semántico pre-computado Float16 en IDB (Phase D.2)
//                          + Calibración factor de fusión semántico/BM25 (Task F)
// Retro-compatible: misma API pública que v1/v2 (iniciar, preguntar, agregarPares, idDe)
// Nuevos métodos: iniciarConIDB(), _construirIndice(), buscarConScore()
//
// Task F — constantes de fusión semántica/BM25:
//   SEM_PESO         → escala coseno (0-1) a rango BM25 (0-~15). Factor 10 equipara
//                       medias empíricas (~0.6 × 10 ≈ 6 vs ~6 BM25 típico).
//   SEM_UMBRAL       → descarta candidatos con coseno < umbral antes de fusionar.
//                       Evita que matches de ruido suman puntos espurios al score.
//   SEM_BOOST_ALTO   → bonus para matches de muy alta confianza (coseno > SEM_BOOST_UMBRAL).
//                       Asegura que respuestas semánticamente casi idénticas ganen
//                       sobre matches BM25 parciales cuando el modelo está seguro.
//
// Tuning post-producción:
//   · Si aparecen falsos positivos semánticos: subir SEM_UMBRAL a 0.25–0.30.
//   · Si BM25 gana cuando no debería (vocabulario técnico inusual): subir SEM_PESO a 12.
//   · Si resultados semánticos parecen débiles: bajar SEM_BOOST_UMBRAL a 0.65.
//
// Estrategia de búsqueda (por prioridad):
//   1. Motor MIU axiomático (MIU.consultar)
//   2. Índice invertido BM25 sobre todos los pares (base + extensión + IDB)
//      BM25 (Okapi BM25) supera a TF-IDF puro en textos cortos (Q&A):
//      - TF saturado: dos menciones de un token no valen el doble (k1=1.5)
//      - Normalización por longitud: respuestas largas no dominan (b=0.75)
//      - avgdl calculado dinámicamente al construir el índice
//   3. Fallback lineal clásico si el índice no está listo
//
// Complejidad: O(k log n) donde k = tokens de la query + LRU cache O(1)

function _decodificarOraculoBase64(b64) {
  const binario = atob(b64);
  const bytes = Uint8Array.from(binario, c => c.charCodeAt(0));
  return new TextDecoder('utf-8').decode(bytes);
}

window.BuscarOraculo = (function () {
  'use strict';

  // ─────────────── Estado interno ───────────────────────────────────────────────
  let _pares  = [];        // array maestro: base + extension + IDB
  let _listo  = false;
  let _indice = null;      // { token → Set<idx> }
  let _idf    = null;      // { token → número } — IDF clásico para BM25
  let _tf_doc = null;      // { idx → { token → frecuencia_normalizada } } — TF por doc
  let _dl     = null;      // { idx → longitud en tokens del doc }
  let _avgdl  = 0;         // longitud media de documento (calculada al construir índice)
  let _indiceValido = false;
  let _indice_q   = null;   // Set-like object de tokens presentes en campo q — filtro dominio

  // ─────────────── Estado del embedder semántico (Phase D.1) ───────────────────
  // _embedder: pipeline de feature-extraction de transformers.js, o null si no disponible.
  // Se carga en background al final de iniciarConIDB() — no bloquea el arranque.
  let _embedder = null;

  // ─────────────── Índice semántico pre-computado (Phase D.2) ──────────────────
  // _idxEmbs: Array<{ id, emb: Float32Array }> cargado desde IDB al arranque.
  // _parPorId: Map<id → par> para resolver id → {q,a} sin buscar en _pares.
  // Una vez cargado, buscarSemantico() hace búsqueda lineal coseno sobre todos los pares
  // sin pasar por BM25. Si el índice no está listo, delega en buscarConScoreSemantico().
  let _idxEmbs   = null;  // null = no cargado, [] = vacío pero intentado
  let _parPorId  = null;  // Map<id → par> — se reconstruye junto con _idxEmbs

  // Parámetros BM25 estándar (Okapi BM25)
  // k1=1.5: saturación de TF (0→sin saturación, ∞→TF lineal); 1.2–2.0 es el rango habitual
  // b=0.75: normalización por longitud de doc (0→sin normalizar, 1→normalización total)
  const BM25_K1 = 1.5;
  const BM25_B  = 0.75;

  // ─── Parámetros de fusión semántica/BM25 (Task F — calibración) ───────────
  // Ver guía de tuning en el encabezado del archivo.
  const SEM_PESO         = 10;    // escala coseno (0–1) → rango BM25 (0–~15)
  const SEM_UMBRAL       = 0.20;  // coseno mínimo aceptable; por debajo = ruido
  const SEM_BOOST_ALTO   = 3;     // puntos extra si coseno > SEM_BOOST_UMBRAL
  const SEM_BOOST_UMBRAL = 0.75;  // umbral de "match de alta confianza"

  // LRU cache — 64 entradas, evita recalcular queries repetidas
  const CACHE_MAX = 64;
  const _cache = new Map();
  function _cacheGet(key) {
    if (!_cache.has(key)) return undefined;
    const val = _cache.get(key);
    _cache.delete(key); _cache.set(key, val); // mover al final (LRU)
    return val;
  }
  function _cacheSet(key, val) {
    if (_cache.size >= CACHE_MAX) _cache.delete(_cache.keys().next().value);
    _cache.set(key, val);
  }
  function _cacheInvalidar() { _cache.clear(); }

  // ─────────────── Tokenización ─────────────────────────────────────────────────
  // Stop-words en español — no aportan discriminación semántica
  const STOP = new Set([
    'de','la','el','en','y','a','que','es','se','del','los','las','un','una',
    'con','por','para','como','más','pero','si','lo','le','su','sus','no','al',
    'me','mi','te','tu','yo','él','qué','cómo','cuál','cuándo','donde','o',
    'hay','muy','todo','esta','este','son','fue','ser','estar','ha','han',
    'era','sido','tiene','también','ya','sobre','desde','hasta','entre'
  ]);

  function _tokenizar(texto) {
    return texto
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // quitar tildes para matching robusto
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter(t => t.length > 2 && !STOP.has(t));
  }

  // Bigramas: "materia oscura" → token compuesto que mejora precision
  function _bigramas(tokens) {
    const bg = [];
    for (let i = 0; i < tokens.length - 1; i++) bg.push(tokens[i] + '_' + tokens[i+1]);
    return bg;
  }

  function _tokensCompletos(texto) {
    const base = _tokenizar(texto);
    return base.concat(_bigramas(base));
  }

  // ─────────────── Construcción del índice BM25 ────────────────────────────────
  function _construirIndice() {
    const n = _pares.length;
    if (n === 0) { _indiceValido = false; return; }

    const idx  = Object.create(null);  // token → Set<docIdx>
    const df   = Object.create(null);  // token → doc frequency
    const tf   = [];                   // tf[docIdx] = { token → count_raw }
    const dl   = new Float32Array(n);  // longitud en tokens de cada doc

    let totalTokens = 0;

    for (let i = 0; i < n; i++) {
      const p      = _pares[i];
      // Peso mayor a la pregunta que a la respuesta (2:1) — en Q&A la pregunta
      // es el descriptor más discriminante del par
      const tokens = _tokensCompletos((p.q || '') + ' ' + (p.q || '') + ' ' + (p.a || ''));
      const tfDoc  = Object.create(null);
      const vistos = new Set();

      tokens.forEach(t => {
        tfDoc[t] = (tfDoc[t] || 0) + 1;
        if (!idx[t]) idx[t] = new Set();
        idx[t].add(i);
        if (!vistos.has(t)) { df[t] = (df[t] || 0) + 1; vistos.add(t); }
      });

      tf.push(tfDoc);
      dl[i] = tokens.length;
      totalTokens += tokens.length;
    }

    // IDF con suavizado Robertson (evita log negativo con df=n)
    // IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
    const idf = Object.create(null);
    Object.keys(df).forEach(t => {
      const dft = df[t];
      idf[t] = Math.log((n - dft + 0.5) / (dft + 0.5) + 1);
    });

    _indice   = idx;
    _idf      = idf;
    _tf_doc   = tf;
    _dl       = dl;
    _avgdl    = totalTokens / n;
    _indiceValido = true;

    // ── Índice de dominio: tokens en campo q (preguntas) únicamente ──────────
    // Objeto {token: true} — solo presencia. Usado por _coberturaPreguntas().
    const idx_q = Object.create(null);
    for (let i = 0; i < n; i++) {
      _tokenizar((_pares[i].q || '')).forEach(t => { idx_q[t] = true; });
    }
    _indice_q = idx_q;

    _cacheInvalidar();
  }

  // ─────────────── Filtro de relevancia de dominio ──────────────────────────────
  // Calcula fracción de tokens unigramas de la query que aparecen en alguna
  // PREGUNTA del oráculo (campo q). Cobertura 0 → query off-domain → null.
  // No usa bigramas: son demasiado específicos y generarían falsos negativos.
  //
  // Ejemplos calibración Ciclo AB:
  //   "receta de paella valenciana" → 0/3 → null ✓
  //   "cómo cambio una llanta"      → 0/3 → null ✓
  //   "cuál es la capital de Mongolia" → depende de si "capital" está en alguna q
  //   "qué es la coherencia"        → 1/1 → pasa ✓
  //   "qué es la materia oscura"    → 2/2 → pasa ✓
  function _coberturaPreguntas(queryTokens) {
    if (!_indice_q) return 1; // sin índice → no filtrar (seguro)
    const unigramas = queryTokens.filter(t => !t.includes('_'));
    if (!unigramas.length) return 1;
    const encontrados = unigramas.filter(t => _indice_q[t]).length;
    return encontrados / unigramas.length;
  }

  // ─────────────── Sinonimia axiomática MIU ─────────────────────────────────────
  // Expande la query con conceptos del Códice para mejor recall semántico
  const SINONIMIA = {
    'materia_oscura': ['materia','oscura','cosmologia','galaxia','invisible','pegamento','rho'],
    'felicidad':      ['felicidad','coherencia','hedonica','bienestar','ich','ritmo'],
    'alma':           ['alma','fii','identidad','informacional','firma','persiste','nap'],
    'conciencia':     ['conciencia','phi','integracion','neuronal','phi_miu'],
    'gravedad':       ['gravedad','metrica','emergente','curvatura','flujo'],
    'realidad':       ['realidad','informacion','campo','rho','fundamental'],
    'tiempo':         ['tiempo','flujo','entropia','flecha','evolucion'],
    'amor':           ['amor','resonancia','vinculo','coherencia'],
    'coherencia':     ['coherencia','ki','fractal','df','phi','banda'],
    'micelio':        ['micelio','red','nodo','coneccion','jardin','hifa'],
    'ki':             ['ki','coherencia','phi','df','invariante','calculo'],
    'entropia':       ['entropia','desorden','tiempo','flecha','ds'],
  };

  function _expandirQuery(tokens) {
    const extra = [];
    const joined = tokens.join('_');
    // bigramas primero
    for (const clave in SINONIMIA) {
      if (joined.includes(clave)) {
        extra.push(...SINONIMIA[clave]);
        break;
      }
    }
    // unigramas
    tokens.forEach(t => {
      if (SINONIMIA[t]) extra.push(...SINONIMIA[t]);
    });
    return tokens.concat(extra);
  }

  // ─────────────── Score BM25 (Okapi BM25) ────────────────────────────────────
  // BM25(q,d) = Σ_t [ IDF(t) * (tf(t,d) * (k1+1)) / (tf(t,d) + k1*(1 - b + b*|d|/avgdl)) ]
  function _scoreBM25(queryTokens, pesos) {
    pesos = pesos || {};
    if (!_indiceValido) return null;

    const expandidos = _expandirQuery(queryTokens);
    const candidatos = new Map(); // idx → score BM25 acumulado

    expandidos.forEach((t, qi) => {
      const ids = _indice[t];
      if (!ids) return;
      const idfVal = _idf[t];
      if (!idfVal || idfVal <= 0) return; // token demasiado frecuente (omnipresente)
      // Los tokens originales de la query valen más que los de sinonimia
      const pesoSinonimia = qi < queryTokens.length ? 1.0 : 0.4;

      ids.forEach(idx => {
        const tfRaw = (_tf_doc[idx] && _tf_doc[idx][t]) || 0;
        const docLen = _dl[idx] || 1;
        // Fórmula BM25 canónica
        const tfNorm = (tfRaw * (BM25_K1 + 1)) /
                       (tfRaw + BM25_K1 * (1 - BM25_B + BM25_B * docLen / _avgdl));
        const aporte = idfVal * tfNorm * pesoSinonimia;
        candidatos.set(idx, (candidatos.get(idx) || 0) + aporte);
      });
    });

    if (!candidatos.size) return null;

    const resultados = [];
    candidatos.forEach((sc, idx) => {
      const par  = _pares[idx];
      const voto = pesos[String(idx)] || 0;
      if (voto <= -3) return; // par muy penalizado → descartar

      let score = sc + voto * 4; // boost de voto humano (escala calibrada con BM25)

      // Boost por categoría
      if (par.cat) {
        const catTokens = par.cat.replace(/_/g,' ').split(' ');
        if (catTokens.some(ct => queryTokens.includes(ct))) score += 1.5;
      }

      // Bonus por match literal exacto en la pregunta (muy discriminante)
      const qNorm    = _normalizar(par.q || '');
      const entrada  = queryTokens.join(' ');
      if (qNorm.includes(entrada)) score += 8;

      // Penalización respuestas muy cortas
      if ((par.a || '').length < 60) score -= 2;

      // Penalización por query muy larga (Tipo B: preguntas discursivas ~367 pares)
      // Si queryTokens.length > 20, penalizar gradualmente (queries largas tienden a hacer false positives)
      if (queryTokens.length > 20) {
        const penalty = Math.min(4, (queryTokens.length - 20) * 0.1);
        score -= penalty;
      }

      resultados.push({ idx, par, score });
    });

    resultados.sort((a, b) => b.score - a.score);
    return resultados;
  }

  // Alias interno para compatibilidad con llamadas a _scoreTFIDF en buscarConScore
  function _scoreTFIDF(queryTokens, pesos) { return _scoreBM25(queryTokens, pesos); }

  function _normalizar(s) {
    return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9\s]/g,' ').trim();
  }

  // ─────────────── API pública ──────────────────────────────────────────────────

  function iniciar() {
    if (_listo) return;
    try {
      let motor = null;
      if (window.ORACULO_JSON)        motor = window.ORACULO_JSON;
      else if (window.ORACULO_BASE64) motor = JSON.parse(_decodificarOraculoBase64(window.ORACULO_BASE64));
      if (motor && Array.isArray(motor.pares)) {
        _pares = motor.pares.slice();
        _listo = true;
        _construirIndice();
        const ver = motor.version ? ' v' + motor.version : '';
        const cat = motor.categorias ? ' · ' + motor.categorias.length + ' categorías' : '';
        console.log('🔮 Oráculo' + ver + ': ' + _pares.length + ' pares' + cat + ' · índice BM25 listo');
      }
    } catch (e) { console.error('Oráculo: error al iniciar', e); }
  }

  /** Carga pares adicionales desde IndexedDB (async, llamar después de iniciar()) */
  async function iniciarConIDB() {
    if (!window.IDBStore) return 0;
    // Asegurar que el oráculo base ya esté cargado antes de agregar pares IDB
    if (!_listo) iniciar();
    try {
      await window.IDBStore.open();
      const paresIDB = await window.IDBStore.todosLosPares();
      if (!paresIDB || !paresIDB.length) return 0;
      // Agregar solo los que no están ya (deduplicar por q normalizada)
      const existentes = new Set(_pares.map(p => _normalizar(p.q || '')));
      let nuevos = 0;
      paresIDB.forEach(p => {
        if (p && typeof p.q === 'string' && !existentes.has(_normalizar(p.q))) {
          _pares.push({ q: p.q, a: p.a, origen: p.origen || 'idb', _idb_id: p.id });
          existentes.add(_normalizar(p.q));
          nuevos++;
        }
      });
      if (nuevos > 0) _construirIndice();
      console.log('🔮 Oráculo IDB: +'  + nuevos + ' pares desde IndexedDB → total=' + _pares.length);
      // Iniciar embedder en background sin bloquear el retorno — fallback a BM25 si falla
      _iniciarEmbedder().catch(() => {});
      return nuevos;
    } catch (e) {
      console.warn('Oráculo: no se pudieron cargar pares desde IDB', e);
      return 0;
    }
  }

  function agregarPares(nuevos) {
    if (!_listo) iniciar();
    if (!Array.isArray(nuevos) || !nuevos.length) return 0;
    const existentes = new Set(_pares.map(p => _normalizar(p.q || '')));
    let n = 0;
    nuevos.forEach(p => {
      if (p && typeof p.q === 'string' && typeof p.a === 'string' &&
          p.q.trim() && p.a.trim() && !existentes.has(_normalizar(p.q))) {
        _pares.push({ q: p.q.trim(), a: p.a.trim(), origen: p.origen || 'aprendido' });
        existentes.add(_normalizar(p.q));
        n++;
      }
    });
    if (n > 0) _construirIndice();
    _cacheInvalidar();
    return n;
  }

  function idDe(textoRespuesta) {
    if (!_listo) iniciar();
    const i = _pares.findIndex(p => p.a === textoRespuesta);
    return i >= 0 ? String(i) : null;
  }

  // ─── COMPOSICIÓN (Ciclo Z: pensar y reorganizar, incluso local) ────────────
  // Antes, el núcleo devolvía el top-1 verbatim de UNA sola fuente (MIU si había
  // match, si no el mejor par del oráculo) y todo lo demás se perdía. Ahora:
  //   · si hay convergencia real entre 2+ fuentes (varios axiomas, o MIU+oráculo
  //     ambos fuertes), se combinan sin redundancia (Jaccard vía Consolidar);
  //   · si solo hay señal débil (real pero bajo el umbral de confianza), se dice
  //     con honestidad en vez de fingir certeza — regla del propio KERNEL.json
  //     ("no alucinar: si no hay dato, declarar NO SÉ");
  //   · si no hay señal alguna, se devuelve null — eso sigue siendo "débil" de
  //     verdad para que core.js decida, y NUNCA se rellena con una coincidencia
  //     inventada. Nada de esto toca buscarConScore/buscarSemantico (RAG API).
  const UMBRAL_BM25_FUERTE   = 0.8;  // (sin cambios — calibración previa intacta)
  const UMBRAL_BM25_BLANDO   = 0.25; // señal real pero floja — no es ruido puro
  const UMBRAL_LINEAL_FUERTE = 10;   // (sin cambios)
  const UMBRAL_LINEAL_BLANDO = 3;
  const MAX_FRAGMENTOS_MIU   = 2;    // tope: no saturar la respuesta de fórmulas
  const SIM_REDUNDANCIA      = 0.5;  // por encima de esto, dos fragmentos dicen "lo mismo"
  // Prefijo del match "blando" (real pero no exacto). Se expone como constante
  // (en vez de dejarlo como string suelto en _componer) para que core.js pueda
  // distinguir confianza real sin duplicar umbrales propios de este módulo.
  const MARCADOR_MATCH_BLANDO = '*Lo más cercano que encuentro — no es una coincidencia exacta:*';

  /** Similitud entre dos fragmentos para no duplicar contenido al componer.
   *  Reusa el Jaccard ya calibrado de Consolidar; si aún no cargó (orden de
   *  scripts), cae a un cálculo mínimo equivalente — mismo patrón que core.js. */
  function _simFragmentos(a, b) {
    if (window.Consolidar && window.Consolidar._jaccardSim) return window.Consolidar._jaccardSim(a, b);
    const tok = s => new Set((s || '').toLowerCase().normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/).filter(t => t.length > 2));
    const A = tok(a), B = tok(b);
    if (!A.size || !B.size) return 0;
    let inter = 0; A.forEach(t => { if (B.has(t)) inter++; });
    return inter / (A.size + B.size - inter);
  }

  /** Une 1–2 fragmentos del motor MIU (ya ordenados por score) sin duplicar. */
  function _unirFragmentosMIU(miuTop) {
    if (!miuTop.length) return '';
    if (miuTop.length === 1) return miuTop[0].texto;
    if (_simFragmentos(miuTop[0].texto, miuTop[1].texto) >= SIM_REDUNDANCIA) return miuTop[0].texto;
    return miuTop.map(m => m.texto).join('\n\n');
  }

  /** Decide cómo combinar los matches del motor MIU con el mejor candidato del
   *  oráculo. candidato = { par, fuerte, blando } | null. */
  function _componer(miuHits, candidato) {
    const miuTop = miuHits.slice().sort((a, b) => b.score - a.score).slice(0, MAX_FRAGMENTOS_MIU);
    const oracleFuerte = !!(candidato && candidato.fuerte);
    const oracleBlando  = !!(candidato && !candidato.fuerte && candidato.blando);

    if (!miuTop.length && !oracleFuerte && !oracleBlando) return null; // sin señal real

    if (!miuTop.length) {
      if (oracleFuerte) return candidato.par.a; // status quo: match único y fuerte
      return MARCADOR_MATCH_BLANDO + '\n\n' + candidato.par.a;
    }

    if (!oracleFuerte) return _unirFragmentosMIU(miuTop); // ignora ruido de oráculo débil

    // Convergencia real: MIU + oráculo, ambos con señal fuerte.
    const miuTexto = _unirFragmentosMIU(miuTop);
    if (_simFragmentos(miuTexto, candidato.par.a) >= SIM_REDUNDANCIA) return candidato.par.a; // ya dice lo mismo
    return miuTexto + '\n\n' + candidato.par.a;
  }

  /** Búsqueda principal. Devuelve texto de respuesta (de una o varias fuentes
   *  combinadas) o null si no hay ninguna señal real. */
  function preguntar(texto, pesos) {
    if (!_listo) iniciar();
    const entrada = texto.toLowerCase().trim();
    pesos = pesos || {};

    // 1. Motor MIU axiomático — TODOS los matches, no solo el primero.
    const miuHits = (window.MIU && window.MIU.consultarTodos) ? window.MIU.consultarTodos(entrada) : [];

    if (!_pares.length) {
      const miuTop = miuHits.slice().sort((a, b) => b.score - a.score).slice(0, MAX_FRAGMENTOS_MIU);
      return miuTop.length ? _unirFragmentosMIU(miuTop) : null;
    }

    // 2. Caché LRU
    const _pvotes = pesos ? Object.keys(pesos).length : 0;
    const cacheKey = entrada + '|v' + _pvotes;
    const cached   = _cacheGet(cacheKey);
    if (cached !== undefined) return cached;

    // 3. Mejor candidato del oráculo: BM25 indexado primero; si no da un match
    //    fuerte, se prueba también la búsqueda lineal clásica (señal distinta:
    //    contención literal) y se toma la mejor de las dos — igual que en v1,
    //    solo que ahora con un nivel intermedio "blando" en vez de todo o nada.
    let candBM25 = null;
    if (_indiceValido) {
      const tokens     = _tokensCompletos(entrada);
      const resultados = _scoreBM25(tokens, pesos);
      if (resultados && resultados.length > 0) {
        const top = resultados[0];
        candBM25 = { par: top.par, fuerte: top.score >= UMBRAL_BM25_FUERTE, blando: top.score >= UMBRAL_BM25_BLANDO };
      }
    }

    // ─── Filtro de relevancia de dominio (Ciclo AB) ───────────────────────────
    // Si CERO tokens unigramas de la query aparecen en alguna PREGUNTA del oráculo,
    // la consulta es casi seguro off-domain (coincidencia léxica en respuestas).
    // Descartamos candBM25 antes de seguir. No toca buscarConScore/buscarSemantico.
    if (candBM25 && _indice_q) {
      const tokens_uni = _tokenizar(entrada);       // solo unigramas
      if (_coberturaPreguntas(tokens_uni) === 0) {
        candBM25 = null;
      }
    }

    let candidato = (candBM25 && candBM25.fuerte) ? candBM25 : null;
    if (!candidato) {
      const lin = _busquedaLinealConScore(entrada, pesos);
      const candLineal = lin ? { par: lin.par, fuerte: lin.score >= UMBRAL_LINEAL_FUERTE, blando: lin.score >= UMBRAL_LINEAL_BLANDO } : null;
      if (candLineal && candLineal.fuerte) candidato = candLineal;
      else if (candBM25 && candBM25.blando) candidato = candBM25;
      else if (candLineal && candLineal.blando) candidato = candLineal;
    }

    const resultado = _componer(miuHits, candidato);
    _cacheSet(cacheKey, resultado);
    return resultado;
  }

  /** Fallback O(n), ahora con score explícito (para que _componer clasifique
   *  fuerte/blando/nada) en vez de aplicar su propio umbral internamente. */
  function _busquedaLinealConScore(entrada, pesos) {
    let mejor = null, mejorScore = -999, mejorIdx = -1;
    for (let i = 0; i < _pares.length; i++) {
      const par   = _pares[i];
      let score   = _calcularScoreClasico(par, entrada);
      score += (pesos[String(i)] || 0) * 8;
      if (score > mejorScore) { mejorScore = score; mejor = par; mejorIdx = i; }
    }
    if (mejorIdx >= 0 && (pesos[String(mejorIdx)] || 0) <= -3) return null;
    return mejor ? { par: mejor, score: mejorScore } : null;
  }

  function _calcularScoreClasico(par, entrada) {
    let score = 0;
    const q   = (par.q || '').toLowerCase();
    const a   = (par.a || '').toLowerCase();
    if (q.indexOf(entrada) !== -1) score += 100;
    else if (entrada.indexOf(q) !== -1 && q.length > 10) score += 70;
    // sinonimia reducida — el TF-IDF ya la cubre mejor
    if (entrada.includes('coherencia') && a.includes('ki'))    score += 20;
    if (entrada.includes('alma')       && a.includes('fii'))   score += 20;
    if (a.length < 80) score -= 30;
    return score;
  }

  /** Devuelve los N mejores pares con su score (para debug, visor de Biblioteca y RAG).
   *  maxA: longitud máxima del campo 'a' en cada resultado.
   *        Default 120 para el visor (display). Pasar un valor mayor en llamadas RAG
   *        donde se necesita el texto completo para inyectarlo en el system prompt. */
  function buscarConScore(texto, pesos, n, maxA) {
    if (!_listo) iniciar();
    n    = n    || 5;
    maxA = maxA || 120;
    const tokens     = _tokensCompletos((texto || '').toLowerCase());
    const resultados = _scoreTFIDF(tokens, pesos || {}) || [];
    return resultados.slice(0, n).map(r => ({
      score: r.score.toFixed(2), q: r.par.q, a: r.par.a.slice(0, maxA)
    }));
  }

  // ─────────────── Embedder semántico (Phase D.1) ──────────────────────────────
  // Modelo: Xenova/all-MiniLM-L6-v2 quantized (~6 MB), 384 dims, CDN externo.
  // El SW no necesita cachearlo — se sirve desde cdn.jsdelivr.net y el browser lo
  // cachea en su propio cache HTTP (no en el cache del SW).
  //
  // ⚠️ CRÍTICO: _iniciarEmbedder() solo se llama desde iniciarConIDB(), sin await,
  // para no bloquear la UI. Los llamadores deben tolerar _embedder === null.

  async function _iniciarEmbedder() {
    try {
      const { pipeline } = await import(
        'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2'
      );
      _embedder = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
        quantized: true, // versión 8-bit: ~6 MB en vez de 23 MB, calidad casi igual
      });
      console.log('🔮 BuscarOraculo: modelo MiniLM-L6-v2 cargado ✓ (reranking semántico activo)');
    } catch (e) {
      // Fallo silencioso — el sistema sigue funcionando con BM25 puro
      console.warn('BuscarOraculo: embedder no disponible, modo BM25 puro:', e.message || e);
    }
  }

  /** Embed un texto → Float32Array de 384 dims, ya normalizada (coseno = dot product) */
  async function _embedTexto(texto) {
    const out = await _embedder(texto, { pooling: 'mean', normalize: true });
    return out.data; // Float32Array
  }

  /** Similitud coseno entre dos vectores normalizados = producto punto */
  function _coseno(a, b) {
    let dot = 0;
    for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
    return dot; // rango [-1, 1]; vectores normalizados → directamente coseno
  }

  /**
   * Búsqueda con reranking semántico (Phase D.1).
   *
   * Flujo:
   *   1. BM25 recupera top-50 candidatos como pool léxico.
   *   2. Si el embedder está listo: embed query + candidatos → rerank por score combinado.
   *   3. Si el embedder NO está listo (primera carga o fallo): devuelve los top-N de BM25
   *      directamente — latencia idéntica al comportamiento anterior, sin degradación.
   *
   * Solo se usa en el path RAG (app.js línea ~866). El visor de biblioteca (línea ~772)
   * sigue usando buscarConScore() síncrona para no añadir latencia en la UI.
   *
   * @param {string} texto - Query del usuario
   * @param {Object} pesos - Pesos de votos { idx → número }
   * @param {number} n     - Cuántos resultados devolver (default 3)
   * @param {number} maxA  - Longitud máxima del campo 'a' (default 500 para RAG)
   * @returns {Promise<Array<{score, semScore, q, a}>>}
   */
  async function buscarConScoreSemantico(texto, pesos, n, maxA) {
    n    = n    || 3;
    maxA = maxA || 500;

    // 1. BM25 top-50 como pool de candidatos
    const candidatos = buscarConScore(texto, pesos, 50, maxA);

    // 2. Fallback gracioso si el modelo no está listo
    if (!_embedder) return candidatos.slice(0, n);

    // 3. Embed query
    let qEmb;
    try {
      qEmb = await _embedTexto(texto);
    } catch (e) {
      console.warn('BuscarOraculo: fallo al embed query, usando BM25 puro:', e.message || e);
      return candidatos.slice(0, n);
    }

    // 4. Embed candidatos y calcular similitud coseno — en paralelo para minimizar latencia
    let reranked;
    try {
      reranked = await Promise.all(
        candidatos.map(async (c) => {
          try {
            const cEmb = await _embedTexto(c.q + ' ' + c.a);
            return { ...c, semScore: _coseno(qEmb, cEmb) };
          } catch (_e) {
            return { ...c, semScore: 0 }; // si falla un candidato, score 0, sigue
          }
        })
      );
    } catch (e) {
      console.warn('BuscarOraculo: fallo en reranking semántico, usando BM25 puro:', e.message || e);
      return candidatos.slice(0, n);
    }

    // 5. Score combinado con umbral + boost de alta confianza (Task F).
    //    · Candidatos con semScore < SEM_UMBRAL se descartan (ruido del modelo).
    //    · Si el filtro deja < n resultados, usamos el pool completo como fallback.
    //    · Boost SEM_BOOST_ALTO para matches de muy alta confianza (coseno > SEM_BOOST_UMBRAL).
    const sobreUmbral = reranked.filter(r => r.semScore >= SEM_UMBRAL);
    const poolD1      = sobreUmbral.length >= n ? sobreUmbral : reranked;
    poolD1.sort((a, b) => {
      const boostA = a.semScore >= SEM_BOOST_UMBRAL ? SEM_BOOST_ALTO : 0;
      const boostB = b.semScore >= SEM_BOOST_UMBRAL ? SEM_BOOST_ALTO : 0;
      const semA   = a.semScore * SEM_PESO + boostA;
      const semB   = b.semScore * SEM_PESO + boostB;
      return (semB + parseFloat(b.score)) - (semA + parseFloat(a.score));
    });

    return poolD1.slice(0, n).map(r => ({
      score:    r.score,
      semScore: r.semScore.toFixed(3),
      q:        r.q,
      a:        r.a,
    }));
  }

  /** Estadísticas del índice (para panel Biblioteca) */
  function stats() {
    return {
      totalPares: _pares.length,
      tokensTotales: _indice ? Object.keys(_indice).length : 0,
      indiceValido: _indiceValido,
      cacheEntradas: _cache.size,
      motor: 'BM25 (k1=' + BM25_K1 + ', b=' + BM25_B + ')',
      avgdl: _avgdl ? _avgdl.toFixed(1) : 0,
      embedder: _embedder ? 'MiniLM-L6-v2 (activo)' : 'no disponible (BM25 puro)',
      embedsIndexados: _idxEmbs ? _idxEmbs.length : 0,
      indiceSemantico: _idxEmbs === null ? 'no cargado'
                      : _idxEmbs.length === 0 ? 'vacío (indexando…)'
                      : 'listo (' + _idxEmbs.length + ' embeds)',
    };
  }

  // ─────────────── Índice semántico pre-computado (Phase D.2) ──────────────────

  /**
   * Decodifica un ArrayBuffer de Float16 a Float32Array.
   * Inverso de la función encodeFloat16Array() del embed-worker.
   */
  function _float16ToFloat32Array(buf) {
    const u16 = new Uint16Array(buf);
    const f32 = new Float32Array(u16.length);
    for (let i = 0; i < u16.length; i++) {
      const h    = u16[i];
      const sign = (h >>> 15) ? -1 : 1;
      const exp  = (h >>> 10) & 0x1f;
      const frac =  h & 0x3ff;
      if (exp === 0) {
        f32[i] = sign * Math.pow(2, -14) * (frac / 1024); // subnormal
      } else if (exp === 0x1f) {
        f32[i] = frac ? NaN : sign * Infinity;
      } else {
        f32[i] = sign * Math.pow(2, exp - 15) * (1 + frac / 1024);
      }
    }
    return f32;
  }

  /**
   * Carga todos los embeddings almacenados en IDB y construye el índice en memoria.
   * Debe llamarse DESPUÉS de iniciarConIDB() para que _pares esté completo.
   * No bloquea: en caso de fallo, _idxEmbs queda en [] y el sistema usa D.1 (reranking).
   *
   * También construye _parPorId para resolver id → par sin scan lineal de _pares.
   * Los pares del oráculo base (sin _idb_id) no tienen entrada en el store 'embeddings'
   * y por tanto no aparecen aquí — solo los pares IDB tienen embedding pre-computado.
   */
  async function cargarIndiceSemantico() {
    if (!window.IDBStore) { _idxEmbs = []; return 0; }
    try {
      const recs = await window.IDBStore.obtenerEmbeddings();
      if (!recs || recs.length === 0) { _idxEmbs = []; return 0; }

      // Construir _parPorId (solo pares IDB tienen _idb_id)
      _parPorId = new Map();
      _pares.forEach(p => {
        if (p._idb_id != null) _parPorId.set(p._idb_id, p);
      });

      // Decodificar Float16 → Float32 en bulk
      _idxEmbs = recs
        .map(r => {
          const par = _parPorId.get(r.id);
          if (!par) return null; // par borrado desde que se indexó
          return { id: r.id, emb: _float16ToFloat32Array(r.emb), par };
        })
        .filter(Boolean);

      console.log('🔮 BuscarOraculo D.2: índice semántico cargado — ' + _idxEmbs.length + ' embeds en memoria');
      return _idxEmbs.length;
    } catch (e) {
      console.warn('BuscarOraculo D.2: no se pudo cargar índice semántico:', e.message || e);
      _idxEmbs = [];
      return 0;
    }
  }

  /**
   * Búsqueda semántica directa sobre el índice pre-computado (Phase D.2).
   *
   * Si el índice está listo (_idxEmbs con datos): embed la query y hace producto punto
   * contra todos los vectores — O(k×384) siendo k el nº de pares IDB indexados.
   * Los pares del oráculo base (no indexados) se cubren con reranking D.1 como fallback.
   *
   * Si el índice NO está listo (null o vacío): delega en buscarConScoreSemantico()
   * (reranking D.1: BM25 top-50 → coseno) — degradación cero.
   *
   * Fusión de scores (Task F — calibrada):
   *   - semScore × SEM_PESO: escala coseno (0–1) al rango BM25 (0–~15).
   *   - Umbral SEM_UMBRAL: descarta candidatos de baja confianza semántica.
   *   - Boost SEM_BOOST_ALTO si coseno > SEM_BOOST_UMBRAL (match de alta confianza).
   *   - BM25 complementa: para los pares con overlap léxico, el score BM25 suma directamente.
   *   - Para integrar con pares de la base (no en el índice D.2), se mezclan:
   *     · Top-n_sem del índice semántico (coseno directo)
   *     · Top-n_lex de BM25 clásico
   *
   * @param {string} texto - Query del usuario
   * @param {Object} pesos - Pesos de votos { idx → número }
   * @param {number} n     - Cuántos resultados devolver (default 3)
   * @param {number} maxA  - Longitud máxima del campo 'a' (default 500 para RAG)
   * @returns {Promise<Array<{score, semScore, q, a}>>}
   */
  async function buscarSemantico(texto, pesos, n, maxA) {
    n    = n    || 3;
    maxA = maxA || 500;

    // Sin índice o índice vacío → delegar en D.1 (reranking on-the-fly)
    if (!_idxEmbs || _idxEmbs.length === 0) {
      return buscarConScoreSemantico(texto, pesos, n, maxA);
    }

    // Sin embedder cargado → BM25 puro (aún cargando el modelo)
    if (!_embedder) {
      const fallback = buscarConScore(texto, pesos, n, maxA);
      return fallback;
    }

    // Embed la query
    let qEmb;
    try {
      qEmb = await _embedTexto(texto);
    } catch (e) {
      console.warn('BuscarOraculo D.2: fallo embed query, fallback D.1:', e.message || e);
      return buscarConScoreSemantico(texto, pesos, n, maxA);
    }

    // Búsqueda lineal coseno sobre el índice semántico
    // Para colecciones >200k pares considerar HNSW; hasta ese tamaño la búsqueda
    // lineal con Float32 es <20 ms en hardware moderno (benchmark antes de migrar).
    const POOL_SEM = Math.min(_idxEmbs.length, 100); // top-100 semántico como pool
    const scores = _idxEmbs.map(entry => ({
      par: entry.par,
      semScore: _coseno(qEmb, entry.emb),
    }));
    scores.sort((a, b) => b.semScore - a.semScore);
    const topSem = scores.slice(0, POOL_SEM);

    // Obtener scores BM25 para fusionar
    const tokens    = _tokensCompletos((texto || '').toLowerCase());
    const bm25Res   = _scoreTFIDF(tokens, pesos || {}) || [];
    // Construir mapa idx → BM25 score por pregunta normalizada
    const bm25Map   = new Map();
    bm25Res.forEach(r => bm25Map.set(_normalizar(r.par.q || ''), parseFloat(r.score)));

    // Fusión: score_final = semScore×SEM_PESO [+SEM_BOOST_ALTO si alta confianza] + BM25score.
    // Umbral: candidatos con semScore < SEM_UMBRAL se descartan antes de fusionar.
    //   Si el umbral deja < n resultados (colección pequeña o embeddings poco calibrados),
    //   se incluyen los mejores hasta completar n sin importar el umbral.
    // Boost: coseno > SEM_BOOST_UMBRAL suma SEM_BOOST_ALTO puntos extra.
    const topSemFiltrado = topSem.filter(r => r.semScore >= SEM_UMBRAL);
    const poolD2 = topSemFiltrado.length >= n ? topSemFiltrado
                                              : topSem.slice(0, Math.max(topSemFiltrado.length, n));

    const fusionados = poolD2.map(r => {
      const qNorm  = _normalizar(r.par.q || '');
      const bm25sc = bm25Map.get(qNorm) || 0;
      const voto   = (pesos || {})[String(_pares.indexOf(r.par))] || 0;
      if (voto <= -3) return null; // par muy penalizado
      const boost = r.semScore >= SEM_BOOST_UMBRAL ? SEM_BOOST_ALTO : 0;
      return {
        q:        r.par.q,
        a:        (r.par.a || '').slice(0, maxA),
        semScore: r.semScore,
        score:    (r.semScore * SEM_PESO + boost + bm25sc).toFixed(2),
      };
    }).filter(Boolean);

    fusionados.sort((a, b) => parseFloat(b.score) - parseFloat(a.score));

    return fusionados.slice(0, n).map(r => ({
      score:    r.score,
      semScore: r.semScore.toFixed(3),
      q:        r.q,
      a:        r.a,
    }));
  }

  // ─────────────── SUBFLOW v0.3 — dedupe semántico para ingestión ─────────────
  // Compara cada query candidata contra un pool de preguntas existentes usando
  // similitud coseno sobre MiniLM-L6-v2. Si el embedder no está disponible
  // (aún cargando o fallo de red), retorna Map vacío — fallback silencioso.
  //
  // Diseño:
  //   · Pool acotado externamente (core.js pasa slice(-20)) para mantener
  //     latencia < 1s incluso en hardware lento (20+N embeds × ~20ms ≈ <1s).
  //   · Advisory puro: el llamador decide qué hacer con los resultados.
  //   · Cada embed individual falla silenciosamente — no bloquea el resto.
  //
  // @param {string[]} queryList  Preguntas candidatas a ingerir
  // @param {string[]} poolList   Pool de preguntas existentes (acotado por caller)
  // @param {number}   umbral     Umbral coseno [0,1], default 0.82
  // @returns {Promise<Map<string,number>>} query → maxSimCoseno (solo ≥ umbral)
  async function dedupeSemantico(queryList, poolList, umbral) {
    umbral = typeof umbral === 'number' ? umbral : 0.82;
    if (!_embedder || !queryList.length || !poolList.length) return new Map();
    try {
      // Embed el pool en paralelo; fallos individuales → null (se filtran)
      const poolEmbs = await Promise.all(
        poolList.map(q => _embedTexto(q).catch(() => null))
      );
      const poolValido = poolEmbs
        .map((emb, i) => ({ emb, q: poolList[i] }))
        .filter(e => e.emb !== null);
      if (!poolValido.length) return new Map();

      const resultado = new Map();
      // Embed candidatos y comparar vs pool en paralelo
      await Promise.all(queryList.map(async q => {
        try {
          const qEmb = await _embedTexto(q);
          let maxSim = 0;
          for (const { emb } of poolValido) {
            const s = _coseno(qEmb, emb);
            if (s > maxSim) maxSim = s;
          }
          if (maxSim >= umbral) resultado.set(q, maxSim);
        } catch (_e) { /* fallo por candidato: silencioso */ }
      }));
      return resultado;
    } catch (e) {
      // Fallo total → advisory vacío, ingestión no bloqueada
      console.warn('BuscarOraculo.dedupeSemantico: fallo embeddings, SUBFLOW v0.3 off:', e.message || e);
      return new Map();
    }
  }

  // ── AS: γ₃ — SUBFLOW v0.3 pool extendido (índice D.2) ──────────────────────
  // dedupeSemantico() de arriba re-embebe un pool acotado (core.js pasa slice(-20))
  // en cada llamada — necesario porque ese pool no tiene embeddings precomputados.
  // Si el índice D.2 ya está cargado (_idxEmbs: Phase D.2, todos los pares IDB
  // indexados, Float32 en memoria), podemos comparar contra el CORPUS COMPLETO
  // sin coste de re-embed: cada candidato se embebe una vez y se compara por
  // producto punto contra _idxEmbs — el pool ya no está acotado a 20.
  //
  // Diseño:
  //   · Cobertura: corpus IDB completo en vez de los últimos 20 pares del lote.
  //   · Coste: 1 embed por candidato (igual que v0.3) + N productos punto
  //     (~<1ms por cada 1000 embeds indexados) — no escala con el tamaño del lote.
  //   · Si el índice no está cargado o vacío (_idxEmbs null/[]), retorna null:
  //     el llamador (core.js) cae en dedupeSemantico() con el pool acotado de
  //     siempre — degradación cero, mismo comportamiento que antes de γ₃.
  //
  // @param {string[]} queryList  Preguntas candidatas a ingerir
  // @param {number}   umbral     Umbral coseno [0,1], default 0.82
  // @returns {Promise<Map<string,number>|null>} query → maxSimCoseno, o null si sin índice
  async function dedupeSemanticoIndexado(queryList, umbral) {
    umbral = typeof umbral === 'number' ? umbral : 0.82;
    if (!_embedder || !_idxEmbs || !_idxEmbs.length || !queryList.length) return null;
    try {
      const resultado = new Map();
      await Promise.all(queryList.map(async q => {
        try {
          const qEmb = await _embedTexto(q);
          let maxSim = 0;
          for (const entry of _idxEmbs) {
            const s = _coseno(qEmb, entry.emb);
            if (s > maxSim) maxSim = s;
          }
          if (maxSim >= umbral) resultado.set(q, maxSim);
        } catch (_e) { /* fallo por candidato: silencioso */ }
      }));
      return resultado;
    } catch (e) {
      // Fallo total → null, el llamador cae en el pool acotado de v0.3
      console.warn('BuscarOraculo.dedupeSemanticoIndexado: fallo índice D.2, fallback pool v0.3:', e.message || e);
      return null;
    }
  }

  // ─────────────────────────────────────────────────────────────────────────────
  return {
    iniciar,
    iniciarConIDB,
    agregarPares,
    idDe,
    preguntar,
    buscarConScore,
    buscarConScoreSemantico,
    buscarSemantico,
    cargarIndiceSemantico,
    dedupeSemantico,                  // SUBFLOW v0.3
    dedupeSemanticoIndexado,          // AS: γ₃ — SUBFLOW v0.3 pool extendido (índice D.2)
    stats,
    MARCADOR_MATCH_BLANDO,
    // internos expuestos para tests
    _tokenizar,
    _tokensCompletos,
    _construirIndice,
    _coberturaPreguntas,
    _componer,
    _unirFragmentosMIU,
    _simFragmentos,
    get _pares() { return _pares; },
    get _embedderActivo() { return !!_embedder; }, // SUBFLOW v0.3: sonda para core.js
    get _idxEmbsActivo() { return !!(_idxEmbs && _idxEmbs.length); }, // AS: γ₃ — sonda índice D.2 para core.js
  };
})();

// Arranque
if (document.readyState === 'complete') {
  BuscarOraculo.iniciar();
  // Carga IDB en background sin bloquear
  BuscarOraculo.iniciarConIDB().catch(() => {});
} else {
  window.addEventListener('DOMContentLoaded', function () {
    BuscarOraculo.iniciar();
    BuscarOraculo.iniciarConIDB().catch(() => {});
  });
}
