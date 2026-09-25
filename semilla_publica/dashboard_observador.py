import http.server, json, pathlib, time, glob, csv, urllib.parse, sys
ROOT=pathlib.Path.cwd()
sys.path.insert(0,str(ROOT/"nodos/oraculo"))
sys.path.insert(0,str(ROOT/"nodos/puente"))
sys.path.insert(0,str(ROOT/"nodos/lenguaje"))
GRACE=-0.00048470001250509534
HEAD="804a1fb"
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"

def safe_count(p):
    try:
        pp=ROOT/p
        if not pp.exists(): return 0
        return len([l for l in pp.read_text(errors='ignore').splitlines() if l.strip()]) if pp.is_file() else len(list(pp.rglob("*")))
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
    return [{"name":pathlib.Path(fp).name,"size":pathlib.Path(fp).stat().st_size} for fp in glob.glob(str(ROOT/"data/corpus/*"))]

try:
    from franbot_v12 import responder as fran_v12
except Exception as e:
    def fran_v12(q): return {"error":str(e),"query":q}

try:
    from cobro_miu import cobrar
except:
    def cobrar(q,a): return {"tx":safe_count("nodos/puente/puente_micelio.jsonl")}

try:
    from fst_engine import fst_rho_base
    from grafo_lenguaje import GrafoLenguaje
    from tts_fst import TTS_FST
    from asr_fst import ASR_FST
    GRAFO=GrafoLenguaje()
    TTS=TTS_FST()
    ASR=ASR_FST()
    FST_OK=True
except Exception as e:
    FST_OK=False
    FST_ERR=str(e)

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
                try: cob=cobrar(q, ans); puente=cob.get('tx',puente)
                except: pass
                data={"head":HEAD,"q":q,"a":ans,"contexto_real":ans.get('contexto_real',[]),"grace":grace,"corpus_files":len(corpus),"puente_tx":puente,"precio":"0.01 MIU/query","wallet":WALLET,"fst_ok":FST_OK,"timestamp":time.time()}

            elif "/lenguaje" in parsed.path:
                q=qs.get('q',['rho'])[0]
                q=urllib.parse.unquote_plus(q)
                if FST_OK:
                    cons=GRAFO.consultar(q)
                    ora=GRAFO.oraculo_v12(q)
                    try: cob=cobrar(f"lenguaje:{q}", cons); puente=cob.get('tx',puente)
                    except: pass
                    data={"head":HEAD,"q":q,"consulta_fst":cons,"oraculo_v12_contexto":ora.get('contexto_real',[])[:1],"puente_tx":puente,"precio":"0.01 MIU/query","rho":">0"}
                else:
                    data={"error":FST_ERR,"head":HEAD}

            elif "/tts" in parsed.path:
                q=qs.get('q',['rho mayor que cero'])[0]
                q=urllib.parse.unquote_plus(q)
                if FST_OK:
                    fon=TTS.texto_a_fonemas(q)
                    # no habla en server, solo devuelve fonemas
                    try: cob=cobrar(f"tts:{q}", fon); puente=cob.get('tx',puente)
                    except: pass
                    data={"head":HEAD,"q":q,"fonemas":fon,"puente_tx":puente,"precio":"0.01 MIU/query","cmd":f"espeak -v es-la '{q}'"}
                else:
                    data={"error":FST_ERR}

            elif "/asr" in parsed.path:
                # usa audio de artemis si existe
                wav=ROOT/"artemis/tests/tools/inputs/audio_recording.mp3"
                wav2=ROOT/"artemis/tests/tools/inputs/recording.mp4"
                sample=str(wav) if wav.exists() else (str(wav2) if wav2.exists() else "no audio sample")
                if FST_OK:
                    # ejemplo normalización
                    texto=qs.get('q',['ro mayor que cero conciencia'])[0]
                    texto=urllib.parse.unquote_plus(texto)
                    norm=ASR.normalizar(texto)
                    try: cob=cobrar(f"asr:{texto}", norm); puente=cob.get('tx',puente)
                    except: pass
                    data={"head":HEAD,"asr_crudo":texto,"normalizado_fst":norm,"sample_audio":sample,"puente_tx":puente,"precio":"0.01 MIU/query","note":"usa termux-speech-to-text o whisper-cpp para wav real"}
                else:
                    data={"error":FST_ERR}

            elif "/corpus" in parsed.path:
                data={"head":HEAD,"corpus_266R":corpus,"total_archivos":len(corpus),"grace":grace,"rho":">0","fst_ok":FST_OK}
            elif "/suelo" in parsed.path:
                data={"grace":"GRACE 221R","mean":grace["mean"],"lineas_csv":grace["lineas"],"archivos_corpus":len(corpus),"rho":1.0,"suelo":"vivo","head":HEAD,"fst_ok":FST_OK}
            else:
                data={"head":HEAD,"grace_mean":grace["mean"],"suelo":"vivo","flujo":"perfecto con oraculo V12 + FST TTS/ASR","savia":520,"suelo_220R_lineas":grace["lineas"],"corpus_archivos":len(corpus),"ledger_tx":ledger,"puente_tx":puente,"nodos_py":nodos_py,"observador_ve":{"bloque_fisico":f"GRACE {grace['lineas']}L + {len(corpus)} corpus vivo","bloque_economico":f"{ledger} tx ledger + {puente} puente + wallet OK 0.01 MIU/query","bloque_conocimiento":f"{nodos_py} nodos py + oraculo V12 + FST grafo lenguaje TTS/ASR vivo"},"endpoints":["/miu/status","/suelo","/corpus","/oraculo?q=","/lenguaje?q=","/tts?q=","/asr?q="],"oraculo":"/oraculo?q=conciencia","fst_demo":"/lenguaje?q=rho","timestamp":time.time(),"wallet":WALLET}
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(data,indent=2,ensure_ascii=False).encode())
        except Exception as e:
            self.send_response(500); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e),"head":HEAD}).encode())
    def log_message(self,*a): return

print(f"🌱 Dashboard V25 HEAD {HEAD} 520 MIU + FST TTS/ASR 8001")
http.server.HTTPServer(("",8001),H).serve_forever()
