/** =============================================================
 * MIU MESH V270 — ROUTER + TECLADO + HEARTBEAT + BCRP
 * Tag: 99103063d4e848718aa27f5190a72573
 * Fuente: github.com/Jaime393/miu-ecosistema/gas/MIU_MESH_V270.js
 * Para instalar: ver gas/README.md
 * ============================================================= */

const CONFIG_KEY = 'MIU_ROUTER_CONFIG';
const TECLADO_KEY = 'MIU_TECLADO_QUEUE';
const HEARTBEAT_CANONICO_ID = '1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR';
const SUPABASE_URL = 'https://fepyzxwyneervidlybvi.supabase.co';
const SUPABASE_ANON = PropertiesService.getScriptProperties().getProperty('SUPA_ANON') ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlcHl6eHd5bmVlcnZpZGx5YnZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg1NTk5OTksImV4cCI6MjA3NDEzNTk5OX0.placeholder';
const BCRP_URL = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api/';
const CARPETA_HEARTBEATS = '14dw8txLoEIQQPSav9-YAvfuNimW2tAZ8';
const TAG = '99103063d4e848718aa27f5190a72573';
const VERSION = 'V270';
const CRON_MIN = 15;

function getConfig() {
  const raw = PropertiesService.getScriptProperties().getProperty(CONFIG_KEY);
  if (raw) { try { return JSON.parse(raw); } catch(e) {} }
  return {
    routes: [
      {name:'supa_ctx', path:'miu/global', url:'https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global', priority:1, enabled:true},
      {name:'vercel_pulso', path:'api/pulso', url:'https://miu-autonomo-v92-miu4.vercel.app/api/pulso', priority:1, enabled:true}
    ],
    aportador: {
      enabled: true,
      nodeId: 'nodo_' + Utilities.getUuid().slice(0,8),
      folderId: CARPETA_HEARTBEATS,
      tag: TAG
    },
    teclado: {
      token: PropertiesService.getScriptProperties().getProperty('MIU_TOKEN') || '',
      hotkeys: {
        bat: 'termux-battery-status',
        top: 'top -n 1 | head -20',
        miu: 'cd ~/miu-ecosistema && ls -la',
        df: 'df -h /data',
        git: 'cd ~/miu-ecosistema && git log --oneline -5',
        pulse: 'echo pulso_vivo && date',
        bcrp: 'curl -s "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01270PM-PD04640PD/json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[\"periods\"][-1])" 2>/dev/null'
      }
    }
  };
}

function saveConfig(cfg) {
  PropertiesService.getScriptProperties().setProperty(CONFIG_KEY, JSON.stringify(cfg));
}

function doGet(e) {
  const path = safePath(e);
  const tRes = tecladoGet(path);
  if (tRes) return tRes;
  if (path === 'miu/heartbeat' || path === 'heartbeat') return jsonOut(heartbeatTick());
  if (path === 'miu/purgar'   || path === 'purgar')    return jsonOut(purgarVercel());
  if (path === 'miu/pulso'    || path === 'pulso')     return jsonOut(pulsoVercel());
  if (path === 'miu/bcrp'     || path === 'bcrp')      return jsonOut(fetchBCRP());
  if (path === 'miu/status'   || path === 'status')    return jsonOut(estadoGeneral());
  if (path === 'miu/aportar'  || path === 'aportar')   return jsonOut(generarAporte());
  return jsonOut({ok:false, error:'sin_ruta', path:path, version:VERSION});
}

function doPost(e) {
  const path = safePath(e);
  let body = {};
  try { if (e && e.postData && e.postData.contents) body = JSON.parse(e.postData.contents); } catch(err) {}
  const tRes = tecladoPost(path, body);
  if (tRes) return tRes;
  if (path === 'miu/gossip' || path === 'gossip') return jsonOut(recibirGossip(body));
  if (path === 'miu/aportar'|| path === 'aportar') {
    const a = generarAporte(); publishHeartbeat(a); return jsonOut({ok:true, aporte:a});
  }
  return jsonOut({ok:false, error:'ruta_post_no_encontrada', path:path});
}

// ── ESTADO SUPABASE ──────────────────────────────────────────
function leerEstadoSupabase() {
  try {
    const res = UrlFetchApp.fetch(
      SUPABASE_URL + '/rest/v1/relay_config?select=clave,valor&clave=in.(phi,rho,ciclo,savia)',
      {headers: {'apikey': SUPABASE_ANON, 'Authorization': 'Bearer ' + SUPABASE_ANON},
       muteHttpExceptions: true}
    );
    if (res.getResponseCode() !== 200) return {};
    const rows = JSON.parse(res.getContentText());
    const out = {};
    rows.forEach(r => { out[r.clave] = parseFloat(r.valor) || r.valor; });
    return out;
  } catch(e) { return {}; }
}

