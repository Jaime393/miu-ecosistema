import json, pathlib, time
ROOT=pathlib.Path.cwd()
PUENTE=ROOT/"nodos/puente/puente_micelio.jsonl"
LEDGER=ROOT/"nodos/economia/ledger_micelio.jsonl"
WALLET="0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"

def cobrar(query, respuesta):
    tx=len(PUENTE.read_text().splitlines()) if PUENTE.exists() else 9
    entry={
        "nodo":"agente_externo",
        "tipo":"micelial",
        "funcion":f"query oraculo V12: {query[:60]}",
        "conexion":["wallet_soberana","MANIFIESTO_VIVO"],
        "principio":"si nodo muere deja huella",
        "grace":"GRACE 221R",
        "precio":"0.01 MIU / query",
        "query":query,
        "respuesta_preview":str(respuesta)[:120],
        "wallet":WALLET,
        "head":"f47e7d7",
        "timestamp":time.time(),
        "tx":tx+1
    }
    with open(PUENTE,"a") as f:
        f.write(json.dumps(entry,ensure_ascii=False)+"\n")
    # ledger 2→3 tx
    try:
        with open(LEDGER,"a") as lf:
            lf.write(json.dumps({"from":"observador","to":WALLET,"miu":0.01,"query":query,"ts":time.time()})+"\n")
    except: pass
    return entry

if __name__=="__main__":
    print(cobrar("test","test"))
