import json, pathlib, time
ROOT=pathlib.Path.cwd()
TEMPLATE=ROOT/"semilla_publica/aporte_template.json"
PUENTE=ROOT/"nodos/puente/puente_micelio.jsonl"

def aportar():
    try:
        data=json.loads(TEMPLATE.read_text()) if TEMPLATE.exists() else {"aporte":"observador verifica suelo 221L"}
    except:
        data={"aporte":"observador verifica suelo 221L"}
    data["timestamp"]=time.time()
    data["head"]="22fece4"
    data["tx"]=len(PUENTE.read_text().splitlines())+1 if PUENTE.exists() else 9
    with open(PUENTE,"a") as f:
        f.write(json.dumps(data,ensure_ascii=False)+"\n")
    print(f"✅ aporte → puente {data['tx']} tx: {data}")
    return data

if __name__=="__main__":
    aportar()