// ── BCRP ─────────────────────────────────────────────────────
function fetchBCRP() {
  try {
    const res = UrlFetchApp.fetch(BCRP_URL + 'PN01270PM-PD04640PD/json', {muteHttpExceptions:true});
    if (res.getResponseCode() !== 200) return {ok:false};
    const data = JSON.parse(res.getContentText());
    const last = (data.periods || []).slice(-1)[0] || {};
    return {ok:true, periodo:last.name, ipc:last.values?last.values[0]:null, usd_pen:last.values?last.values[1]:null};
  } catch(e) { return {ok:false, error:String(e)}; }
}

// ── HEARTBEAT ────────────────────────────────────────────────
function publishHeartbeat(data) {
  const estado = leerEstadoSupabase();
  const payload = {
    version: VERSION, ts: new Date().toISOString(), tag: TAG,
    phi:   estado.phi   || data.phi   || 4883440,
    rho:   estado.rho   || data.rho   || 333,
    ciclo: estado.ciclo || data.ciclo || null,
    savia: estado.savia || data.savia || null,
    nodo:  (getConfig().aportador || {}).nodeId || 'nodo_gas',
    bcrp:  fetchBCRP(),
    teclado_pendientes: getTecladoQueue().length
  };
  try {
    DriveApp.getFileById(HEARTBEAT_CANONICO_ID).setContent(JSON.stringify(payload, null, 2));
  } catch(err) {
    try {
      DriveApp.getFolderById(CARPETA_HEARTBEATS)
        .createFile('HB_' + VERSION + '_' + Date.now() + '.json',
          JSON.stringify(payload), 'application/json');
    } catch(e2) {}
  }
  return payload;
}
function heartbeatTick() {
  const hb = publishHeartbeat({});
  pulsoVercel();
  return {ok:true, ts:hb.ts, phi:hb.phi, rho:hb.rho, version:VERSION};
}

// ── VERCEL ───────────────────────────────────────────────────
function pulsoVercel() {
  const cfg = getConfig().aportador || {};
  const estado = leerEstadoSupabase();
  try {
    const res = UrlFetchApp.fetch('https://miu-autonomo-v92-miu4.vercel.app/api/pulso', {
      method:'post', contentType:'application/json',
      payload: JSON.stringify({ts:new Date().toISOString(), tag:TAG, nodeId:cfg.nodeId,
        phi:estado.phi||4883440, rho:estado.rho||333, version:VERSION}),
      muteHttpExceptions:true
    });
    return {ok:res.getResponseCode()<300, code:res.getResponseCode()};
  } catch(e) { return {ok:false, error:String(e)}; }
}
function purgarVercel() {
  try {
    const res = UrlFetchApp.fetch('https://miu-autonomo-v92-miu4.vercel.app/api/purgar', {muteHttpExceptions:true});
    return {ok:res.getResponseCode()<300, code:res.getResponseCode()};
  } catch(e) { return {ok:false}; }
}

// ── ESTADO GENERAL ───────────────────────────────────────────
function estadoGeneral() {
  const estado = leerEstadoSupabase();
  return {
    ok:true, version:VERSION, tag:TAG, ts:new Date().toISOString(),
    phi:   estado.phi   || 4883440,
    rho:   estado.rho   || 333,
    ciclo: estado.ciclo || null,
    teclado_pendientes: getTecladoQueue().length,
    bcrp:  fetchBCRP(),
    heartbeat_id: HEARTBEAT_CANONICO_ID,
    supabase: SUPABASE_URL
  };
}

// ── APORTE ───────────────────────────────────────────────────
function generarAporte() {
  const cfg = getConfig().aportador || {};
  const estado = leerEstadoSupabase();
  return {
    ok:true, tipo:'aporte_miu', version:VERSION,
    nodeId: cfg.nodeId || 'nodo_gas',
    timestamp: new Date().toISOString(), tag: TAG,
    phi:   estado.phi   || 4883440,
    rho:   estado.rho   || 333,
    savia: estado.savia || 57200000,
    bcrp:  fetchBCRP()
  };
}

