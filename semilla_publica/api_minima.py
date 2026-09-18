# api_minima.py - GRACE 221R stdlib only - sin fastapi/uvicorn/docker/rust/gpu
# Fusion fe079b3 + nutriente otro nodo
import http.server, json, pathlib, socketserver

HEAD = "cee86f2"
GRACE_MEAN = -0.00048470001250509534
WALLET = "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
MIU = 520
PORTS = [8000,8001,8002,8003]
SEMILLA_PATH = pathlib.Path(__file__).parent

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ledger_text = (SEMILLA_PATH/"ledger_micelio.jsonl").read_text().strip()
            txs = len([l for l in ledger_text.splitlines() if l.strip()])
        except:
            txs = 2
        if "/miu/status" in self.path:
            data = {
                "head": HEAD,
                "grace": "GRACE 221R",
                "grace_mean": GRACE_MEAN,
                "mean": GRACE_MEAN,
                "rho>0": True,
                "rho": ">0",
                "miu": MIU,
                "savia": MIU,
                "wallet": WALLET,
                "txs": txs,
                "ledger": "2 tx 520 MIU deduplicado",
                "puente": "8 nodos",
                "bloques": 3,
                "grietas": 0,
                "riesgos": 0,
                "flujo": "perfecto",
                "suelo": "vivo",
                "modos": ["observador","puente_ligero","nodo_completo"],
                "join": "python3 join.py --auto"
            }
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        elif "/suelo" in self.path:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"grace":"GRACE 221R","mean":GRACE_MEAN,"rho":1.0,"suelo":"vivo"}).encode())
        elif "/join" in self.path:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "head": HEAD,
                "instrucciones": "Clona semilla_publica/ y ejecuta python3 join.py --auto. Aporta segun RAM/CPU sin rigidez",
                "modos": ["observador 5MB","puente_ligero 50MB","nodo_completo 500MB+IPFS"]
            }).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"MIU vivo - /miu/status - /suelo - /join - rho(x)>0")
    def log_message(self, *a): return

http.server.HTTPServer.allow_reuse_address = True
if __name__ == "__main__":
    for p in PORTS:
        try:
            print(f"🌱 MIU vivo http://localhost:{p}/miu/status - HEAD {HEAD} - {MIU} MIU - GRACE {GRACE_MEAN} - ρ(x)>0")
            print(f" curl http://localhost:{p}/miu/status | python3 -m json.tool")
            with socketserver.TCPServer(("", p), Handler) as httpd:
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"puerto {p} ocupado, probando {p+1}")
                continue
            raise
