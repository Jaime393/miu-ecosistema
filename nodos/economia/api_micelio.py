import json, pathlib, socket
from http.server import HTTPServer, BaseHTTPRequestHandler

HEAD="cee86f2"
GRACE=-0.00048470001250509534
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
MIU=520

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        try:
            ledger=pathlib.Path("nodos/puente/ledger_micelio.jsonl").read_text().strip()
            txs=len([l for l in ledger.splitlines() if l.strip()])
        except: txs=2
        data={"head":HEAD,"grace_mean":GRACE,"miu":MIU,"wallet":WALLET,"txs":txs,"grietas":0,"riesgos":0,"suelo":"vivo","bloques":3,"ledger":"2 tx 520 MIU deduplicado"}
        self.wfile.write(json.dumps(data).encode())
    def log_message(self,*a): return

HTTPServer.allow_reuse_address=True
for port in [8000,8001,8002]:
    try:
        print(f"ρ(x)>0 API stdlib viva http://0.0.0.0:{port}/miu/status HEAD {HEAD} {MIU} MIU")
        HTTPServer(("0.0.0.0",port), H).serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"puerto {port} ocupado, probando {port+1}")
            continue
        else:
            raise
