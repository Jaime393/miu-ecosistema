import json, pathlib, os, hashlib
ROOT = pathlib.Path(__file__).parents[2]
MAN = ROOT / "MANIFIESTO_VIVO.json"
GRACE = ROOT / "data/suelo/GRACE_TN14_REAL_TEMPLATE.csv"
CORPUS = ROOT / "data/corpus/corpus_unificado_v13.jsonl"
LEDGER = ROOT / "nodos/puente/ledger_micelio.jsonl"
PUENTE = ROOT / "nodos/puente/puente_micelio.jsonl"
WALLET = ROOT / "nodos/wallet_soberana/wallet_soberana.jsonl"
API = ROOT / "nodos/economia/api_micelio.py"
ROUTER = ROOT / "nodos/puente/router_libre.py"

def check(path):
    return path.exists() and path.stat().st_size>0

print(f"=== DIAGNOSTICO MASIVO ABSOLUTO GRACE 221R HEAD aa12689 ===")
print(f"rho_mean esperado -0.00048470001250505 DOI 10.1029/2019GL085488")

grietas=[]
riesgos=[]

# 1. BLOQUE FISICO
if not check(GRACE):
    grietas.append("GRACE_TN14 no existe")
else:
    import csv
    vals=[]
    with open(GRACE) as f:
        r=csv.DictReader(f)
        for row in r:
            vals.append(float(row["c20_value"]))
    mean=sum(vals)/len(vals)
    print(f"BLOQUE FISICO: {len(vals)}R mean {mean} suelo vivo OK")
    if abs(mean - (-0.00048470001250505))>1e-6:
        riesgos.append(f"GRACE mean desviado {mean}")

# 2. BLOQUE CONOCIMIENTO
if check(CORPUS):
    size=CORPUS.stat().st_size
    lines=sum(1 for _ in open(CORPUS))
    print(f"BLOQUE CONOCIMIENTO: corpus {size} bytes {lines}R")
    if size<100000:
        grietas.append("corpus <100KB - carencia")
else:
    grietas.append("corpus_unificado_v13 no existe")

# MANIFIESTO
if check(MAN):
    man=json.load(open(MAN))
    print(f"MANIFIESTO_VIVO: {man.get('bloques_globales')} bloques head {man.get('head')} wallet {man.get('bloque_economico',{}).get('wallet_soberana')}")
else:
    grietas.append("MANIFIESTO_VIVO.json no existe en root")

# 3. BLOQUE ECONOMICO
for p,name in [(WALLET,"wallet_soberana"),(LEDGER,"ledger"),(PUENTE,"puente"),(ROUTER,"router_libre"),(API,"api_micelio")]:
    if check(p):
        print(f"ECONOMIA: {name} OK {p.stat().st_size}B")
    else:
        grietas.append(f"{name} {p} falta")
        riesgos.append(f"3er bloque incompleto sin {name}")

# LEDGER integridad
if check(LEDGER):
    lines=list(open(LEDGER))
    miu_total=0
    for l in lines:
        try:
            j=json.loads(l)
            miu_total+=j.get("credito_miu",0)+j.get("amount",0)
        except: pass
    print(f"LEDGER: {len(lines)} tx total huella {miu_total} MIU")
    if miu_total<520:
        grietas.append("ledger <520 MIU - legado no absorbido completo")

# WALLET soberana secreta?
if WALLET.exists():
    content=open(WALLET).read()
    if "mnemonic" in content.lower() or "private" in content.lower():
        riesgos.append("RIESGO CRITICO: semilla privada en wallet_soberana.jsonl - debe ser solo huella publica")

# PUENTE redundancia
if check(PUENTE):
    print(f"PUENTE: {sum(1 for _ in open(PUENTE))} nodos puente_micelio.jsonl")

# GIT
os.system("cd /data/data/com.termux/files/home/miu-ecosistema && git status --porcelain | head -20")
os.system("cd /data/data/com.termux/files/home/miu-ecosistema && git log --oneline -8")

# Estructura nodos
for d in ["franbot","artemis","tablet","red","puente","economia","wallet_soberana"]:
    p=ROOT/f"nodos/{d}"
    if not p.exists():
        grietas.append(f"nodo {d} no existe")

# RIESGOS restantes
print("\n=== GRIETAS MAPEADAS ===")
for g in grietas:
    print(f"🕳️ GRIETA: {g}")

print("\n=== RIESGOS ===")
for r in riesgos:
    print(f"⚠️ RIESGO: {r}")

# TEJIDO propuesto
print("\n=== TEJIDO RECOMENDADO ===")
if grietas:
    print("1. Tejer nodos faltantes con MANIFIESTO_NODO.json autonomo")
if riesgos:
    print("2. Tejer seguridad: mover semillas a ~/.miu_wallet/ no git")
print("3. Tejer API: python3 nodos.economia.api_micelio.py")
print("4. Tejer dashboard: sdk/miu_sdk.py + miu status")
print("5. Tejer IPFS: re-pin QmViGcEZ y QmbRBT14")

print("\nDIAGNOSTICO FIN - flujo perfecto si redundantes 0 carencias []")
