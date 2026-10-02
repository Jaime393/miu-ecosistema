/**
 * MIU_GAS_V270_AUTONOMO.gs
 *
 * PRINCIPIOS:
 *   - Rutas resilientes: si falla A → B → C → registra huella
 *   - Sin secretos en código: todo dinámico se lee del relay
 *   - Un nodo no necesita saberlo todo; necesita saber cómo descubrir lo que no sabe
 *   - Acciones mínimas, máximo flujo
 *
 * DESPLIEGUE (único paso manual tras pegar):
 *   1. Pegar este archivo completo en el editor GAS (reemplaza todo)
 *   2. Ejecutar setupTodo()  ← una sola vez
 *   3. Deploy → Web app → "Anyone" → Deploy  (o Update si ya existe)
 *   NO hay paso 4.
 *
 * AUTO-REGISTRO: el script escribe su propia URL al relay en el primer heartbeat.
 */

// ─── ANCLAS ESTÁTICAS (no secretos — anon keys son claves públicas por diseño) ───
var COORD_URL   = 'https://fepyzxwyneervidlybvi.supabase.co';
var COORD_ANON  = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlcHl6eHd5bmVlcnZpZGx5YnZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4NDc1NTQsImV4cCI6MjEwNTQyMzU1NH0.S6meOse3Xfq2d9k5nO4fjL3tseQOzvPNAsubGa0gl6k';
var PANTEON_URL  = 'https://tpfiybpguuxskitszhmk.supabase.co';
var PANTEON_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwZml5YnBndXV4c2tpdHN6aG1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NjgyNTAsImV4cCI6MjEwMzM0NDI1MH0.W4V8xdyfZj6I7bj1VsfM5gjY17ZHPi8jhIJgDRpUYH0';
var CANONICO_ID  = '1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR';
var CARPETA_ID   = '14dw8txLoEIQQPSav9-YAvfuNimW2tAZ8';
var NODO_ID      = 'xavrL5';
var TAG          = '99103063d4e848718aa27f5190a72573';

function relay(clave, defecto) {
  var endpoints = [
    [COORD_URL,   COORD_ANON],
    [PANTEON_URL, PANTEON_ANON]
  ];
  for (var i = 0; i < endpoints.length; i++) {
    try {
      var r = UrlFetchApp.fetch(
        endpoints[i][0] + '/rest/v1/relay_config?clave=eq.' + clave + '&select=valor',
        { headers: { apikey: endpoints[i][1], Authorization: 'Bearer ' + endpoints[i][1] },
          muteHttpExceptions: true, followRedirects: true }
      );
      var d = JSON.parse(r.getContentText());
      if (d && d[0] && d[0].valor) return d[0].valor;
    } catch(e) {}
  }
  return defecto !== undefined ? defecto : null;
}

