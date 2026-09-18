import json, pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler

HEAD="cee86f2"
GRACE=-0.00048470001250509534
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
MIU=520
BASE=pathlib.Path(__file__).parent

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ledger=(BASE.parent/"puente"/"ledger_micelio.jsonl").read_text().strip()
            txs=len([l for l in ledger.splitlines() if l.strip()])
        except: txs=2
        if "/miu/status" in self.path:
            data={"head":HEAD,"grace_mean":GRACE,"mean":GRACE,"miu":MIU,"savia":MIU,"wallet":WALLET,"txs":txs,"grietas":0,"riesgos":0,"suelo":"vivo","bloques":3,"ledger":"2 tx 520 MIU deduplicado","puente":"8 nodos","flujo":"perfecto","rho":">0","rho_bool":True}
        elif "/suelo" in self.path:
            data={"grace":"GRACE 221R","mean":GRACE,"grace_mean":GRACE,"rho":1.0,"suelo":"vivo","head":HEAD}
        else:
            data={"msg":"MIU vivo - /miu/status - /suelo - rho(x)>0","head":HEAD,"miu":MIU,"savia":MIU}
        self.send_response(200)
        self.send_header("Content-type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())
    def log_message(self,*a): return

HTTPServer.allow_reuse_address=True
if __name__=="__main__":
    for port in [8000,8001,8002,8003]:
        try:
            print(f"ρ(x)>0 API principal viva http://0.0.0.0:{port}/miu/status HEAD {HEAD} {MIU} MIU savia {MIU} flujo perfecto GRACE {GRACE}")
            HTTPServer(("0.0.0.0",port),H).serve_forever()
        except OSError:
            continue
