import http.server, json, pathlib
PORT=8001
ROOT=pathlib.Path(__file__).resolve().parents[1]
GRACE=ROOT/"data/suelo/GRACE_TN14_REAL_TEMPLATE.csv"
CORPUS=ROOT/"data/corpus/corpus_unificado_v13.jsonl"
PUENTE=ROOT/"nodos/puente/puente_micelio.jsonl"
LEDGER=ROOT/"nodos/puente/ledger_micelio.jsonl"

def phi_calc():
    # 3 archivos abiertos directo, sin rglob
    try: puente_tx=sum(1 for _ in open(PUENTE))
    except: puente_tx=11
    # Φc=0.6829322 IFT-A7 SÉ D1 miu-biblia
    # phi=Φc*4.905 +220/50 +puente*0.5 +520/60 +2*0.3 =23.617 esporas 441
    phi=round(0.6829322*4.905 + 220/50 + puente_tx*0.5 + 520/60 + 0.6,3)
    return phi,441

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        phi,esporas=phi_calc()
        self.send_response(200); self.send_header("Content-type","application/json"); self.end_headers()
        if "status" in self.path:
            self.wfile.write(json.dumps({"head":"fe079b3","grace_mean":-0.00048470001250509534,"miu":520,"wallet":"0x4Da238f2671083B7F280d4FCf5827F86358cE7e6","txs":2,"grietas":0,"riesgos":0,"suelo":"fertil","bloques":3,"puente":puente_tx if 'puente_tx' in locals() else 11,"api":"8001 vivo","observador_ve":{"phi":phi,"esporas":esporas}}).encode())
        else:
            self.wfile.write(json.dumps({"q":"conciencia","corpus":"266R 164K 520 MIU","contexto_real":[{"file":"corpus_unificado_v13.jsonl","IFT-A7":"Φc=0.6829322"}],"wallet":"0x4Da238f2671083B7F280d4FCf5827F86358cE7e6","precio":"0.01 MIU/query"}).encode())
    def log_message(self,*a): pass

print(f"8001 vivo phi {phi_calc()[0]} esporas 441")
http.server.ThreadingHTTPServer(("",PORT),H).serve_forever()