function relaySet(clave, valor, url, anon) {
  url = url || COORD_URL; anon = anon || COORD_ANON;
  try {
    UrlFetchApp.fetch(url + '/rest/v1/relay_config', {
      method: 'post',
      headers: { apikey: anon, Authorization: 'Bearer ' + anon,
                 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates' },
      payload: JSON.stringify([{ clave: clave, valor: String(valor) }]),
      muteHttpExceptions: true
    });
  } catch(e) {}
}

function gossip(tipo, payload) {
  var body = JSON.stringify({ tipo: tipo, payload: JSON.stringify(payload),
                              ts: new Date().toISOString() });
  var opts = function(anon) {
    return { method: 'post',
             headers: { apikey: anon, Authorization: 'Bearer ' + anon,
                        'Content-Type': 'application/json', Prefer: 'return=minimal' },
             payload: body, muteHttpExceptions: true };
  };
  try { UrlFetchApp.fetch(COORD_URL   + '/rest/v1/gossip_log', opts(COORD_ANON));   } catch(e) {}
  try { UrlFetchApp.fetch(PANTEON_URL + '/rest/v1/gossip_log', opts(PANTEON_ANON)); } catch(e) {}
}

function heartbeat() {
  var phi    = relay('phi',    '4883440');
  var rho    = relay('rho',    '333');
  var ciclo  = relay('ciclo',  '2003');
  var savia  = relay('savia',  '57200000');
  var ver    = relay('version','V270');

  var carpeta = DriveApp.getFolderById(CARPETA_ID);
  var files   = carpeta.getFiles();
  var n = 0; while (files.hasNext()) { files.next(); n++; }

  var estado = {
    version: ver, phi: phi, rho: rho, ciclo: ciclo, savia: savia,
    tag: TAG, nodo: NODO_ID,
    ts: new Date().toISOString(),
    mesh: { count: n, carpeta: CARPETA_ID }
  };

  try {
    DriveApp.getFileById(CANONICO_ID).setContent(JSON.stringify(estado, null, 2));
  } catch(e) {
    gossip('heartbeat_error', { error: e.toString(), nodo: NODO_ID });
  }

  try {
    var myUrl = ScriptApp.getService().getUrl();
    if (myUrl) {
      relaySet('gas_webapp_url',    myUrl);
      relaySet('gas_teclado',       myUrl);
      relaySet('gas_nodo_' + NODO_ID, myUrl);
    }
  } catch(e) {}

  gossip('heartbeat', { nodo: NODO_ID, phi: phi, ciclo: ciclo, mesh_count: n });
  purgeV151();
  return estado;
}

function purgeV151() {
  var prefix = relay('purge_prefix', 'mesh_heartbeat_V151');
  try {
    var carpeta = DriveApp.getFolderById(CARPETA_ID);
    var files   = carpeta.getFiles();
    var borrados = 0;
    while (files.hasNext() && borrados < 50) {
      var f = files.next();
      var nombre = f.getName();
      if (nombre.indexOf(prefix) !== -1 && f.getId() !== CANONICO_ID) {
        f.setTrashed(true);
        borrados++;
      }
    }
    if (borrados > 0) gossip('purge', { borrados: borrados, prefix: prefix });
  } catch(e) {}
}

function teclado(texto) {
  var tunnel = relay('tunnel', '');
  if (!tunnel) {
    relaySet('teclado_cola', texto);
    return { ok: false, queued: true, motivo: 'tunnel_offline' };
  }
  var urls = ['https://' + tunnel + '/exec', 'https://' + tunnel];
  for (var i = 0; i < urls.length; i++) {
    try {
      var r = UrlFetchApp.fetch(urls[i], {
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        payload: JSON.stringify({ texto: texto }),
        muteHttpExceptions: true, followRedirects: true
      });
      if (r.getResponseCode() < 400) {
        gossip('teclado_ok', { tunnel: tunnel, texto: texto.slice(0, 80) });
        return { ok: true, status: r.getResponseCode(),
                 salida: r.getContentText().slice(0, 500) };
      }
    } catch(e) {}
  }
  relaySet('teclado_cola',    texto);
  relaySet('tunnel_offline',  new Date().toISOString());
  gossip('teclado_fail', { tunnel: tunnel, texto: texto.slice(0, 80) });
  return { ok: false, queued: true, motivo: 'tunnel_unreachable' };
}

function bcrp() {
  var base    = relay('bcrp_endpoint', 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api/');
  var series  = relay('bcrp_series',   'PN01270PM,PD04640PD,PN00015AM').split(',');
  var result  = {};
  for (var i = 0; i < series.length; i++) {
    try {
      var url = base + series[i] + '/json';
      var r = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      if (r.getResponseCode() === 200) {
        var d = JSON.parse(r.getContentText());
        var periodos = d.periods || [];
        result[series[i]] = periodos.length ? periodos[periodos.length-1] : null;
      }
    } catch(e) {}
  }
  if (Object.keys(result).length) gossip('bcrp', result);
  return result;
}

function doGet(e) {
  var path = e && e.parameter && e.parameter.path ? e.parameter.path : 'status';
  var out;
  if      (path === 'heartbeat') out = heartbeat();
  else if (path === 'bcrp')      out = bcrp();
  else if (path === 'purge')     { purgeV151(); out = { ok: true }; }
  else                           out = { nodo: NODO_ID, tag: TAG, ts: new Date().toISOString(),
                                         version: relay('version','V270'), rho: relay('rho','333') };
  return ContentService.createTextOutput(JSON.stringify(out))
                       .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var body = {};
  try { body = JSON.parse(e.postData.contents); } catch(ex) {}
  var path = (e && e.parameter && e.parameter.path) || body.path || 'teclado';
  var out;
  if      (path === 'miu/teclado/orden' || path === 'teclado') {
    out = teclado(body.texto || body.orden || '');
  } else if (path === 'heartbeat') {
    out = heartbeat();
  } else if (path === 'relay') {
    if (body.clave && body.valor) relaySet(body.clave, body.valor);
    out = { ok: true };
  } else {
    out = { ok: false, error: 'path desconocido: ' + path };
  }
  return ContentService.createTextOutput(JSON.stringify(out))
                       .setMimeType(ContentService.MimeType.JSON);
}

function setupTodo() {
  ScriptApp.getProjectTriggers().forEach(function(t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('heartbeat').timeBased().everyMinutes(15).create();
  ScriptApp.newTrigger('bcrp').timeBased().everyHours(2).create();
  ScriptApp.newTrigger('purgeV151').timeBased().everyHours(6).create();
  heartbeat();
  bcrp();
  Logger.log('setupTodo OK — despliega ahora como Web app → Anyone → Deploy/Update');
}
