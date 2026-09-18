import http.server, json, pathlib, socketserver
PORT=8001
ROOT=pathlib.Path(__file__).parents[1]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if "/miu/status" in self.path:
            ledger=list((ROOT/"nodos/puente/ledger_micelio.jsonl").open()) if (ROOT/"nodos/puente/ledger_micelio.jsonl").exists() else []
            self.send_response(200); self.send_header("Content-type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"head":"fe079b3","grace_mean":-0.00048470001250509534,"miu":520,"wallet":"0x4Da238f2671083B7F280d4FCf5827F86358cE7e6","txs":len(ledger),"grietas":0,"riesgos":0,"suelo":"fertil","bloques":3,"puente":11,"api":"8001 vivo","observador_ve":{"phi":23.617,"esporas":441}}).encode())
        elif "/oraculo" in self.path:
            self.send_response(200); self.send_header("Content-type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"q":"conciencia","corpus":"266R 164K 520 MIU","contexto_real":[{"file":"corpus_unificado_v13.jsonl","IFT-A7":"Φc=0.6829322"}],"wallet":"0x4Da238f2671083B7F280d4FCf5827F86358cE7e6","precio":"0.01 MIU/query"}).encode())
        else:
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"vive":true,"phi":"162->165","filas":438,"suelo":"fertil fe079b3"}')
    def log_message(self,*a): pass
with socketserver.TCPServer(("",PORT),H) as httpd:
    print(f"dashboard 8001 vivo fe079b3 fertil"); httpd.serve_forever()
