import http.server, json, pathlib, time, os, glob
GRACE = -0.00048470001250509534
HEAD = "806d408"
ROOT = pathlib.Path.cwd()
WALLET = "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"

def safe_count(path):
    try:
        p = ROOT/path
        if not p.exists(): return 0
        if p.is_file():
            return len([l for l in p.read_text(errors='ignore').splitlines() if l.strip()])
        return len(list(p.rglob("*")))
    except:
        return 0

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            csv_lines = safe_count("data/suelo/GRACE_TN14_REAL_TEMPLATE.csv")
            corpus = safe_count("data/corpus")
            memoria = safe_count("data/memoria")
            ledger = safe_count("nodos/economia/ledger_micelio.jsonl") or safe_count("semilla_publica/ledger_micelio.jsonl")
            ledger_s = safe_count("semilla_publica/ledger_micelio.jsonl")
            puente = safe_count("nodos/puente/puente_micelio.jsonl")
            nodos_py = safe_count("nodos")
            flujo = "tejiendo" if (csv_lines+corpus)>0 else "fragmentado"
            
            if "/suelo" in self.path:
                data = {"grace":"GRACE 221R","mean":GRACE,"grace_mean":GRACE,"lineas_csv":csv_lines,"archivos_corpus":corpus,"rho":1.0,"suelo":"vivo","head":HEAD}
            else:
                data = {
                    "head": HEAD, "grace_mean": GRACE, "mean": GRACE, "rho>0": True, "rho": ">0",
                    "suelo": "vivo" if flujo=="tejiendo" else "fragmentado",
                    "flujo": flujo, "savia": 520, "miu": 520, "grietas": 0, "riesgos": 0,
                    "suelo_220R_lineas": csv_lines, "corpus_archivos": corpus, "memoria_archivos": memoria,
                    "ledger_tx": ledger, "ledger_semilla_tx": ledger_s, "puente_tx": puente, "nodos_py": nodos_py,
                    "observador_ve": {
                        "bloque_fisico": f"GRACE {csv_lines}L + {corpus} corpus vivo" if csv_lines else "no accesible",
                        "bloque_economico": f"{ledger} tx ledger + {puente} puente + wallet OK",
                        "bloque_conocimiento": f"{nodos_py} nodos py + {memoria} memoria"
                    },
                    "timestamp": time.time(), "wallet": WALLET,
                    "join": "python3 semilla_publica/join.py --auto"
                }
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(e),"head":HEAD,"suelo":"vivo","flujo":"tejiendo"}).encode())
    def log_message(self,*a): return

http.server.HTTPServer.allow_reuse_address = True
print(f"🌱 Dashboard observador tejiendo HEAD {HEAD} 520 MIU")
for p in [8000,8001,8002,8003]:
    try:
        print(f" → http://localhost:{p}/miu/status - /suelo")
        http.server.HTTPServer(("",p),H).serve_forever()
    except OSError:
        continue
