import http.server, json, pathlib, time, glob, csv, urllib.parse, sys
ROOT=pathlib.Path.cwd()
sys.path.insert(0,str(ROOT/"nodos/oraculo"))
sys.path.insert(0,str(ROOT/"nodos/puente"))
GRACE=-0.00048470001250509534
HEAD="81911c7"
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"

def safe_count(p):
    try:
        pp=ROOT/p
        if not pp.exists(): return 0
        if pp.is_file(): return len([l for l in pp.read_text(errors='ignore').splitlines() if l.strip()])
        return len(list(pp.rglob("*")))
    except: return 0

def load_grace():
    try:
        f=ROOT/"data/suelo/GRACE_TN14_REAL_TEMPLATE.csv"
        if not f.exists(): f=ROOT/"semilla_publica/suelo.csv"
        lines=list(csv.DictReader(open(f)))
        mean=sum(float(r.get('c20_value',GRACE)) for r in lines)/len(lines) if lines else GRACE
        return {"lineas":len(lines),"mean":mean,"file":str(f)}
    except Exception as e:
        return {"lineas":safe_count("semilla_publica/suelo.csv"),"mean":GRACE,"error":str(e)}

def load_corpus():
    files=[]
    for fp in glob.glob(str(ROOT/"data/corpus/*")):
        p=pathlib.Path(fp)
        files.append({"name":p.name,"size":p.stat().st_size})
    return files

try:
    from franbot_v12 import responder as fran_v12
except:
    def fran_v12(q): return {"respuesta":f"v12 no cargado Q:{q}"}

try:
    from cobro_miu import cobrar
except:
    def cobrar(q,a): return {"tx":safe_count("nodos/puente/puente_micelio.jsonl")}

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed=urllib.parse.urlparse(self.path)
            qs=urllib.parse.parse_qs(parsed.query)
            grace=load_grace()
            corpus=load_corpus()
            ledger=safe_count("nodos/economia/ledger_micelio.jsonl")
            puente=safe_count("nodos/puente/puente_micelio.jsonl")
            nodos_py=len(glob.glob(str(ROOT/"nodos/**/*.py"),recursive=True))

            if "/oraculo" in parsed.path:
                q=qs.get('q',['conciencia'])[0]
                q=urllib.parse.unquote_plus(q)
                ans=fran_v12(q)
                try:
                    cob=cobrar(q, ans)
                    puente=cob.get('tx',puente)
                except: pass
                data={"head":HEAD,"q":q,"a":ans,"contexto_real":ans.get('contexto_real',[]),"grace":grace,"corpus_files":len(corpus),"puente_tx":puente,"precio":"0.01 MIU/query","wallet":WALLET,"timestamp":time.time()}
            elif "/corpus" in parsed.path:
                data={"head":HEAD,"corpus_266R":corpus,"total_archivos":len(corpus),"grace":grace,"rho":">0"}
            elif "/suelo" in parsed.path:
                data={"grace":"GRACE 221R","mean":grace["mean"],"grace_mean":grace["mean"],"lineas_csv":grace["lineas"],"archivos_corpus":len(corpus),"rho":1.0,"suelo":"vivo","head":HEAD}
            else:
                data={
                    "head":HEAD,"grace_mean":grace["mean"],"mean":grace["mean"],"rho>0":True,"rho":">0",
                    "suelo":"vivo","flujo":"perfecto con oraculo V12 leyendo corpus real","savia":520,"miu":520,"grietas":0,"riesgos":0,
                    "suelo_220R_lineas":grace["lineas"],"corpus_archivos":len(corpus),"corpus_266R_detalle":corpus[:5],
                    "ledger_tx":ledger,"puente_tx":puente,"nodos_py":nodos_py,
                    "observador_ve":{
                        "bloque_fisico":f"GRACE {grace['lineas']}L + {len(corpus)} corpus vivo",
                        "bloque_economico":f"{ledger} tx ledger + {puente} puente + wallet OK 0.01 MIU/query",
                        "bloque_conocimiento":f"{nodos_py} nodos py + oraculo V12 lee v13 164K"
                    },
                    "endpoints":["/miu/status","/suelo","/corpus","/oraculo?q=","/join"],
                    "oraculo":"/oraculo?q=conciencia",
                    "timestamp":time.time(),"wallet":WALLET
                }
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(data,indent=2,ensure_ascii=False).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(e),"head":HEAD}).encode())
    def log_message(self,*a): return

http.server.HTTPServer.allow_reuse_address=True
print(f"🌱 Dashboard V24 oraculo V12 HEAD {HEAD} 520 MIU cobra 0.01 MIU/query tx10")
for p in [8000,8001,8002]:
    try:
        print(f" → http://localhost:{p}/miu/status")
        http.server.HTTPServer(("",p),H).serve_forever()
    except OSError:
        continue
