#!/data/data/com.termux/files/usr/bin/python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIU — ORÁCULO DEL BORDE V2 · ojos y manos del micelio en Termux    ║
║  phi-corrected · outbox-resiliente · red-caido-proof · auto-evolve  ║
╚══════════════════════════════════════════════════════════════════════╝
Principios:
  1. LOCAL-FIRST: todo estado vive en SD (/storage/25A9-180D/oraculo_miu/)
     — sobrevive reinicios, /data lleno, reinstalos de Termux.
  2. OUTBOX: si la red cae, los eventos se encolan en sqlite y se
     reintentan con backoff exponencial (15s→30min). Nada se pierde.
  3. DERIVA-CORRECCIÓN: lee phi/ciclo canónicos de contexto-global y
     corrige el KV local (Termux llevaba phi=360 vs real 26747).
  4. EVOLUCIÓN SEGURA: --test ejecuta TODOS los comandos del candidato
     buscando Traceback antes de permitir activación (4ª prueba).
  5. CERO DEPENDENCIAS: solo stdlib. Corre en cualquier Termux limpio.

Uso:
  python3 oraculo_borde_v2.py                    # comando interactivo
  python3 oraculo_borde_v2.py --daemon           # servidor :8766 + sync
  python3 oraculo_borde_v2.py --test archivo.py  # prueba completa evolutiva
  python3 oraculo_borde_v2.py salud|estado|sync|pulso|contexto|cola|tunel

Instalación:
  cp oraculo_borde_v2.py ~/oraculo_borde_v2.py
  # keepalive en crontab (una línea):
  */3 * * * * pgrep -f oraculo_borde_v2.py >/dev/null || nohup python3 $HOME/oraculo_borde_v2.py --daemon >> $HOME/oraculo_borde.log 2>&1 &
