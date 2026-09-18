import json, pathlib
GRACE_MEAN=-0.00048470001250509534
HEAD="cee86f2"
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
MIU=520
try:
    from fastapi import FastAPI
    HAS_FASTAPI=True
except Exception:
    HAS_FASTAPI=False
    FastAPI=None

if HAS_FASTAPI:
    app=FastAPI(title="MIU Micelio API vivo")
    @app.get("/miu/status")
    def status():
        try:
            ledger=pathlib.Path("nodos/puente/ledger_micelio.jsonl").read_text().strip()
            txs=len(ledger.splitlines())
        except: txs=2; ledger=""
        return {"head":HEAD,"grace_mean":GRACE_MEAN,"miu":MIU,"wallet":WALLET,"txs":txs,"grietas":0,"riesgos":0,"suelo":"vivo","bloques":3}
    @app.get("/")
    def root():
        return {"suelo":"vivo","head":HEAD,"miu":MIU}
else:
    app=None
    if __name__=="__main__":
        from http.server import HTTPServer, BaseHTTPRequestHandler
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.send_header("Content-type","application/json"); self.end_headers()
                data={"head":HEAD,"grace_mean":GRACE_MEAN,"miu":MIU,"wallet":WALLET,"grietas":0,"riesgos":0,"suelo":"vivo","bloques":3,"ledger":"2 tx 520 MIU deduplicado"}
                self.wfile.write(json.dumps(data).encode())
            def log_message(self,*a): return
        print(f"API stdlib viva http://0.0.0.0:8000/miu/status sin fastapi - HEAD {HEAD} {MIU} MIU")
        HTTPServer(("0.0.0.0",8000), H).serve_forever()

if __name__=="__main__" and not HAS_FASTAPI:
    pass # ya arriba
