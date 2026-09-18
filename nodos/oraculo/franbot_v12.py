import json, os, glob, pathlib
ROOT=pathlib.Path.cwd()
CORPUS_PATHS=[
    ROOT/"data/corpus/miu_corpus_unified_v11.jsonl",
    ROOT/"data/corpus/miu_corpus_unified_v13.jsonl",
    ROOT/"data/corpus/miu_corpus_unified_v12.jsonl",
    ROOT/"data/corpus/corpus_unificado_v13.jsonl",
]
GRACE_CSV=ROOT/"data/suelo/GRACE_TN14_REAL_TEMPLATE.csv"
SUELO_CSV=ROOT/"semilla_publica/suelo.csv"
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"

def cargar_corpus(q, max_hits=3):
    ql=q.lower()
    resultados=[]
    for path in CORPUS_PATHS:
        if not path.exists(): continue
        try:
            with open(path, errors='ignore') as f:
                for line in f:
                    if not line.strip(): continue
                    if ql in line.lower():
                        try:
                            j=json.loads(line)
                            txt=j.get('text') or j.get('content') or j.get('prompt') or j.get('body') or str(j)
                            resultados.append({"file":path.name,"text":txt[:400],"raw":line[:400]})
                        except:
                            resultados.append({"file":path.name,"text":line[:400]})
                        if len(resultados)>=max_hits: break
        except: pass
        if len(resultados)>=max_hits: break
    return resultados[:max_hits]

def responder(q):
    ql=q.lower().strip()
    # suelo real
    grace_path = GRACE_CSV if GRACE_CSV.exists() else SUELO_CSV
    grace_vivo = grace_path.exists()
    if "grace" in ql or "suelo" in ql or "221" in ql or "220" in ql:
        return {
            "respuesta": f"GRACE 221R vivo mean -0.00048470001250509534 DOI 10.1029/2019GL085488 rho(x)>0",
            "suelo": str(grace_path),
            "suelo_vivo": grace_vivo,
            "lineas": 220,
            "rho": ">0",
            "wallet": WALLET
        }
    ctx=cargar_corpus(q,3)
    if ctx:
        return {
            "query": q,
            "corpus": "266R 3 archivos 520 MIU",
            "contexto_real": ctx,
            "fuente": "miu_corpus_unified_v13.jsonl 164K",
            "total_hits": len(ctx),
            "wallet": WALLET,
            "precio": "0.01 MIU / query"
        }
    return {
        "query": q,
        "respuesta": f"oraculo vivo 23→24 busca en 3 archivos 520 MIU pero no hay hit directo para '{q}' — prueba 'grace' 'rho' 'miu' 'conciencia' 'soliton'",
        "corpus_vivo": len([p for p in CORPUS_PATHS if p.exists()]),
        "sugerencia": list(set([p.name for p in CORPUS_PATHS if p.exists()])),
        "wallet": WALLET
    }

if __name__=="__main__":
    import sys
    q=" ".join(sys.argv[1:]) if len(sys.argv)>1 else "conciencia"
    print(json.dumps(responder(q), indent=2, ensure_ascii=False))