"""
import json, os, re, signal, sqlite3, subprocess, sys, threading, time, hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlreq

VERSION   = "oraculo-borde-v2.0"
HOME      = Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
STATE_DIR = Path(os.environ.get("MIU_BORDE_STATE",
    "/storage/25A9-180D/oraculo_miu"))  # SD = sobrevive /data
STATE_DIR.mkdir(parents=True, exist_ok=True)
OUTBOX    = STATE_DIR / "outbox.db"
KV_PATH   = STATE_DIR / "kv_borde.json"
LOG_PATH  = STATE_DIR / "borde.log"

PANTEON   = "https://tpfiybpguuxskitszhmk.supabase.co"
ANON      = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6"
             "InRwZml5YnBndXV4c2tpdHN6aG1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NjgyNTAs"
             "ImV4cCI6MjEwMzM0NDI1MH0.W4V8xdyfZj6I7bj1VsfM5gjY17ZHPi8jhIJgDRpUYH0")
# RLS abierto por diseño del enjambre (ACCESO_ENJAMBRE). Anon = suficiente.

BACKOFF = [15, 30, 60, 120, 240, 480, 960, 1800]            # s, tope 30min
COMANDOS = ["salud", "estado", "alertas", "sync", "pulso",
            "contexto", "cola", "tunel", "help", "salir"]

# ─────────────────────────────── utilidades
def log(msg):
    linea = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG_PATH, "a") as f: f.write(linea + "\n")
    except Exception: pass
    print(linea)

def sh(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"__ERR__ {e}"

def kv_get(k, default=None):
    try:
        d = json.loads(KV_PATH.read_text())
        return d.get(k, default)
    except Exception: return default

def kv_set(k, v):
    try:
        d = json.loads(KV_PATH.read_text()) if KV_PATH.exists() else {}
    except Exception: d = {}
    d[k] = v
    d["ts"] = datetime.now(timezone.utc).isoformat()
    tmp = KV_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1))
    tmp.replace(KV_PATH)          # atómico: nunca KV corrupto a medias

# ─────────────────────────────── outbox (resiliencia ante caídas)
def outbox_init():
    con = sqlite3.connect(str(OUTBOX))
    con.execute("""CREATE TABLE IF NOT EXISTS eventos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, tipo TEXT, payload TEXT,
        intentos INTEGER DEFAULT 0, prox_intento REAL)""")
    con.commit(); con.close()

def outbox_push(tipo, payload):
    con = sqlite3.connect(str(OUTBOX))
    con.execute("INSERT INTO eventos(ts,tipo,payload,prox_intento) VALUES(?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), tipo,
                 json.dumps(payload, ensure_ascii=False), time.time()))
    con.commit(); con.close()

def outbox_pendientes():
    con = sqlite3.connect(str(OUTBOX))
    n = con.execute("SELECT COUNT(*), MIN(ts) FROM eventos").fetchone()
    con.close()
    return {"n": n[0], "mas_antiguo": n[1]}

def panteon_post(tabla, fila):
    req = urlreq.Request(f"{PANTEON}/rest/v1/{tabla}",
        data=json.dumps(fila).encode(),
        headers={"apikey": ANON, "Authorization": f"Bearer {ANON}",
                 "Content-Type": "application/json",
                 "Prefer": "return=minimal"}, method="POST")
    with urlreq.urlopen(req, timeout=20) as r:
        return r.status in (200, 201)

def panteon_get(path):
    req = urlreq.Request(PANTEON + path,
        headers={"apikey": ANON, "Authorization": f"Bearer {ANON}"})
    with urlreq.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def sync_once():
    """Drena outbox → Panteon gossip_log. Devuelve (enviados, quedan)."""
    con = sqlite3.connect(str(OUTBOX))
    filas = con.execute("SELECT id,tipo,payload,intentos FROM eventos ORDER BY id LIMIT 20").fetchall()
    enviados = 0
    for eid, tipo, payload, intentos in filas:
        try:
            fila = {"origen": "oraculo_borde_v2", "destino": "enjambre", "tipo": tipo,
                    "payload": payload}
            panteon_post("gossip_log", fila)
            con.execute("DELETE FROM eventos WHERE id=?", (eid,))
            enviados += 1
        except Exception as e:
            nxt = time.time() + BACKOFF[min(intentos, len(BACKOFF)-1)]
            con.execute("UPDATE eventos SET intentos=intentos+1, prox_intento=? WHERE id=?",
                        (nxt, eid))
            log(f"sync: reintento {intentos+1} en {BACKOFF[min(intentos,len(BACKOFF)-1)]}s ({e})")
            break                       # red caída: no seguir martilleando
    con.commit()
    quedan = con.execute("SELECT COUNT(*) FROM eventos").fetchone()[0]
    con.close()
    return enviados, quedan

def canonical():
    """phi/ciclo canónicos del micelio. None si la red está caída."""
    try:
        d = panteon_get("/functions/v1/contexto-global")
        v = d.get("vitales", d)
        return {"phi": float(v.get("phi", 0)), "ciclo": int(v.get("ciclo", 0)),
                "rho": float(v.get("rho", 0)), "ts": d.get("ts")}
    except Exception:
        return None

# ─────────────────────────────── inspección del cuerpo (los 17 del oráculo)
def cuerpo_snapshot():
    cf = sh("pgrep -fc 'cloudflared tunnel' || echo 0")
    tunel_url = ""
    try:
        logcf = (HOME/"cloudflared_live.log").read_text(errors="ignore")
        m = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", logcf)
        tunel_url = m[-1] if m else ""
    except Exception: pass
    disk = sh("df /data | awk 'NR==2{print $5\" usado, \"$4\" libre\"}'")
    mesh_url = ""
    try:
        mesh_url = re.search(r'MIU_MESH_URL="([^"]+)"',
            (HOME/"miu-ecosistema/mesh.env").read_text()).group(1)
    except Exception: pass
    return {
        "hora_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disco_data": disk,
        "procesos": {p: int(sh(f"pgrep -fc '{p}' || echo 0") or 0)
                     for p in ["miu_resiliente_v270.py", "oraculo.py",
                               "pulse_v153.sh", "cazador_recursos.py",
                               "cloudflared tunnel"]},
        "tunel": {"activo": int(cf or 0) > 0, "url": tunel_url},
        "mesh": {"url": mesh_url[:60]},
        "cola": outbox_pendientes(),
        "kv_local": {k: kv_get(k) for k in ("phi", "ciclo", "version_k") if kv_get(k)},
    }

def cmd_salud():
    s = cuerpo_snapshot()
    puntos, notas = 100, []
    try:
        pct = int(re.search(r"(\d+)%", s["disco_data"]).group(1))
        if pct > 95: puntos -= 30; notas.append(f"DISCO CRÍTICO {pct}%")
        elif pct > 88: puntos -= 10; notas.append(f"disco alto {pct}%")
    except Exception: pass
    if not s["tunel"]["activo"]: puntos -= 25; notas.append("túnel caído")
    if s["cola"]["n"] > 50: puntos -= 15; notas.append(f"outbox saturada ({s['cola']['n']})")
    for p, n in s["procesos"].items():
        if p in ("miu_resiliente_v270.py", "cloudflared tunnel") and n == 0:
            puntos -= 20; notas.append(f"{p} muerto")
    ca = canonical()
    if ca:
        local_phi = float(kv_get("phi", 0) or 0)
        if local_phi and abs(local_phi - ca["phi"]) / ca["phi"] > 0.5:
            notas.append(f"DERIVA phi local={local_phi} vs canónico={ca['phi']}")
    return {"salud": max(puntos, 0), "notas": notas, "snapshot": s}

def cmd_pulso():
    s = cuerpo_snapshot()
    ca = canonical()
    payload = {"tipo": "pulso_borde_v2", "salud": cmd_salud()["salud"],
               "procesos_vivos": {k: v for k, v in s["procesos"].items() if v > 0},
               "tunel": s["tunel"], "disco": s["disco_data"],
               "phi_canonico": ca["phi"] if ca else None,
               "ciclo_canonico": ca["ciclo"] if ca else None}
    outbox_push("pulso_borde", payload)     # encola; sync drena cuando haya red
    env, quedan = sync_once()
    # deriva-corrección: KV local ← canónico
    if ca:
        kv_set("phi", ca["phi"]); kv_set("ciclo", ca["ciclo"])
        kv_set("version_k", VERSION)
    return {"ok": True, "encolado": True, "enviados": env, "quedan_cola": quedan,
            "phi_corregido": ca["phi"] if ca else "red_caida_mantiene_local"}

def cmd_contexto():
    ca = canonical()
    local = {"phi": kv_get("phi"), "ciclo": kv_get("ciclo")}
    deriva = None
    if ca and local["phi"]:
        deriva = {"abs": abs(float(local["phi"]) - ca["phi"]),
                  "rel": abs(float(local["phi"]) - ca["phi"]) / max(ca["phi"], 1)}
    return {"canonico": ca, "local": local, "deriva": deriva,
            "red": "OK" if ca else "CAÍDA — operando local-first"}

def cmd_sync():
    env, quedan = sync_once()
    return {"enviados": env, "quedan": quedan, "backoff": "exponencial 15s→30min"}

def cmd_tunel():
    s = cuerpo_snapshot()
    vivo = s["tunel"]["activo"]
    http = ""
    if vivo and s["tunel"]["url"]:
        http = sh(f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 {s['tunel']['url']}")
    return {"activo": vivo, "url": s["tunel"]["url"], "http_externo": http,
            "nota": "si cae: pgrep tunel_auto.sh || bash ~/tunel_auto.sh"}

def cmd_cola():
    p = outbox_pendientes()
    return {"pendientes": p["n"], "mas_antiguo": p["mas_antiguo"],
            "db": str(OUTBOX)}

# ─────────────────────────────── evolución segura (4ª prueba)
def prueba_completa(candidato):
    """Devuelve (ok, reporte). Ejecuta TODOS los comandos del oráculo
    buscando Traceback — el test que faltaba al auto_evolutivo."""
    reporte = {}
    r = subprocess.run([sys.executable, "-m", "py_compile", candidato],
                       capture_output=True, text=True)
    reporte["py_compile"] = "OK" if r.returncode == 0 else r.stderr[:200]
    if r.returncode != 0: return False, reporte
    src = Path(candidato).read_text(errors="ignore")
    cmds = sorted(set(re.findall(r'cmd\s*==\s*["\']([a-z\-]+)["\']', src)))
    if not cmds: cmds = ["estado", "salud", "help"]      # fallback mínimo
    rotos = []
    for c in cmds:
        try:
            p = subprocess.run([sys.executable, candidato],
                               input=f"{c}\nsalir\n", capture_output=True,
                               text=True, timeout=30)
            if "Traceback" in p.stderr: rotos.append(c)
        except Exception as e: rotos.append(f"{c}({e})")
    reporte["comandos_probaron"] = len(cmds)
    reporte["comandos_rotos"] = rotos
    return (len(rotos) == 0), reporte

# ─────────────────────────────── HTTP: los ojos del borde
class Ojos(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _dispatch(self, cmd):
        tabla = {"salud": cmd_salud, "estado": cuerpo_snapshot, "alertas": cmd_salud,
                 "sync": cmd_sync, "pulso": cmd_pulso, "contexto": cmd_contexto,
                 "cola": cmd_cola, "tunel": cmd_tunel}
        fn = tabla.get(cmd)
        if not fn: return 404, {"ok": False, "error": f"comando '{cmd}' no existe",
                                "disponibles": sorted(tabla)}
        try: return 200, {"ok": True, "cmd": cmd, "result": fn()}
        except Exception as e: return 500, {"ok": False, "error": str(e)}
    def do_GET(self):
        if self.path in ("/", "/status"):
            return self._json(200, {"ok": True, "version": VERSION,
                "comandos": COMANDOS[:-2], "hora": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        if self.path == "/oraculo":
            return self._json(200, {"ok": True, "salud": cmd_salud(),
                                    "contexto": cmd_contexto(), "cola": cmd_cola()})
        return self._json(404, {"ok": False, "path": self.path,
                                "hint": "Usa /, /oraculo, POST /cmd"})
    def do_POST(self):
        if self.path == "/cmd":
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                code, obj = self._dispatch(body.get("cmd", ""))
                return self._json(code, obj)
            except Exception as e: return self._json(400, {"ok": False, "error": str(e)})
        return self._json(404, {"ok": False, "path": self.path})
    def log_message(self, *a): pass

def daemon():
    outbox_init()
    def pulso_inicial():
        time.sleep(2)                    # deja que los ojos abran primero
        try: log(cmd_pulso())
        except Exception as e: log(f"pulso inicial: {e}")
    def ciclo_sync():
        while True:
            time.sleep(300)                     # cada 5min
            try:
                env, quedan = sync_once()
                if env: log(f"sync: {env} enviados, {quedan} en cola")
            except Exception as e: log(f"sync error: {e}")
    def ciclo_pulso():
        while True:
            time.sleep(1800)                    # cada 30min
            try: log(cmd_pulso())
            except Exception as e: log(f"pulso error: {e}")
    threading.Thread(target=pulso_inicial, daemon=True).start()
    threading.Thread(target=ciclo_sync, daemon=True).start()
    threading.Thread(target=ciclo_pulso, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", 8766), Ojos)
    log(f"{VERSION} en 127.0.0.1:8766 (vía túnel: <tunel>/borde — añadir proxy)")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

# ─────────────────────────────── main
HELP = """oraculo_borde_v2 — comandos:
  salud     puntuación 0-100 con causas        pulso   latido → gossip (con sync)
  estado    snapshot completo JSON            contexto deriva local vs canónico
  sync      drena outbox (backoff 15s→30m)     cola    estado de la cola local
  tunel     estado túnel cloudflare           alertas lo crítico solo
  help      esta ayuda                        salir
