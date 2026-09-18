import os, pathlib, json, urllib.request, sys
ROOT=pathlib.Path.cwd()
def check(p):
    pp=ROOT/p
    return pp.exists(), pp.stat().st_size if pp.exists() and pp.is_file() else len(list(pp.rglob("*"))) if pp.exists() else 0

print("ρ(x)>0 — TEST OBSERVADOR TOTAL")
for path in ["data/suelo/GRACE_TN14_REAL_TEMPLATE.csv","data/corpus","nodos/economia/ledger_micelio.jsonl","semilla_publica/ledger_micelio.jsonl","nodos/economia/wallet_soberana.json","nodos/oraculo/franbot","semilla_publica/api_minima.py","semilla_publica/dashboard_observador.py"]:
    ex,size=check(path)
    print(f"{'✅' if ex else '❌'} {path} -> {size}")

print("\n--- API local 8000 ---")
try:
    import urllib.request, json
    data=json.loads(urllib.request.urlopen("http://localhost:8000/miu/status", timeout=2).read())
    print(f"✅ /miu/status vivo {data.get('suelo_220R_lineas')} lineas flujo {data.get('flujo')}")
    print(f"   observador_ve: {data.get('observador_ve')}")
except Exception as e:
    print(f"❌ /miu/status muerto: {e}")

print("\n--- GitHub raw accesible? ---")
for raw in ["https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/semilla_publica/semilla.json","https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/semilla_publica/ledger_micelio.jsonl","https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/nodos/puente/puente_micelio.jsonl"]:
    try:
        code=urllib.request.urlopen(raw, timeout=3).getcode()
        print(f"✅ {raw} -> {code}")
    except Exception as e:
        print(f"❌ {raw} -> INACCESIBLE {e} — el otro nodo no puede observar")