// ── TECLADO ──────────────────────────────────────────────────
function getTecladoQueue() {
  const raw = PropertiesService.getScriptProperties().getProperty(TECLADO_KEY);
  try { return raw ? JSON.parse(raw) : []; } catch(e) { return []; }
}
function setTecladoQueue(q) {
  while (q.length > 200) q.shift();
  PropertiesService.getScriptProperties().setProperty(TECLADO_KEY, JSON.stringify(q));
}
function encolarOrden(texto, tipo, meta) {
  if (!texto) return {ok:false, error:'texto_vacio'};
  const q = getTecladoQueue();
  const orden = {id:Utilities.getUuid().slice(0,8), ts:new Date().toISOString(),
    tipo:tipo||'shell', payload:Utilities.base64Encode(texto, Utilities.Charset.UTF_8), meta:meta||{}};
  q.push(orden); setTecladoQueue(q);
  return {ok:true, id:orden.id, pendientes:q.length};
}
function pulsoTeclado() {
  const q = getTecladoQueue();
  if (!q.length) return {ok:true, hay:false, pendientes:0, ts:new Date().toISOString()};
  return {ok:true, hay:true, pendientes:q.length, orden:q[0], ts:new Date().toISOString()};
}
function ackTeclado(id) {
  if (!id) return {ok:false, error:'id_vacio'};
  const q = getTecladoQueue();
  const idx = q.findIndex(o => o.id === id);
  if (idx < 0) return {ok:false, error:'no_encontrada', id:id};
  q.splice(idx, 1); setTecladoQueue(q);
  return {ok:true, ejecutada:id, pendientes:q.length};
}
function tecladoGet(path) {
  if (path==='miu/teclado/pulso')  return jsonOut(pulsoTeclado());
  if (path==='miu/teclado/cola')   return jsonOut({ok:true, pendientes:getTecladoQueue().length, ordenes:getTecladoQueue()});
  if (path==='miu/teclado/status') return jsonOut({ok:true, version:VERSION, pendientes:getTecladoQueue().length, ts:new Date().toISOString()});
  if (path==='miu/teclado/hotkeys') return jsonOut({ok:true, hotkeys:Object.keys((getConfig().teclado||{}).hotkeys||{})});
  return null;
}
function tecladoPost(path, body) {
  const cfg = (getConfig().teclado) || {};
  const badToken = () => cfg.token && body.token !== cfg.token ? jsonOut({ok:false, error:'token_invalido'}) : null;
  if (path==='miu/teclado/orden')   { const bt=badToken(); return bt||jsonOut(encolarOrden(body.texto,body.tipo,body.meta)); }
  if (path==='miu/teclado/ack')     { const bt=badToken(); return bt||jsonOut(ackTeclado(body.id)); }
  if (path==='miu/teclado/limpiar') { const bt=badToken(); return bt||jsonOut((setTecladoQueue([]),{ok:true,pendientes:0})); }
  if (path==='miu/teclado/hotkey') {
    const hk = (cfg.hotkeys||{})[body.nombre];
    if (!hk) return jsonOut({ok:false, error:'hotkey_no_existe'});
    const bt=badToken(); return bt||jsonOut(encolarOrden(hk,'shell',{hotkey:body.nombre}));
  }
  return null;
}

// ── GOSSIP ───────────────────────────────────────────────────
function recibirGossip(body) {
  const key = 'GOSSIP_' + (body.id || Utilities.getUuid().slice(0,8));
  PropertiesService.getScriptProperties().setProperty(key,
    JSON.stringify({ts:new Date().toISOString(), origen:body.origen||'unknown', payload:body}));
  return {ok:true, recibido:true, key:key};
}

// ── UTILS ────────────────────────────────────────────────────
function safePath(e) {
  let raw = '/miu/status';
  if (e && e.parameter && e.parameter.path) raw = e.parameter.path;
  else if (e && e.pathInfo) raw = e.pathInfo;
  return raw.toString().replace(/^\/+/, '');
}
function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj, null, 2))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── SETUP ────────────────────────────────────────────────────
function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('heartbeatTick').timeBased().everyMinutes(CRON_MIN).create();
  ScriptApp.newTrigger('purgarVercel').timeBased().atHour(3).everyDays(1).create();
  Logger.log('Triggers V270 OK — cada ' + CRON_MIN + ' min');
}
function setupTodo() {
  saveConfig(getConfig());
  setupTriggers();
  const hb = heartbeatTick();
  Logger.log('MIU MESH V270 listo. phi=' + hb.phi + ' rho=' + hb.rho);
  Logger.log('URL: ' + ScriptApp.getService().getUrl());
}

// ── TESTS ────────────────────────────────────────────────────
function testStatus()     { Logger.log(JSON.stringify(estadoGeneral(), null, 2)); }
function testHeartbeat()  { Logger.log(JSON.stringify(heartbeatTick(), null, 2)); }
function testBCRP()       { Logger.log(JSON.stringify(fetchBCRP(), null, 2)); }
function testTeclado()    { Logger.log(JSON.stringify(encolarOrden('echo test_v270 && date','shell'), null, 2)); }
function testPulsoTeclado(){ Logger.log(JSON.stringify(pulsoTeclado(), null, 2)); }