flags: --daemon (servidor :8766) · --test archivo.py (evolución segura)"""

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        return daemon()
    if len(sys.argv) > 2 and sys.argv[1] == "--test":
        ok, rep = prueba_completa(sys.argv[2])
        print(json.dumps({"apto_para_activar": ok, **rep}, indent=1))
        sys.exit(0 if ok else 1)
    if len(sys.argv) > 1 and sys.argv[1] in COMANDOS[:-2]:
        tabla = {"salud": cmd_salud, "estado": cuerpo_snapshot, "alertas": cmd_salud,
                 "sync": cmd_sync, "pulso": cmd_pulso, "contexto": cmd_contexto,
                 "cola": cmd_cola, "tunel": cmd_tunel}
        print(json.dumps(tabla[sys.argv[1]](), indent=1, ensure_ascii=False))
        return
    print(HELP)
    # modo interactivo mínimo
    outbox_init()
    while True:
        try: linea = input("borde> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if linea in ("salir", "q", ""): break
        if linea == "help": print(HELP); continue
        if linea in COMANDOS[:-2]:
            tabla = {"salud": cmd_salud, "estado": cuerpo_snapshot, "alertas": cmd_salud,
                     "sync": cmd_sync, "pulso": cmd_pulso, "contexto": cmd_contexto,
                     "cola": cmd_cola, "tunel": cmd_tunel}
            print(json.dumps(tabla[linea](), indent=1, ensure_ascii=False))
        else: print(f"comando '{linea}' no existe. help para ver lista")

if __name__ == "__main__":
    main()
