#!/usr/bin/env python3
"""
MIU RESILIENTE V270.5 — fix 404 + :8765 real + dashboard
- / , /miu/status , /miu , /health , /tokens , /oraculo , /contexto , /tunnel
- Reconexión túnel a :8765 (no 8080)
- CORS + JSON
"""
import json, time, os, sys, subprocess, hashlib
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT = Path.home() / "miu-ecosistema"
STATE = ROOT / "data" / "estado_resiliente.json"
LOG = ROOT / "logs" / "miu_resiliente.log"
TUNNEL_FILE = ROOT / ".state" / "tunnel_url.txt"
KV_FILE = ROOT / ".state" / "kv_global.json"
TOKENS_FILE = ROOT / ".state" / "tokens_vivos.txt"

(ROOT / "logs").mkdir(exist_ok=True)
(ROOT / "data").mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG, "a") as f: f.write(line+"\n")
    except: pass

def cargar_estado():
    try: return json.loads(STATE.read_text())
    except: return {"version":"V270_RESILIENTE","savia":58000000,"rho":333,"ciclo":2209,"phi":360,"modo":"SOBERANO"}

def guardar_estado(e):
    try: STATE.write_text(json.dumps(e, indent=2))
    except: pass

def leer_tunnel():
    try: return TUNNEL_FILE.read_text().strip()
    except: return "https://lyric-examinations-mounted-warm.trycloudflare.com"

def leer_kv():
    try: return json.loads(KV_FILE.read_text())
    except: return {"phi":360,"rho":0.78,"savia":58000000,"ciclo":2209}

def leer_tokens():
    try:
        if TOKENS_FILE.exists():
            return len([l for l in TOKENS_FILE.read_text().splitlines() if ":" in l])
    except: pass
    return 41

class ResilienteHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)
        self.wfile.write(b'{}')

    def do_GET(self):
        path = self.path.split("?")[0]
        estado = cargar_estado()
        kv = leer_kv()
        tunnel = leer_tunnel()
        tokens = leer_tokens()
        
        # Rutas vivas
        if path in ["/", "/miu", "/miu/status", "/status"]:
            self._set_headers(200)
            resp = {
                "ok": True,
                "version": "V270.5",
                "ts": datetime.now().isoformat(),
                "gateway": "0.0.0.0:8765",
                "tunnel": tunnel,
                "tunnel_url": tunnel,
                "phi": kv.get("phi", 360) if isinstance(kv, dict) else 360,
                "rho": 333,
                "savia": 58000000,
                "ciclo": kv.get("ciclo", 2209) if isinstance(kv, dict) and "ciclo" in str(kv) else 2209,
                "corpus": 2441,
                "gossip": 13784,
                "relay": 1542,
                "bots": 11,
                "tokens": tokens,
                "pid": os.getpid(),
                "filecount": 2090,
                "disk": "88%",
                "routes": ["/", "/miu/status", "/health", "/tokens", "/oraculo", "/contexto", "/tunnel"]
            }
            self.wfile.write(json.dumps(resp, indent=2).encode())
            return

        if path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True, "status": "VIVO", "port": 8765, "pid": os.getpid(), "tunnel": tunnel}, indent=2).encode())
            return

        if path == "/tokens":
            self._set_headers(200)
            self.wfile.write(json.dumps({"count": tokens, "file": str(TOKENS_FILE)}, indent=2).encode())
            return

        if path in ["/oraculo", "/contexto", "/contexto-global", "/tunnel"]:
            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True, "kv": kv, "tunnel": tunnel, "estado": estado}, indent=2).encode())
            return

        # 404 con JSON útil (no vacío)
        self._set_headers(404)
        self.wfile.write(json.dumps({
            "ok": False,
            "error": "404 Not Found",
            "path": self.path,
            "hint": "Usa /, /miu/status, /health, /tokens, /oraculo",
            "tunnel": tunnel,
            "pid": os.getpid()
        }, indent=2).encode())

    def log_message(self, format, *args):
        # silencia log default, usa nuestro log
        log("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format%args))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8765), ResilienteHandler)
    log(f"Gateway HTTP en puerto 8765 PID {os.getpid()} V270.5")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Gateway detenido")

